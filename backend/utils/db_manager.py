"""
Database manager for SQLite/Cloudflare D1
Provides CRUD operations for all models
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import (
    User, UserCreate,
    Conversation, ConversationCreate,
    Message, MessageCreate,
    GrammarCorrection, GrammarCorrectionCreate,
    UserFact, UserFactCreate,
    GrammarError
)


class DatabaseManager:
    """
    Database manager that works with both local SQLite and Cloudflare D1
    For local development, uses sqlite3
    For production, uses D1 bindings via request.state.env.DB
    """
    
    def __init__(self, db_path: str = "keliva.db", db_connection=None):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file (for local development)
            db_connection: D1 database connection (for Cloudflare deployment)
        """
        self.db_path = db_path
        self.db_connection = db_connection
        
        # If using local SQLite, initialize the database
        if not db_connection:
            self._init_local_db()
    
    def _init_local_db(self):
        """Initialize local SQLite database with schema"""
        schema_path = Path(__file__).parent.parent.parent / "schema.sql"
        
        if not Path(self.db_path).exists() and schema_path.exists():
            conn = sqlite3.connect(self.db_path)
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
            conn.commit()
            conn.close()
    
    def _get_connection(self):
        """Get database connection (local SQLite or D1)"""
        if self.db_connection:
            return self.db_connection
        return sqlite3.connect(self.db_path)
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a SELECT query and return results as list of dicts"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        if not self.db_connection:
            conn.close()
        
        return results
    
    def _execute_write(self, query: str, params: tuple = ()) -> str:
        """Execute an INSERT/UPDATE/DELETE query"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        
        if not self.db_connection:
            conn.close()
        
        return str(last_id)
    
    # User CRUD operations
    def create_user(self, user: UserCreate) -> User:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Generate a username from session_id or telegram_id if not provided
        username = f"user_{user_id[:8]}"
        
        query = """
        INSERT INTO users (id, telegram_id, session_id, name, preferred_language, created_at, last_active, username, email, full_name, password_hash, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            user_id, 
            user.telegram_id, 
            user.session_id, 
            user.name, 
            user.preferred_language, 
            now, 
            now,
            username,
            f"{username}@guest.keliva.app",
            user.name or username,
            "",  # empty password for guest users
            1
        )
        
        self._execute_write(query, params)
        
        return self.get_user(user_id)
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = ?"
        results = self._execute_query(query, (user_id,))
        
        if results:
            row = results[0]
            return User(
                id=row['id'],
                telegram_id=row['telegram_id'],
                session_id=row.get('session_id'),
                name=row['name'],
                preferred_language=row['preferred_language'],
                created_at=datetime.fromisoformat(row['created_at']),
                last_active=datetime.fromisoformat(row['last_active'])
            )
        return None
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        query = "SELECT * FROM users WHERE telegram_id = ?"
        results = self._execute_query(query, (telegram_id,))
        
        if results:
            row = results[0]
            return User(
                id=row['id'],
                telegram_id=row['telegram_id'],
                session_id=row.get('session_id'),
                name=row['name'],
                preferred_language=row['preferred_language'],
                created_at=datetime.fromisoformat(row['created_at']),
                last_active=datetime.fromisoformat(row['last_active'])
            )
        return None
    
    def get_user_by_session_id(self, session_id: str) -> Optional[User]:
        """Get user by session ID (for web users)"""
        query = "SELECT * FROM users WHERE session_id = ?"
        results = self._execute_query(query, (session_id,))
        
        if results:
            row = results[0]
            return User(
                id=row['id'],
                telegram_id=row['telegram_id'],
                session_id=row.get('session_id'),
                name=row['name'],
                preferred_language=row['preferred_language'],
                created_at=datetime.fromisoformat(row['created_at']),
                last_active=datetime.fromisoformat(row['last_active'])
            )
        return None
    
    def update_user_last_active(self, user_id: str) -> None:
        """Update user's last active timestamp"""
        now = datetime.utcnow().isoformat()
        query = "UPDATE users SET last_active = ? WHERE id = ?"
        self._execute_write(query, (now, user_id))
    
    def list_users(self) -> List[User]:
        """List all users"""
        query = "SELECT * FROM users ORDER BY created_at DESC"
        results = self._execute_query(query)
        
        return [
            User(
                id=row['id'],
                telegram_id=row['telegram_id'],
                session_id=row.get('session_id'),
                name=row['name'],
                preferred_language=row['preferred_language'],
                created_at=datetime.fromisoformat(row['created_at']),
                last_active=datetime.fromisoformat(row['last_active'])
            )
            for row in results
        ]
    
    def find_users_by_name(self, name: str) -> List[User]:
        """Find all users with the given name across all platforms"""
        query = "SELECT * FROM users WHERE LOWER(name) = LOWER(?) ORDER BY last_active DESC"
        results = self._execute_query(query, (name,))
        
        users = []
        for row in results:
            users.append(User(
                id=row['id'],
                telegram_id=row['telegram_id'],
                session_id=row.get('session_id'),
                name=row['name'],
                preferred_language=row['preferred_language'],
                created_at=datetime.fromisoformat(row['created_at']),
                last_active=datetime.fromisoformat(row['last_active'])
            ))
        return users
    
    # Conversation CRUD operations
    def create_conversation(self, conversation: ConversationCreate) -> Conversation:
        """Create a new conversation"""
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        query = """
        INSERT INTO conversations (id, user_id, started_at, interface)
        VALUES (?, ?, ?, ?)
        """
        params = (conversation_id, conversation.user_id, now, conversation.interface)
        
        self._execute_write(query, params)
        
        return self.get_conversation(conversation_id)
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        query = "SELECT * FROM conversations WHERE id = ?"
        results = self._execute_query(query, (conversation_id,))
        
        if results:
            row = results[0]
            return Conversation(
                id=row['id'],
                user_id=row['user_id'],
                started_at=datetime.fromisoformat(row['started_at']),
                ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] else None,
                interface=row['interface']
            )
        return None
    
    def get_user_conversations(self, user_id: str, limit: int = 10, interface: Optional[str] = None) -> List[Conversation]:
        """
        Get conversations for a user, optionally filtered by interface.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to retrieve
            interface: Optional interface filter (telegram, whatsapp, web)
        
        Returns:
            List of conversations ordered by most recent first
        """
        if interface:
            query = """
            SELECT * FROM conversations 
            WHERE user_id = ? AND interface = ?
            ORDER BY started_at DESC 
            LIMIT ?
            """
            results = self._execute_query(query, (user_id, interface, limit))
        else:
            query = """
            SELECT * FROM conversations 
            WHERE user_id = ? 
            ORDER BY started_at DESC 
            LIMIT ?
            """
            results = self._execute_query(query, (user_id, limit))
        
        return [
            Conversation(
                id=row['id'],
                user_id=row['user_id'],
                started_at=datetime.fromisoformat(row['started_at']),
                ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] else None,
                interface=row['interface']
            )
            for row in results
        ]
    
    def end_conversation(self, conversation_id: str) -> None:
        """Mark conversation as ended"""
        now = datetime.utcnow().isoformat()
        query = "UPDATE conversations SET ended_at = ? WHERE id = ?"
        self._execute_write(query, (now, conversation_id))
    
    # Message CRUD operations
    def create_message(self, message: MessageCreate) -> Message:
        """Create a new message"""
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Convert metadata dict to JSON string
        metadata_json = json.dumps(message.metadata) if message.metadata else None
        
        query = """
        INSERT INTO messages (id, conversation_id, role, content, language, message_type, metadata, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            message_id, 
            message.conversation_id, 
            message.role, 
            message.content,
            message.language,
            message.message_type,
            metadata_json,
            now
        )
        
        self._execute_write(query, params)
        
        return self.get_message(message_id)
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        query = "SELECT * FROM messages WHERE id = ?"
        results = self._execute_query(query, (message_id,))
        
        if results:
            row = results[0]
            metadata = json.loads(row['metadata']) if row['metadata'] else None
            
            return Message(
                id=row['id'],
                conversation_id=row['conversation_id'],
                role=row['role'],
                content=row['content'],
                language=row['language'],
                message_type=row['message_type'],
                metadata=metadata,
                timestamp=datetime.fromisoformat(row['timestamp'])
            )
        return None
    
    def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[Message]:
        """Get messages for a conversation"""
        query = """
        SELECT * FROM messages 
        WHERE conversation_id = ? 
        ORDER BY timestamp ASC 
        LIMIT ?
        """
        results = self._execute_query(query, (conversation_id, limit))
        
        messages = []
        for row in results:
            metadata = json.loads(row['metadata']) if row['metadata'] else None
            messages.append(Message(
                id=row['id'],
                conversation_id=row['conversation_id'],
                role=row['role'],
                content=row['content'],
                language=row['language'],
                message_type=row['message_type'],
                metadata=metadata,
                timestamp=datetime.fromisoformat(row['timestamp'])
            ))
        
        return messages
    
    def get_user_messages_across_all_interfaces(self, user_id: str, limit: int = 100) -> List[Message]:
        """
        Get all messages for a user across all conversations and interfaces.
        This enables cross-platform conversation continuity.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of messages ordered by timestamp (oldest first)
        """
        query = """
        SELECT m.* FROM messages m
        INNER JOIN conversations c ON m.conversation_id = c.id
        WHERE c.user_id = ?
        ORDER BY m.timestamp ASC
        LIMIT ?
        """
        results = self._execute_query(query, (user_id, limit))
        
        messages = []
        for row in results:
            metadata = json.loads(row['metadata']) if row['metadata'] else None
            messages.append(Message(
                id=row['id'],
                conversation_id=row['conversation_id'],
                role=row['role'],
                content=row['content'],
                language=row['language'],
                message_type=row['message_type'],
                metadata=metadata,
                timestamp=datetime.fromisoformat(row['timestamp'])
            ))
        
        return messages
    
    # Grammar Correction CRUD operations
    def create_grammar_correction(self, correction: GrammarCorrectionCreate) -> GrammarCorrection:
        """Create a new grammar correction"""
        correction_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Convert errors list to JSON string
        errors_json = json.dumps([error.dict() for error in correction.errors])
        
        query = """
        INSERT INTO grammar_corrections (id, message_id, original_text, corrected_text, errors, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            correction_id,
            correction.message_id,
            correction.original_text,
            correction.corrected_text,
            errors_json,
            now
        )
        
        self._execute_write(query, params)
        
        return self.get_grammar_correction(correction_id)
    
    def get_grammar_correction(self, correction_id: str) -> Optional[GrammarCorrection]:
        """Get grammar correction by ID"""
        query = "SELECT * FROM grammar_corrections WHERE id = ?"
        results = self._execute_query(query, (correction_id,))
        
        if results:
            row = results[0]
            errors_data = json.loads(row['errors']) if row['errors'] else []
            errors = [GrammarError(**error) for error in errors_data]
            
            return GrammarCorrection(
                id=row['id'],
                message_id=row['message_id'],
                original_text=row['original_text'],
                corrected_text=row['corrected_text'],
                errors=errors,
                timestamp=datetime.fromisoformat(row['timestamp'])
            )
        return None
    
    def get_grammar_correction_by_message(self, message_id: str) -> Optional[GrammarCorrection]:
        """Get grammar correction by message ID"""
        query = "SELECT * FROM grammar_corrections WHERE message_id = ?"
        results = self._execute_query(query, (message_id,))
        
        if results:
            row = results[0]
            errors_data = json.loads(row['errors']) if row['errors'] else []
            errors = [GrammarError(**error) for error in errors_data]
            
            return GrammarCorrection(
                id=row['id'],
                message_id=row['message_id'],
                original_text=row['original_text'],
                corrected_text=row['corrected_text'],
                errors=errors,
                timestamp=datetime.fromisoformat(row['timestamp'])
            )
        return None
    
    # User Facts CRUD operations
    def create_user_fact(self, fact: UserFactCreate) -> UserFact:
        """Create a new user fact"""
        fact_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        query = """
        INSERT INTO user_facts (id, user_id, fact_text, category, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (fact_id, fact.user_id, fact.fact_text, fact.category, now)
        
        self._execute_write(query, params)
        
        return self.get_user_fact(fact_id)
    
    def get_user_fact(self, fact_id: str) -> Optional[UserFact]:
        """Get user fact by ID"""
        query = "SELECT * FROM user_facts WHERE id = ?"
        results = self._execute_query(query, (fact_id,))
        
        if results:
            row = results[0]
            return UserFact(
                id=row['id'],
                user_id=row['user_id'],
                fact_text=row['fact_text'],
                category=row['category'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
        return None
    
    def get_user_facts(self, user_id: str, limit: int = 100) -> List[UserFact]:
        """Get facts for a user"""
        query = """
        SELECT * FROM user_facts 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
        """
        results = self._execute_query(query, (user_id, limit))
        
        return [
            UserFact(
                id=row['id'],
                user_id=row['user_id'],
                fact_text=row['fact_text'],
                category=row['category'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
            for row in results
        ]
