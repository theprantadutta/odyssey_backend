"""Firebase Authentication Service for Google Sign-In"""
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Firebase Admin SDK imports
_firebase_initialized = False


def _ensure_firebase_initialized():
    """Initialize Firebase Admin SDK if not already done"""
    global _firebase_initialized

    if _firebase_initialized:
        return

    try:
        import firebase_admin
        from firebase_admin import credentials
        from app.config import settings

        # Check if already initialized
        try:
            firebase_admin.get_app()
            _firebase_initialized = True
            return
        except ValueError:
            pass  # Not initialized yet

        # Check for credentials file
        creds_path = settings.FCM_CREDENTIALS_PATH
        if not os.path.exists(creds_path):
            logger.warning(f"Firebase credentials file not found at {creds_path}")
            raise RuntimeError(f"Firebase credentials file not found at {creds_path}")

        # Initialize Firebase
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred, {
            'projectId': settings.FIREBASE_PROJECT_ID
        })
        _firebase_initialized = True
        logger.info("Firebase Admin SDK initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def verify_firebase_token(id_token: str) -> Dict:
    """
    Verify a Firebase ID token and return the decoded token.

    Args:
        id_token: The Firebase ID token from the client

    Returns:
        Decoded token dictionary containing user info

    Raises:
        ValueError: If token is invalid or expired
    """
    _ensure_firebase_initialized()

    from firebase_admin import auth
    from firebase_admin.auth import InvalidIdTokenError, ExpiredIdTokenError

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token

    except InvalidIdTokenError as e:
        logger.warning(f"Invalid Firebase token: {e}")
        raise ValueError("Invalid authentication token")

    except ExpiredIdTokenError as e:
        logger.warning(f"Expired Firebase token: {e}")
        raise ValueError("Authentication token has expired")

    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        raise ValueError(f"Token verification failed: {str(e)}")


def get_user_info_from_token(decoded_token: Dict) -> Dict:
    """
    Extract user information from a decoded Firebase token.

    Args:
        decoded_token: The decoded Firebase ID token

    Returns:
        Dictionary containing user info:
        - firebase_uid: Firebase user ID
        - email: User's email
        - email_verified: Whether email is verified
        - display_name: User's display name
        - photo_url: User's profile photo URL
        - auth_provider: Authentication provider ('google' or 'firebase')
        - google_id: Google user ID (if signed in with Google)
    """
    # Get sign-in provider
    sign_in_provider = decoded_token.get('firebase', {}).get('sign_in_provider', '')
    is_google = sign_in_provider == 'google.com'

    return {
        'firebase_uid': decoded_token.get('uid'),
        'email': decoded_token.get('email'),
        'email_verified': decoded_token.get('email_verified', False),
        'display_name': decoded_token.get('name'),
        'photo_url': decoded_token.get('picture'),
        'auth_provider': 'google' if is_google else 'firebase',
        'google_id': decoded_token.get('sub') if is_google else None,
    }


def get_firebase_user_by_uid(firebase_uid: str) -> Optional[Dict]:
    """
    Get Firebase user record by UID.

    Args:
        firebase_uid: The Firebase user ID

    Returns:
        Firebase user record or None if not found
    """
    _ensure_firebase_initialized()

    from firebase_admin import auth

    try:
        user = auth.get_user(firebase_uid)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'photo_url': user.photo_url,
            'email_verified': user.email_verified,
        }
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        logger.error(f"Error getting Firebase user: {e}")
        return None


def get_firebase_user_by_email(email: str) -> Optional[Dict]:
    """
    Get Firebase user record by email.

    Args:
        email: The user's email address

    Returns:
        Firebase user record or None if not found
    """
    _ensure_firebase_initialized()

    from firebase_admin import auth

    try:
        user = auth.get_user_by_email(email)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'photo_url': user.photo_url,
            'email_verified': user.email_verified,
        }
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        logger.error(f"Error getting Firebase user by email: {e}")
        return None
