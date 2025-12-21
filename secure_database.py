"""
Secure Database Configuration for KeLiva
Implements secure database connections and query protection
"""

import os
import asyncio
import asyncpg
import sqlite3
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
import logging
from security_config import SecurityConfig, log_security_event

logger = logging.getLogger(__name__)

class SecureDatabase:
    """Secure database manager with SQL injection protection"""
    
    def __init__(self):
        self.database_url = SecurityConfig.DATABASE_URL
        self.connection_pool = None
        self.is_sqlite = self.database_url.startswith("sqlite")
    
    async def initialize(self):
        """Initialize secure database connection"""
        try:
            if not self.is_sqlite:
                # PostgreSQL connection with security settings
                self.connection_pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=1,
                    max_size=10,
                    command_timeout=30,
                    server_settings={
                        'application_name': 'keliva_secure',
                        'search_path': 'public'
                    }
                )
                logger.info("Secure PostgreSQL connection pool initialized")
            else:
                logger.info("Using SQLite database")
        except Exception as e:
            log_security_event("DATABASE_CONNECTION_FAILED", {"error": str(e)}, "ERROR")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get secure database connection"""
        if self.is_sqlite:
            # SQLite connection
            conn = sqlite3.connect(
                self.database_url.replace("sqlite:///", ""),
                timeout=30.0,
                isolation_level=None  # Autocommit mode
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
            try:
                yield conn
            finally:
                conn.close()
        else:
            # PostgreSQL connection from pool
            async with self.connection_pool.acquire() as conn:
                yield conn
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """Execute parameterized query safely"""
        if params is None:
            params = {}
        
        # Log query for security monitoring (without sensitive data)
        sanitized_query = self._sanitize_query_for_logging(query)
        logger.info(f"Executing query: {sanitized_query}")
        
        try:
            async with self.get_connection() as conn:
                if self.is_sqlite:
                    # SQLite execution
                    cursor = conn.cursor()
                    
                    # Convert named parameters to positional for SQLite
                    if params:
                        # Replace named parameters with ? placeholders
                        param_values = []
                        modified_query = query
                        for key, value in params.items():
                            modified_query = modified_query.replace(f":{key}", "?")
                            param_values.append(value)
                        
                        cursor.execute(modified_query, param_values)
                    else:
                        cursor.execute(query)
                    
                    # Fetch results
                    if query.strip().upper().startswith("SELECT"):
                        rows = cursor.fetchall()
                        return [dict(row) for row in rows]
                    else:
                        conn.commit()
                        return [{"affected_rows": cursor.rowcount}]
                
                else:
                    # PostgreSQL execution
                    if query.strip().upper().startswith("SELECT"):
                        rows = await conn.fetch(query, *params.values())
                        return [dict(row) for row in rows]
                    else:
                        result = await conn.execute(query, *params.values())
                        return [{"affected_rows": int(result.split()[-1]) if result else 0}]
        
        except Exception as e:
            log_security_event(
                "DATABASE_QUERY_FAILED", 
                {"query": sanitized_query, "error": str(e)}, 
                "ERROR"
            )
            raise
    
    async def safe_insert(self, table: str, data: Dict[str, Any]) -> int:
        """Safely insert data with parameter binding"""
        # Validate table name (prevent SQL injection)
        if not self._is_valid_table_name(table):
            raise ValueError(f"Invalid table name: {table}")
        
        # Sanitize input data
        sanitized_data = {}
        for key, value in data.items():
            if not self._is_valid_column_name(key):
                raise ValueError(f"Invalid column name: {key}")
            sanitized_data[key] = SecurityConfig.sanitize_input(str(value)) if isinstance(value, str) else value
        
        # Build parameterized query
        columns = ", ".join(sanitized_data.keys())
        placeholders = ", ".join([f":{key}" for key in sanitized_data.keys()])
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        result = await self.execute_query(query, sanitized_data)
        return result[0].get("affected_rows", 0)
    
    async def safe_update(self, table: str, data: Dict[str, Any], where_clause: str, where_params: Dict[str, Any]) -> int:
        """Safely update data with parameter binding"""
        # Validate table name
        if not self._is_valid_table_name(table):
            raise ValueError(f"Invalid table name: {table}")
        
        # Sanitize input data
        sanitized_data = {}
        for key, value in data.items():
            if not self._is_valid_column_name(key):
                raise ValueError(f"Invalid column name: {key}")
            sanitized_data[key] = SecurityConfig.sanitize_input(str(value)) if isinstance(value, str) else value
        
        # Build parameterized query
        set_clause = ", ".join([f"{key} = :{key}" for key in sanitized_data.keys()])
        
        # Combine data and where parameters
        all_params = {**sanitized_data, **where_params}
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        result = await self.execute_query(query, all_params)
        return result[0].get("affected_rows", 0)
    
    async def safe_select(self, table: str, columns: List[str] = None, where_clause: str = "", where_params: Dict[str, Any] = None) -> List[Dict]:
        """Safely select data with parameter binding"""
        # Validate table name
        if not self._is_valid_table_name(table):
            raise ValueError(f"Invalid table name: {table}")
        
        # Validate column names
        if columns:
            for col in columns:
                if not self._is_valid_column_name(col):
                    raise ValueError(f"Invalid column name: {col}")
            columns_str = ", ".join(columns)
        else:
            columns_str = "*"
        
        # Build query
        query = f"SELECT {columns_str} FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        return await self.execute_query(query, where_params or {})
    
    def _is_valid_table_name(self, table_name: str) -> bool:
        """Validate table name to prevent SQL injection"""
        import re
        # Allow only alphanumeric characters and underscores
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name))
    
    def _is_valid_column_name(self, column_name: str) -> bool:
        """Validate column name to prevent SQL injection"""
        import re
        # Allow only alphanumeric characters and underscores
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name))
    
    def _sanitize_query_for_logging(self, query: str) -> str:
        """Remove sensitive data from query for logging"""
        # Remove potential passwords, tokens, etc.
        import re
        sanitized = re.sub(r'(password|token|secret|key)\s*=\s*[\'"][^\'"]*[\'"]', r'\1=***', query, flags=re.IGNORECASE)
        return sanitized
    
    async def close(self):
        """Close database connections"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("Database connection pool closed")

