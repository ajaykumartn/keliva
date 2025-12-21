"""
Authentication Router
Handles user registration, login, and authentication
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import os

from models.user import UserManager, User

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

# Initialize user manager
user_manager = UserManager(os.getenv("DB_PATH", "keliva.db"))

class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    created_at: str
    last_login: Optional[str]
    profile_picture: Optional[str]
    preferred_languages: list
    learning_goals: list
    family_group_id: Optional[str]

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    user_id = user_manager.verify_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user = user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("/register")
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    user = user_manager.create_user(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password=user_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    token = user_manager.generate_token(user.id)
    
    return {
        "message": "User registered successfully",
        "user": UserResponse(**user.to_dict()),
        "token": token
    }

@router.post("/login")
async def login_user(login_data: UserLogin):
    """Login user"""
    user = user_manager.authenticate_user_by_email(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token = user_manager.generate_token(user.id)
    
    return {
        "message": "Login successful",
        "user": UserResponse(**user.to_dict()),
        "token": token
    }

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**current_user.to_dict())

@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard token)"""
    return {"message": "Logout successful"}