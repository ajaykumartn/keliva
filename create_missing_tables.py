#!/usr/bin/env python3
"""
Create missing family tables
"""
import sqlite3

def create_missing_tables():
    print("🔧 Creating Missing Family Tables")
    print("=" * 40)
    
    db_path = "backend/keliva.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create family_group_invitations table
        print("📝 Creating family_group_invitations table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_group_invitations (
                id TEXT PRIMARY KEY,
                group_id TEXT NOT NULL,
                invited_by TEXT NOT NULL,
                invited_user_email TEXT,
                invited_user_phone TEXT,
                invitation_code TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
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
        
        # Create family_learning_progress table
        print("📝 Creating family_learning_progress table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_learning_progress (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                group_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                progress_data TEXT,
                points_earned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (group_id) REFERENCES family_groups(id)
            )
        ''')
        print("✅ family_learning_progress table created")
        
        # Create indexes
        print("📝 Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_family_invitations_group ON family_group_invitations(group_id)",
            "CREATE INDEX IF NOT EXISTS idx_family_invitations_code ON family_group_invitations(invitation_code)",
            "CREATE INDEX IF NOT EXISTS idx_family_progress_user ON family_learning_progress(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_family_progress_group ON family_learning_progress(group_id)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print("✅ Indexes created")
        
        # Commit changes
        conn.commit()
        
        # Verify tables exist
        print("\n🔍 Verification:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'family_%' ORDER BY name")
        family_tables = cursor.fetchall()
        
        expected_tables = ['family_chat_messages', 'family_groups', 'family_group_invitations', 'family_learning_progress']
        
        for table_name in expected_tables:
            if any(table[0] == table_name for table in family_tables):
                print(f"✅ {table_name} exists")
            else:
                print(f"❌ {table_name} missing")
        
        print("\n🎉 All family tables are now ready!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    create_missing_tables()