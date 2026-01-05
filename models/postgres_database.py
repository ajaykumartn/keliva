"""
PostgreSQL Database Configuration and Models for KeLiva
Production-ready database setup with SQLAlchemy and psycopg2
Compatible with SQLAlchemy 1.4 and Pydantic v1
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
    """PostgreSQL database manager with SQLAlchemy"""
    
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
            self.engine = create_engine(self.database_url, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("PostgreSQL database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with context manager"""
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
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get database connection from pool"""
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def init_schema(self):
        """Initialize database schema"""
        async with self.get_connection() as conn:
            # Enable UUID extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    telegram_id BIGINT UNIQUE,
                    session_id TEXT UNIQUE,
                    name TEXT,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    full_name TEXT,
                    password_hash TEXT,
                    preferred_language TEXT DEFAULT 'en',
                    learning_streak INTEGER DEFAULT 0,
                    total_points INTEGER DEFAULT 0,
                    last_login TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT TRUE,
                    profile_picture TEXT
                );
            """)
            
            # Conversations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    title TEXT,
                    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    ended_at TIMESTAMP WITH TIME ZONE,
                    interface TEXT DEFAULT 'telegram',
                    metadata JSONB DEFAULT '{}'
                );
            """)
            
            # Messages table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    role TEXT CHECK(role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    language TEXT DEFAULT 'en',
                    message_type TEXT DEFAULT 'text',
                    interface_type TEXT DEFAULT 'web',
                    metadata JSONB DEFAULT '{}',
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Grammar corrections table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS grammar_corrections (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
                    original_text TEXT NOT NULL,
                    corrected_text TEXT NOT NULL,
                    errors JSONB DEFAULT '[]',
                    score INTEGER DEFAULT 0,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Voice practice sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS voice_practice_sessions (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    text_to_read TEXT NOT NULL,
                    audio_url TEXT,
                    pronunciation_score INTEGER DEFAULT 0,
                    feedback JSONB DEFAULT '{}',
                    duration_seconds INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # User facts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_facts (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    fact_text TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    confidence REAL DEFAULT 1.0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            

            
            # Create indexes for performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_session ON users(session_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_grammar_message ON grammar_corrections(message_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_voice_sessions_user ON voice_practice_sessions(user_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_facts_user ON user_facts(user_id);")
            
            logger.info("PostgreSQL schema initialized successfully")

class UserService:
    """User management service for PostgreSQL"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db = db_manager
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    
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
    
    async def create_user(self, username: str, email: str, full_name: str, password: str) -> Optional[Dict[str, Any]]:
        """Create new user"""
        async with self.db.get_connection() as conn:
            try:
                password_hash = self.hash_password(password)
                
                user_id = await conn.fetchval("""
                    INSERT INTO users (username, email, full_name, password_hash)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """, username, email, full_name, password_hash)
                
                return {
                    "id": str(user_id),
                    "username": username,
                    "email": email,
                    "full_name": full_name,
                    "created_at": datetime.now().isoformat()
                }
            except asyncpg.UniqueViolationError:
                return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by username"""
        async with self.db.get_connection() as conn:
            user = await conn.fetchrow("""
                SELECT id, username, email, full_name, password_hash, created_at, 
                       last_login, is_active, profile_picture
                FROM users 
                WHERE username = $1 AND is_active = TRUE
            """, username)
            
            if user and self.verify_password(password, user['password_hash']):
                # Update last login
                await conn.execute("""
                    UPDATE users SET last_login = NOW(), last_active = NOW() 
                    WHERE id = $1
                """, user['id'])
                
                return {
                    "id": str(user['id']),
                    "username": user['username'],
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "created_at": user['created_at'].isoformat() if user['created_at'] else None,
                    "last_login": user['last_login'].isoformat() if user['last_login'] else None,
                    "is_active": user['is_active'],
                    "profile_picture": user['profile_picture']
                }
            return None
    
    async def authenticate_user_by_email(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by email"""
        async with self.db.get_connection() as conn:
            user = await conn.fetchrow("""
                SELECT id, username, email, full_name, password_hash, created_at, 
                       last_login, is_active, profile_picture
                FROM users 
                WHERE email = $1 AND is_active = TRUE
            """, email)
            
            if user and self.verify_password(password, user['password_hash']):
                # Update last login
                await conn.execute("""
                    UPDATE users SET last_login = NOW(), last_active = NOW() 
                    WHERE id = $1
                """, user['id'])
                
                return {
                    "id": str(user['id']),
                    "username": user['username'],
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "created_at": user['created_at'].isoformat() if user['created_at'] else None,
                    "last_login": user['last_login'].isoformat() if user['last_login'] else None,
                    "is_active": user['is_active'],
                    "profile_picture": user['profile_picture']
                }
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with self.db.get_connection() as conn:
            user = await conn.fetchrow("""
                SELECT id, username, email, full_name, created_at, last_login, 
                       is_active, profile_picture
                FROM users 
                WHERE id = $1
            """, user_id)
            
            if user:
                return {
                    "id": str(user['id']),
                    "username": user['username'],
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "created_at": user['created_at'].isoformat() if user['created_at'] else None,
                    "last_login": user['last_login'].isoformat() if user['last_login'] else None,
                    "is_active": user['is_active'],
                    "profile_picture": user['profile_picture']
                }
            return None

