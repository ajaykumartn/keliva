"""
User management API endpoints
Example of how to use DatabaseManager in FastAPI routes
"""
from fastapi import APIRouter, HTTPException, Request
from typing import List

from models.database import User, UserCreate
from utils.db_manager import DatabaseManager

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/", response_model=User)
async def create_user(user: UserCreate):
    """
    Create a new user
    
    Example request:
    ```json
    {
        "name": "John Doe",
        "telegram_id": 123456789,
        "preferred_language": "en"
    }
    ```
    """
    db = DatabaseManager()
    
    # Check if user with this telegram_id already exists
    if user.telegram_id:
        existing_user = db.get_user_by_telegram_id(user.telegram_id)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail=f"User with Telegram ID {user.telegram_id} already exists"
            )
    
    new_user = db.create_user(user)
    return new_user


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID"""
    db = DatabaseManager()
    user = db.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/telegram/{telegram_id}", response_model=User)
async def get_user_by_telegram(telegram_id: int):
    """Get user by Telegram ID"""
    db = DatabaseManager()
    user = db.get_user_by_telegram_id(telegram_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/", response_model=List[User])
async def list_users():
    """List all users"""
    db = DatabaseManager()
    users = db.list_users()
    return users


@router.put("/{user_id}/active")
async def update_last_active(user_id: str):
    """Update user's last active timestamp"""
    db = DatabaseManager()
    
    # Verify user exists
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.update_user_last_active(user_id)
    return {"message": "Last active timestamp updated"}
