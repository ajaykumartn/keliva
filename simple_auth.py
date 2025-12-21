"""
Simple authentication endpoints for testing
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import hashlib
import uuid
import sqlite3
import os

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str

def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

@router.post("/login")
async def login_user(login_data: UserLogin):
    """Simple login endpoint"""
    try:
        db_path = os.getenv("DB_PATH", "keliva.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, full_name, password_hash 
            FROM users WHERE email = ? AND is_active = 1
        ''', (login_data.email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and verify_password(login_data.password, row[4]):
            return {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "full_name": row[3]
                },
                "token": f"token_{row[0]}_{uuid.uuid4().hex[:8]}"
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/register")
async def register_user(user_data: UserRegistration):
    """Simple registration endpoint"""
    try:
        db_path = os.getenv("DB_PATH", "keliva.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE email = ? OR username = ?', 
                      (user_data.email, user_data.username))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(user_data.password)
        
        cursor.execute('''
            INSERT INTO users (id, username, email, full_name, password_hash, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (user_id, user_data.username, user_data.email, user_data.full_name, password_hash))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Registration successful",
            "user": {
                "id": user_id,
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")