"""Authentication schemas"""
from pydantic import BaseModel, UUID4, EmailStr


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

    class Config:
        from_attributes = True
