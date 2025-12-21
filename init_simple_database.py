#!/usr/bin/env python3
"""
Simple Database Initialization for KeLiva
Creates only essential tables for Grammar Check, Voice Practice, and Messaging
"""
import sqlite3
import os
from pathlib import Path

def init_simple_database():
    """Initialize simplified KeLiva database with only essential tables"""
    
    # Database path
    db_path = "keliva.db"
    
    # Remove existing database to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Removed existing database: {db_path}")
    
    # Connect to database (creates new file)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Read and execute schema
    schema_path = Path(__file__).parent / "simple_schema.sql"
    
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    try:
        # Execute schema
        cursor.executescript(schema_sql)
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print("✅ Simple database initialized successfully!")
        print(f"📁 Database location: {os.path.abspath(db_path)}")
        print(f"📊 Created tables: {tables}")
        
        # Test basic operations
        cursor.execute("INSERT INTO users (id, name, preferred_language) VALUES (?, ?, ?)", 
                      ("test-user", "Test User", "en"))
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count > 0:
            print("✅ Database test successful!")
            # Clean up test data
            cursor.execute("DELETE FROM users WHERE id = 'test-user'")
            conn.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    success = init_simple_database()
    if success:
        print("\n🎉 Ready to use KeLiva with simplified features!")
        print("📝 Features available:")
        print("   • Grammar Check")
        print("   • Voice Practice") 
        print("   • Telegram Bot")
        print("   • WhatsApp Integration")
        print("   • Web Interface")
    else:
        print("\n❌ Database initialization failed!")
        exit(1)