class ConversationService:
    """Conversation management service for PostgreSQL"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db = db_manager
    
    async def create_conversation(self, user_id: str, title: str = None, interface: str = "web") -> str:
        """Create new conversation"""
        async with self.db.get_connection() as conn:
            conversation_id = await conn.fetchval("""
                INSERT INTO conversations (user_id, title, interface)
                VALUES ($1, $2, $3)
                RETURNING id
            """, user_id, title, interface)
            return str(conversation_id)
    
    async def add_message(self, conversation_id: str, user_id: str, role: str, 
                         content: str, message_type: str = "text", 
                         interface_type: str = "web", metadata: Dict = None) -> str:
        """Add message to conversation"""
        async with self.db.get_connection() as conn:
            message_id = await conn.fetchval("""
                INSERT INTO messages (conversation_id, user_id, role, content, 
                                    message_type, interface_type, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, conversation_id, user_id, role, content, message_type, 
                interface_type, json.dumps(metadata or {}))
            return str(message_id)
    
    async def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages from conversation"""
        async with self.db.get_connection() as conn:
            messages = await conn.fetch("""
                SELECT id, role, content, message_type, interface_type, 
                       metadata, timestamp
                FROM messages 
                WHERE conversation_id = $1 
                ORDER BY timestamp DESC 
                LIMIT $2
            """, conversation_id, limit)
            
            return [
                {
                    "id": str(msg['id']),
                    "role": msg['role'],
                    "content": msg['content'],
                    "message_type": msg['message_type'],
                    "interface_type": msg['interface_type'],
                    "metadata": msg['metadata'],
                    "timestamp": msg['timestamp'].isoformat()
                }
                for msg in messages
            ]

class GrammarService:
    """Grammar correction service for PostgreSQL"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db = db_manager
    
    async def save_grammar_correction(self, message_id: str, original_text: str, 
                                    corrected_text: str, errors: List[Dict], 
                                    score: int = 0) -> str:
        """Save grammar correction"""
        async with self.db.get_connection() as conn:
            correction_id = await conn.fetchval("""
                INSERT INTO grammar_corrections (message_id, original_text, 
                                               corrected_text, errors, score)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, message_id, original_text, corrected_text, 
                json.dumps(errors), score)
            return str(correction_id)
    
    async def get_user_grammar_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's grammar correction history"""
        async with self.db.get_connection() as conn:
            corrections = await conn.fetch("""
                SELECT gc.id, gc.original_text, gc.corrected_text, 
                       gc.errors, gc.score, gc.timestamp
                FROM grammar_corrections gc
                JOIN messages m ON gc.message_id = m.id
                WHERE m.user_id = $1
                ORDER BY gc.timestamp DESC
                LIMIT $2
            """, user_id, limit)
            
            return [
                {
                    "id": str(corr['id']),
                    "original_text": corr['original_text'],
                    "corrected_text": corr['corrected_text'],
                    "errors": corr['errors'],
                    "score": corr['score'],
                    "timestamp": corr['timestamp'].isoformat()
                }
                for corr in corrections
            ]

class VoiceService:
    """Voice practice service for PostgreSQL"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db = db_manager
    
    async def save_voice_session(self, user_id: str, text_to_read: str, 
                                audio_url: str = None, pronunciation_score: int = 0,
                                feedback: Dict = None, duration_seconds: int = 0) -> str:
        """Save voice practice session"""
        async with self.db.get_connection() as conn:
            session_id = await conn.fetchval("""
                INSERT INTO voice_practice_sessions (user_id, text_to_read, audio_url, 
                                                   pronunciation_score, feedback, duration_seconds)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, user_id, text_to_read, audio_url, pronunciation_score, 
                json.dumps(feedback or {}), duration_seconds)
            return str(session_id)
    
    async def get_user_voice_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's voice practice history"""
        async with self.db.get_connection() as conn:
            sessions = await conn.fetch("""
                SELECT id, text_to_read, audio_url, pronunciation_score, 
                       feedback, duration_seconds, created_at
                FROM voice_practice_sessions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, user_id, limit)
            
            return [
                {
                    "id": str(session['id']),
                    "text_to_read": session['text_to_read'],
                    "audio_url": session['audio_url'],
                    "pronunciation_score": session['pronunciation_score'],
                    "feedback": session['feedback'],
                    "duration_seconds": session['duration_seconds'],
                    "created_at": session['created_at'].isoformat()
                }
                for session in sessions
            ]

# Global database manager instance
db_manager = PostgreSQLManager()
user_service = UserService(db_manager)
conversation_service = ConversationService(db_manager)
grammar_service = GrammarService(db_manager)
voice_service = VoiceService(db_manager)