# Global secure database instance
secure_db = SecureDatabase()

# Utility functions for common operations
async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Safely get user by ID"""
    try:
        results = await secure_db.safe_select(
            "users", 
            columns=["id", "username", "email", "full_name", "created_at"],
            where_clause="id = :user_id",
            where_params={"user_id": user_id}
        )
        return results[0] if results else None
    except Exception as e:
        log_security_event("USER_LOOKUP_FAILED", {"user_id": user_id, "error": str(e)}, "WARNING")
        return None

async def create_user_safely(username: str, email: str, password_hash: str, full_name: str = "") -> Optional[int]:
    """Safely create a new user"""
    try:
        # Validate input
        if not username or not email or not password_hash:
            raise ValueError("Missing required fields")
        
        # Check if user already exists
        existing = await secure_db.safe_select(
            "users",
            columns=["id"],
            where_clause="username = :username OR email = :email",
            where_params={"username": username, "email": email}
        )
        
        if existing:
            log_security_event("USER_CREATION_DUPLICATE", {"username": username, "email": email}, "WARNING")
            return None
        
        # Create user
        result = await secure_db.safe_insert("users", {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "created_at": "datetime('now')"
        })
        
        log_security_event("USER_CREATED", {"username": username}, "INFO")
        return result
        
    except Exception as e:
        log_security_event("USER_CREATION_FAILED", {"username": username, "error": str(e)}, "ERROR")
        return None

# Initialize database on import
async def init_secure_database():
    """Initialize the secure database"""
    await secure_db.initialize()

# Export main components
__all__ = ['SecureDatabase', 'secure_db', 'get_user_by_id', 'create_user_safely', 'init_secure_database']