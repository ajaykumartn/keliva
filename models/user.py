"""
User Model and Authentication System
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import hashlib
import secrets
import jwt
from dataclasses import dataclass
import sqlite3
import json

@dataclass
class User:
    id: str
    username: str
    email: str
    full_name: str
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    profile_picture: Optional[str] = None
    preferred_languages: List[str] = None
    learning_goals: List[str] = None
    family_group_id: Optional[str] = None

    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'profile_picture': self.profile_picture,
            'preferred_languages': self.preferred_languages or [],
            'learning_goals': self.learning_goals or [],
            'family_group_id': self.family_group_id,

        }

@dataclass
class FamilyGroup:
    id: str
    name: str
    created_by: str
    created_at: datetime
    members: List[str]
    group_settings: Dict[str, Any]
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'members': self.members,
            'group_settings': self.group_settings,
            'is_active': self.is_active
        }

@dataclass
class VoiceBiometric:
    id: str
    user_id: str
    voice_features: Dict[str, Any]
    created_at: datetime
    last_updated: datetime
    accuracy_score: float
    sample_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'voice_features': self.voice_features,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'accuracy_score': self.accuracy_score,
            'sample_count': self.sample_count
        }

@dataclass
class DreamJournalEntry:
    id: str
    user_id: str
    dream_text: str
    language: str
    emotion_detected: Optional[str]
    keywords_extracted: List[str]
    created_at: datetime
    voice_recording_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'dream_text': self.dream_text,
            'language': self.language,
            'emotion_detected': self.emotion_detected,
            'keywords_extracted': self.keywords_extracted,
            'created_at': self.created_at.isoformat(),
            'voice_recording_url': self.voice_recording_url
        }

class UserManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.secret_key = "your-secret-key-here"  # Should be in environment variables
        self.init_database()
    
    def init_database(self):
        """Initialize user-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                profile_picture TEXT,
                preferred_languages TEXT,
                learning_goals TEXT,
                family_group_id TEXT,

            )
        ''')
        
        # Family groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_groups (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                members TEXT NOT NULL,
                group_settings TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Voice biometrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_biometrics (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                voice_features TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accuracy_score REAL DEFAULT 0.0,
                sample_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Dream journal table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dream_journal (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                dream_text TEXT NOT NULL,
                language TEXT NOT NULL,
                emotion_detected TEXT,
                keywords_extracted TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                voice_recording_url TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Family chat messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_chat_messages (
                id TEXT PRIMARY KEY,
                family_group_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                message_text TEXT,
                message_type TEXT DEFAULT 'text',
                voice_url TEXT,
                video_url TEXT,
                emotion_detected TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (family_group_id) REFERENCES family_groups (id),
                FOREIGN KEY (sender_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_hex = password_hash.split(':')
            password_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_check.hex() == hash_hex
        except:
            return False
    
    def generate_token(self, user_id: str) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=7)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['user_id']
        except:
            return None
    
    def create_user(self, username: str, email: str, full_name: str, password: str) -> Optional[User]:
        """Create new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            user_id = secrets.token_urlsafe(16)
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (id, username, email, full_name, password_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, email, full_name, password_hash))
            
            conn.commit()
            
            return User(
                id=user_id,
                username=username,
                email=email,
                full_name=full_name,
                password_hash=password_hash,
                created_at=datetime.now()
            )
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return user object"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users WHERE username = ? AND is_active = 1
        ''', (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and self.verify_password(password, row[4]):  # row[4] is password_hash
            # Update last login
            self.update_last_login(row[0])
            
            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                full_name=row[3],
                password_hash=row[4],
                created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                last_login=datetime.fromisoformat(row[6]) if row[6] else None,
                is_active=bool(row[7]),
                profile_picture=row[8],
                preferred_languages=json.loads(row[9]) if row[9] else [],
                learning_goals=json.loads(row[10]) if row[10] else [],
                family_group_id=row[11],
                voice_biometric_id=row[12]
            )
        return None
    
    def authenticate_user_by_email(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and return user object"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, full_name, password_hash, created_at, 
                   last_login, is_active, profile_picture, preferred_languages, 
                   learning_goals, family_group_id 
            FROM users WHERE email = ? AND is_active = 1
        ''', (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and self.verify_password(password, row[4]):  # row[4] is password_hash
            # Update last login
            self.update_last_login(row[0])
            
            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                full_name=row[3],
                password_hash=row[4],
                created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                last_login=datetime.fromisoformat(row[6]) if row[6] else None,
                is_active=bool(row[7]),
                profile_picture=row[8],
                preferred_languages=json.loads(row[9]) if row[9] else [],
                learning_goals=json.loads(row[10]) if row[10] else [],
                family_group_id=row[11],
                voice_biometric_id=row[12]
            )
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                full_name=row[3],
                password_hash=row[4],
                created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                last_login=datetime.fromisoformat(row[6]) if row[6] else None,
                is_active=bool(row[7]),
                profile_picture=row[8],
                preferred_languages=json.loads(row[9]) if row[9] else [],
                learning_goals=json.loads(row[10]) if row[10] else [],
                family_group_id=row[11],
                voice_biometric_id=row[12]
            )
        return None
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()