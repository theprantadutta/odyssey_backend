"""Authentication schemas"""
from pydantic import BaseModel, UUID4, EmailStr
from typing import Optional, List
from datetime import datetime


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str
    user_id: str


class TokenData(BaseModel):
    """Token payload data"""
    user_id: UUID4


class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response"""
    id: UUID4
    email: str
    is_active: bool
    auth_provider: str = "email"
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    email_verified: bool = False

    class Config:
        from_attributes = True


# Google/Firebase Authentication Schemas
class FirebaseAuthRequest(BaseModel):
    """Firebase/Google authentication request"""
    firebase_token: str


class GoogleLinkRequest(BaseModel):
    """Request to link Google account to existing email account"""
    firebase_token: str
    password: str


class AuthProviderInfo(BaseModel):
    """Authentication provider information"""
    provider: str  # 'email', 'google'
    linked: bool
    email: Optional[str] = None


class AuthProvidersResponse(BaseModel):
    """Response listing user's authentication providers"""
    providers: List[AuthProviderInfo]
