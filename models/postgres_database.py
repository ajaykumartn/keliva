"""
PostgreSQL Database Configuration and Models for KeLiva
Production-ready database setup with SQLAlchemy 1.4
Compatible with older FastAPI and Python versions
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import uuid
import hashlib
import secrets
import logging
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from contextlib import contextmanager

logger = logging.getLogger(__name__)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(String(50), unique=True, index=True)
    username = Column(String(100))
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    message = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String(100), index=True)

class GrammarCorrection(Base):
    __tablename__ = "grammar_corrections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    original_text = Column(Text)
    corrected_text = Column(Text)
    corrections = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

class VoicePractice(Base):
    __tablename__ = "voice_practices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    text = Column(Text)
    audio_url = Column(String(500))
    feedback = Column(Text)
    score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class PostgreSQLManager:
    """PostgreSQL database manager with SQLAlchemy 1.4"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            # Fallback to individual components
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            database = os.getenv("DB_NAME", "keliva")
            user = os.getenv("DB_USER", "postgres")
            password = os.getenv("DB_PASSWORD", "")
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def init_db(self):
        """Initialize database connection"""
        try:
            if not self.database_url:
                logger.warning("No DATABASE_URL provided, database will not be available")
                return
                
            self.engine = create_engine(self.database_url, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("PostgreSQL database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            # Don't raise the exception, just log it
            self.engine = None
            self.SessionLocal = None
    
    @contextmanager
    def get_session(self):
        """Get database session with context manager"""
        if not self.SessionLocal:
            raise Exception("Database not initialized")
            
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

class UserService:
    """User management service"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db_manager = db_manager
    
    def create_user(self, telegram_id: str = None, username: str = None, 
                   email: str = None, password: str = None) -> Optional[str]:
        """Create a new user"""
        try:
            # Check if database is initialized
            if not self.db_manager.engine or not self.db_manager.SessionLocal:
                logger.warning("Database not initialized, skipping user creation")
                return None
                
            with self.db_manager.get_session() as session:
                # Hash password if provided
                password_hash = None
                if password:
                    import bcrypt
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    email=email,
                    password_hash=password_hash
                )
                session.add(user)
                session.flush()
                return str(user.id)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by username or email"""
        try:
            with self.db_manager.get_session() as session:
                # Try username first
                user = session.query(User).filter(User.username == username, User.is_active == True).first()
                
                # If not found, try email
                if not user:
                    user = session.query(User).filter(User.email == username, User.is_active == True).first()
                
                if user and user.password_hash:
                    # Verify password
                    import bcrypt
                    if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                        return {
                            "id": str(user.id),
                            "telegram_id": user.telegram_id,
                            "username": user.username,
                            "email": user.email,
                            "created_at": user.created_at.isoformat(),
                            "is_active": user.is_active
                        }
                return None
        except Exception as e:
            logger.error(f"Failed to authenticate user: {e}")
            return None

    def get_user_by_telegram_id(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if user:
                    return {
                        "id": str(user.id),
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "email": user.email,
                        "created_at": user.created_at.isoformat(),
                        "is_active": user.is_active
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None

class ConversationService:
    """Conversation management service"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db_manager = db_manager
    
    def save_conversation(self, user_id: str, message: str, response: str, 
                         session_id: str = None) -> bool:
        """Save conversation to database"""
        try:
            with self.db_manager.get_session() as session:
                conversation = Conversation(
                    user_id=uuid.UUID(user_id),
                    message=message,
                    response=response,
                    session_id=session_id or str(uuid.uuid4())
                )
                session.add(conversation)
                return True
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False
    
    def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user conversations"""
        try:
            with self.db_manager.get_session() as session:
                conversations = session.query(Conversation)\
                    .filter(Conversation.user_id == uuid.UUID(user_id))\
                    .order_by(Conversation.created_at.desc())\
                    .limit(limit).all()
                
                return [{
                    "id": str(conv.id),
                    "message": conv.message,
                    "response": conv.response,
                    "created_at": conv.created_at.isoformat(),
                    "session_id": conv.session_id
                } for conv in conversations]
        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return []

class GrammarService:
    """Grammar correction service"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db_manager = db_manager
    
    def save_grammar_correction(self, user_id: str, original_text: str, 
                              corrected_text: str, corrections: List[Dict]) -> bool:
        """Save grammar correction"""
        try:
            # Check if database is initialized
            if not self.db_manager.engine or not self.db_manager.SessionLocal:
                logger.warning("Database not initialized, skipping grammar correction save")
                return False
                
            with self.db_manager.get_session() as session:
                correction = GrammarCorrection(
                    user_id=uuid.UUID(user_id),
                    original_text=original_text,
                    corrected_text=corrected_text,
                    corrections=json.dumps(corrections)
                )
                session.add(correction)
                return True
        except Exception as e:
            logger.error(f"Failed to save grammar correction: {e}")
            return False
    
    def get_user_grammar_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's grammar correction history"""
        try:
            # Check if database is initialized
            if not self.db_manager.engine or not self.db_manager.SessionLocal:
                logger.warning("Database not initialized, returning empty grammar history")
                return []
                
            with self.db_manager.get_session() as session:
                corrections = session.query(GrammarCorrection)\
                    .filter(GrammarCorrection.user_id == uuid.UUID(user_id))\
                    .order_by(GrammarCorrection.created_at.desc())\
                    .limit(limit).all()
                
                return [{
                    "id": str(corr.id),
                    "original_text": corr.original_text,
                    "corrected_text": corr.corrected_text,
                    "corrections": json.loads(corr.corrections) if corr.corrections else [],
                    "created_at": corr.created_at.isoformat()
                } for corr in corrections]
        except Exception as e:
            logger.error(f"Failed to get grammar history: {e}")
            return []

class VoiceService:
    """Voice practice service"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db_manager = db_manager
    
    def save_voice_practice(self, user_id: str, text: str, audio_url: str = None, 
                          feedback: str = None, score: int = None) -> bool:
        """Save voice practice session"""
        try:
            with self.db_manager.get_session() as session:
                practice = VoicePractice(
                    user_id=uuid.UUID(user_id),
                    text=text,
                    audio_url=audio_url,
                    feedback=feedback,
                    score=score
                )
                session.add(practice)
                return True
        except Exception as e:
            logger.error(f"Failed to save voice practice: {e}")
            return False

# Initialize services
db_manager = PostgreSQLManager()
user_service = UserService(db_manager)
conversation_service = ConversationService(db_manager)
grammar_service = GrammarService(db_manager)
voice_service = VoiceService(db_manager)