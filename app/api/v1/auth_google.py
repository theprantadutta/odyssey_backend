"""Google/Firebase Authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.schemas.auth import (
    Token,
    FirebaseAuthRequest,
    GoogleLinkRequest,
    AuthProvidersResponse,
    AuthProviderInfo,
)
from app.services.auth_service import AuthService
from app.services.firebase_auth_service import (
    verify_firebase_token,
    get_user_info_from_token,
)
from app.core.dependencies import get_current_user
from app.core.security import verify_password
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/firebase", response_model=Token)
async def authenticate_with_firebase(
    request: FirebaseAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Firebase ID token (from Google Sign-In)

    This endpoint:
    1. Verifies the Firebase ID token
    2. Creates a new user if they don't exist
    3. Returns a JWT access token

    If a user with the same email exists but was registered with email/password,
    returns 409 CONFLICT requiring account linking.
    """
    auth_service = AuthService(db)

    # Verify Firebase token
    try:
        decoded_token = verify_firebase_token(request.firebase_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    # Extract user info from token
    user_info = get_user_info_from_token(decoded_token)
    firebase_uid = user_info['firebase_uid']
    email = user_info['email']

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required for authentication"
        )

    # Check if user exists by Firebase UID
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if user:
        # Existing Firebase user - update last login
        user.last_login = datetime.utcnow()
        db.commit()
        logger.info(f"Existing Firebase user logged in: {email}")
    else:
        # Check if email exists (email/password account)
        existing_user = auth_service.get_user_by_email(email)

        if existing_user:
            # Email exists but no Firebase UID - needs account linking
            if existing_user.firebase_uid is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists. Please link your Google account.",
                    headers={"X-Account-Linking-Required": "true"}
                )
            else:
                # Different Firebase UID for same email (shouldn't happen normally)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Account conflict. Please contact support."
                )

        # Create new user
        user = User(
            email=email,
            firebase_uid=firebase_uid,
            auth_provider=user_info['auth_provider'],
            google_id=user_info['google_id'],
            display_name=user_info['display_name'],
            photo_url=user_info['photo_url'],
            email_verified=user_info['email_verified'],
            password_hash=None,  # No password for Google-only users
            is_active=True,
            last_login=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New Google user created: {email}")

    # Create access token
    access_token = auth_service.create_access_token_for_user(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }


@router.post("/google", response_model=Token)
async def authenticate_with_google(
    request: FirebaseAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Alias for /firebase endpoint for Google Sign-In

    This is a convenience endpoint that works the same as /firebase
    """
    return await authenticate_with_firebase(request, db)


@router.post("/link-google", response_model=Token)
async def link_google_account(
    request: GoogleLinkRequest,
    db: Session = Depends(get_db)
):
    """
    Link Google account to existing email/password account

    Requires:
    - Firebase token from Google Sign-In
    - Password of existing email/password account
    """
    auth_service = AuthService(db)

    # Verify Firebase token
    try:
        decoded_token = verify_firebase_token(request.firebase_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    # Extract user info
    user_info = get_user_info_from_token(decoded_token)
    firebase_uid = user_info['firebase_uid']
    email = user_info['email']
    google_id = user_info['google_id']

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required for account linking"
        )

    # Find existing user by email
    user = auth_service.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email"
        )

    # Verify password
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account was created with Google. Password verification not needed."
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Check if Firebase UID or Google ID is already linked to another account
    if firebase_uid:
        existing = db.query(User).filter(
            User.firebase_uid == firebase_uid,
            User.id != user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Google account is already linked to another user"
            )

    if google_id:
        existing = db.query(User).filter(
            User.google_id == google_id,
            User.id != user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Google account is already linked to another user"
            )

    # Link accounts
    user.firebase_uid = firebase_uid
    user.google_id = google_id
    user.auth_provider = 'google'  # Update to indicate Google is now primary
    user.display_name = user_info['display_name'] or user.display_name
    user.photo_url = user_info['photo_url'] or user.photo_url
    user.email_verified = user_info['email_verified']
    user.last_login = datetime.utcnow()

    db.commit()
    logger.info(f"Google account linked to user: {email}")

    # Create access token
    access_token = auth_service.create_access_token_for_user(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }


@router.post("/auto-link-google", response_model=Token)
async def auto_link_google_account(
    request: FirebaseAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Automatically link Google account to existing email/password account

    This endpoint trusts Google's email verification to prove ownership,
    so no password is required. Used when user clicks "Yes" to link accounts.
    """
    auth_service = AuthService(db)

    # Verify Firebase token
    try:
        decoded_token = verify_firebase_token(request.firebase_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    # Extract user info
    user_info = get_user_info_from_token(decoded_token)
    firebase_uid = user_info['firebase_uid']
    email = user_info['email']
    google_id = user_info['google_id']

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required for account linking"
        )

    # Verify email is verified by Google
    if not user_info.get('email_verified', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email must be verified by Google to auto-link accounts"
        )

    # Find existing user by email
    user = auth_service.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email"
        )

    # Check if Firebase UID or Google ID is already linked to another account
    if firebase_uid:
        existing = db.query(User).filter(
            User.firebase_uid == firebase_uid,
            User.id != user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Google account is already linked to another user"
            )

    if google_id:
        existing = db.query(User).filter(
            User.google_id == google_id,
            User.id != user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This Google account is already linked to another user"
            )

    # Link accounts (no password verification needed - Google verified the email)
    user.firebase_uid = firebase_uid
    user.google_id = google_id
    user.auth_provider = 'google'
    user.display_name = user_info['display_name'] or user.display_name
    user.photo_url = user_info['photo_url'] or user.photo_url
    user.email_verified = True  # Google verified it
    user.last_login = datetime.utcnow()

    db.commit()
    logger.info(f"Google account auto-linked to user: {email}")

    # Create access token
    access_token = auth_service.create_access_token_for_user(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }


@router.post("/unlink-google")
async def unlink_google_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unlink Google account from user

    User must have a password set to unlink Google
    (otherwise they would be locked out)
    """
    if not current_user.firebase_uid and not current_user.google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Google account linked"
        )

    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlink Google account without a password. Please set a password first."
        )

    # Unlink Google
    current_user.firebase_uid = None
    current_user.google_id = None
    current_user.auth_provider = 'email'

    db.commit()
    logger.info(f"Google account unlinked from user: {current_user.email}")

    return {"message": "Google account unlinked successfully"}


@router.get("/providers", response_model=AuthProvidersResponse)
async def get_auth_providers(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of authentication providers linked to user account
    """
    providers = []

    # Email/password provider
    providers.append(AuthProviderInfo(
        provider="email",
        linked=current_user.password_hash is not None,
        email=current_user.email if current_user.password_hash else None
    ))

    # Google provider
    providers.append(AuthProviderInfo(
        provider="google",
        linked=current_user.google_id is not None or current_user.firebase_uid is not None,
        email=current_user.email if current_user.google_id else None
    ))

    return AuthProvidersResponse(providers=providers)
