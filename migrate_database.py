#!/usr/bin/env python3
"""
Database Migration Script for Family Groups
Adds missing columns and tables for the Family Groups feature
"""
import sqlite3
import os
import json
from datetime import datetime

def migrate_database(db_path="keliva.db"):
    """Migrate database to support Family Groups"""
    print("🔄 Starting Database Migration for Family Groups")
    print("=" * 50)
    
    # Backup existing database
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if family_groups table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='family_groups'
        """)
        
        if not cursor.fetchone():
            print("📝 Creating family_groups table...")
            cursor.execute('''
                CREATE TABLE family_groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    members TEXT NOT NULL, -- JSON array of member IDs
                    group_settings TEXT DEFAULT '{}', -- JSON settings
                    is_active INTEGER DEFAULT 1,
                    group_avatar TEXT,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''')
            print("✅ family_groups table created")
        else:
            print("✅ family_groups table already exists")
            
            # Check if description column exists
            cursor.execute("PRAGMA table_info(family_groups)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'description' not in columns:
                print("📝 Adding description column to family_groups...")
                cursor.execute("ALTER TABLE family_groups ADD COLUMN description TEXT")
                print("✅ description column added")
            
            if 'group_avatar' not in columns:
                print("📝 Adding group_avatar column to family_groups...")
                cursor.execute("ALTER TABLE family_groups ADD COLUMN group_avatar TEXT")
                print("✅ group_avatar column added")
        
        # Check if family_chat_messages table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='family_chat_messages'
        """)
        
        if not cursor.fetchone():
            print("📝 Creating family_chat_messages table...")
            cursor.execute('''
                CREATE TABLE family_chat_messages (
                    id TEXT PRIMARY KEY,
                    family_group_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    message_text TEXT,
                    message_type TEXT DEFAULT 'text', -- text, image, file, system
                    image_url TEXT,
                    file_url TEXT,
                    reply_to_message_id TEXT,
                    emotion_detected TEXT,
                    is_edited INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    edited_at TIMESTAMP,
                    FOREIGN KEY (family_group_id) REFERENCES family_groups(id),
                    FOREIGN KEY (sender_id) REFERENCES users(id),
                    FOREIGN KEY (reply_to_message_id) REFERENCES family_chat_messages(id)
                )
            ''')
            print("✅ family_chat_messages table created")
        else:
            print("✅ family_chat_messages table already exists")
        
        # Check if family_group_invitations table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='family_group_invitations'
        """)
        
        if not cursor.fetchone():
            print("📝 Creating family_group_invitations table...")
            cursor.execute('''
                CREATE TABLE family_group_invitations (
                    id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL,
                    invited_by TEXT NOT NULL,
                    invited_user_email TEXT,
                    invited_user_phone TEXT,
                    invitation_code TEXT UNIQUE,
                    status TEXT DEFAULT 'pending', -- pending, accepted, declined, expired
                    is_used INTEGER DEFAULT 0,
                    used_by TEXT,
                    used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES family_groups(id),
                    FOREIGN KEY (invited_by) REFERENCES users(id),
                    FOREIGN KEY (used_by) REFERENCES users(id)
                )
            ''')
            print("✅ family_group_invitations table created")
        else:
            print("✅ family_group_invitations table already exists")
            
            # Check if new columns exist
            cursor.execute("PRAGMA table_info(family_group_invitations)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_used' not in columns:
                print("📝 Adding is_used column to family_group_invitations...")
                cursor.execute("ALTER TABLE family_group_invitations ADD COLUMN is_used INTEGER DEFAULT 0")
                print("✅ is_used column added")
            
            if 'used_by' not in columns:
                print("📝 Adding used_by column to family_group_invitations...")
                cursor.execute("ALTER TABLE family_group_invitations ADD COLUMN used_by TEXT")
                print("✅ used_by column added")
            
            if 'used_at' not in columns:
                print("📝 Adding used_at column to family_group_invitations...")
                cursor.execute("ALTER TABLE family_group_invitations ADD COLUMN used_at TIMESTAMP")
                print("✅ used_at column added")
        
        # Check if family_learning_progress table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='family_learning_progress'
        """)
        
        if not cursor.fetchone():
            print("📝 Creating family_learning_progress table...")
            cursor.execute('''
                CREATE TABLE family_learning_progress (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    progress_data TEXT, -- JSON data
                    points_earned INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (group_id) REFERENCES family_groups(id)
                )
            ''')
            print("✅ family_learning_progress table created")
        else:
            print("✅ family_learning_progress table already exists")
        
        # Add family_group_id column to users table if it doesn't exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'family_group_id' not in columns:
            print("📝 Adding family_group_id column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN family_group_id TEXT")
            print("✅ family_group_id column added to users table")
        
        # Create indexes for better performance
        indexes = [
            ("idx_family_groups_created_by", "CREATE INDEX IF NOT EXISTS idx_family_groups_created_by ON family_groups(created_by)"),
            ("idx_family_chat_group", "CREATE INDEX IF NOT EXISTS idx_family_chat_group ON family_chat_messages(family_group_id)"),
            ("idx_family_chat_sender", "CREATE INDEX IF NOT EXISTS idx_family_chat_sender ON family_chat_messages(sender_id)"),
            ("idx_family_chat_timestamp", "CREATE INDEX IF NOT EXISTS idx_family_chat_timestamp ON family_chat_messages(created_at)"),
            ("idx_family_invitations_group", "CREATE INDEX IF NOT EXISTS idx_family_invitations_group ON family_group_invitations(group_id)"),
            ("idx_family_invitations_code", "CREATE INDEX IF NOT EXISTS idx_family_invitations_code ON family_group_invitations(invitation_code)"),
            ("idx_family_progress_user", "CREATE INDEX IF NOT EXISTS idx_family_progress_user ON family_learning_progress(user_id)"),
            ("idx_family_progress_group", "CREATE INDEX IF NOT EXISTS idx_family_progress_group ON family_learning_progress(group_id)")
        ]
        
        print("📝 Creating indexes...")
        for index_name, index_sql in indexes:
            cursor.execute(index_sql)
            print(f"✅ {index_name} created")
        
        # Commit all changes
        conn.commit()
        print("\n🎉 Database migration completed successfully!")
        
        # Verify tables exist
        print("\n📊 Verification:")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'family_%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        for table in tables:
            print(f"✅ Table exists: {table[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_migration(db_path="keliva.db"):
    """Verify that the migration was successful"""
    print("\n🔍 Verifying Migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Test family_groups table
        cursor.execute("SELECT id, name, description FROM family_groups LIMIT 1")
        print("✅ family_groups table accessible")
        
        # Test family_chat_messages table
        cursor.execute("SELECT id, family_group_id, sender_id FROM family_chat_messages LIMIT 1")
        print("✅ family_chat_messages table accessible")
        
        # Test family_group_invitations table
        cursor.execute("SELECT id, group_id, invitation_code, is_used FROM family_group_invitations LIMIT 1")
        print("✅ family_group_invitations table accessible")
        
        # Test family_learning_progress table
        cursor.execute("SELECT id, user_id, group_id FROM family_learning_progress LIMIT 1")
        print("✅ family_learning_progress table accessible")
        
        print("✅ All tables verified successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Family Groups Database Migration")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run migration
    success = migrate_database()
    
    if success:
        # Verify migration
        verify_migration()
        
        print("\n" + "=" * 50)
        print("🎉 Migration completed successfully!")
        print("\n📋 What was updated:")
        print("✅ family_groups table with description column")
        print("✅ family_chat_messages table for chat functionality")
        print("✅ family_group_invitations table for email invitations")
        print("✅ family_learning_progress table for progress tracking")
        print("✅ Performance indexes for all tables")
        print("✅ family_group_id column in users table")
        print("\n🚀 Your Family Groups feature is now ready to use!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        print("💡 Try running the script again or check your database permissions.")