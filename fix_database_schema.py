#!/usr/bin/env python3
"""
Fix Database Schema Issues
Directly checks and fixes the family_groups table schema
"""
import sqlite3
import os
import json
from datetime import datetime

def check_and_fix_database():
    """Check and fix the database schema issues"""
    print("🔧 Checking and Fixing Database Schema")
    print("=" * 50)
    
    db_path = "backend/keliva.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current schema of family_groups table
        print("📊 Checking family_groups table schema...")
        cursor.execute("PRAGMA table_info(family_groups)")
        columns = cursor.fetchall()
        
        print("Current columns:")
        column_names = []
        for col in columns:
            column_names.append(col[1])
            print(f"   - {col[1]} ({col[2]})")
        
        # Check if description column exists
        if 'description' not in column_names:
            print("\n❌ Missing 'description' column - adding it...")
            cursor.execute("ALTER TABLE family_groups ADD COLUMN description TEXT")
            print("✅ Added 'description' column")
        else:
            print("\n✅ 'description' column exists")
        
        # Check if group_avatar column exists
        if 'group_avatar' not in column_names:
            print("❌ Missing 'group_avatar' column - adding it...")
            cursor.execute("ALTER TABLE family_groups ADD COLUMN group_avatar TEXT")
            print("✅ Added 'group_avatar' column")
        else:
            print("✅ 'group_avatar' column exists")
        
        # Test the problematic query
        print("\n🧪 Testing the problematic query...")
        try:
            cursor.execute('''
                SELECT fg.id, fg.name, fg.description, fg.created_by, fg.created_at, 
                       fg.members, fg.group_settings, fg.is_active, fg.group_avatar, 
                       u.full_name as creator_name
                FROM family_groups fg
                LEFT JOIN users u ON fg.created_by = u.id
                WHERE fg.id = ? AND fg.is_active = 1
            ''', ('test_id',))
            print("✅ Query works correctly now!")
        except Exception as e:
            print(f"❌ Query still fails: {e}")
            
            # If it still fails, let's recreate the table
            print("\n🔄 Recreating family_groups table...")
            
            # Backup existing data
            cursor.execute("SELECT * FROM family_groups")
            existing_data = cursor.fetchall()
            
            # Drop and recreate table
            cursor.execute("DROP TABLE IF EXISTS family_groups_backup")
            cursor.execute("CREATE TABLE family_groups_backup AS SELECT * FROM family_groups")
            cursor.execute("DROP TABLE family_groups")
            
            # Create new table with correct schema
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
            
            # Restore data if any existed
            if existing_data:
                print(f"📦 Restoring {len(existing_data)} existing records...")
                for row in existing_data:
                    # Handle different column counts
                    if len(row) >= 6:  # Minimum required columns
                        cursor.execute('''
                            INSERT INTO family_groups 
                            (id, name, description, created_by, created_at, members, group_settings, is_active, group_avatar)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            row[0],  # id
                            row[1],  # name
                            row[2] if len(row) > 2 else None,  # description
                            row[3] if len(row) > 3 else row[2],  # created_by
                            row[4] if len(row) > 4 else datetime.now().isoformat(),  # created_at
                            row[5] if len(row) > 5 else '[]',  # members
                            row[6] if len(row) > 6 else '{}',  # group_settings
                            row[7] if len(row) > 7 else 1,  # is_active
                            row[8] if len(row) > 8 else None,  # group_avatar
                        ))
                print("✅ Data restored successfully")
            
            print("✅ Table recreated successfully")
        
        # Commit changes
        conn.commit()
        
        # Final verification
        print("\n🔍 Final verification...")
        cursor.execute("PRAGMA table_info(family_groups)")
        columns = cursor.fetchall()
        
        required_columns = ['id', 'name', 'description', 'created_by', 'created_at', 'members', 'group_settings', 'is_active', 'group_avatar']
        existing_columns = [col[1] for col in columns]
        
        all_good = True
        for req_col in required_columns:
            if req_col in existing_columns:
                print(f"✅ {req_col} column exists")
            else:
                print(f"❌ {req_col} column missing")
                all_good = False
        
        if all_good:
            print("\n🎉 Database schema is now correct!")
            return True
        else:
            print("\n❌ Some columns are still missing")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def test_family_groups_query():
    """Test the specific query that was failing"""
    print("\n🧪 Testing Family Groups Query")
    print("=" * 30)
    
    db_path = "backend/keliva.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Test the exact query from the error
        cursor.execute('''
            SELECT fg.id, fg.name, fg.description, fg.created_by, fg.created_at, 
                   fg.members, fg.group_settings, fg.is_active, fg.group_avatar, 
                   u.full_name as creator_name
            FROM family_groups fg
            LEFT JOIN users u ON fg.created_by = u.id
            WHERE fg.id = ? AND fg.is_active = 1
        ''', ('family_ei-SidKRuH8ranwM',))
        
        result = cursor.fetchone()
        if result:
            print("✅ Query executed successfully!")
            print(f"   Found group: {result[1]}")
        else:
            print("✅ Query executed successfully (no results found)")
        
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Database Schema Fix Tool")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Fix the database schema
    success = check_and_fix_database()
    
    if success:
        # Test the specific query
        test_success = test_family_groups_query()
        
        if test_success:
            print("\n" + "=" * 50)
            print("🎉 Database fix completed successfully!")
            print("\n📋 What was fixed:")
            print("✅ family_groups table schema corrected")
            print("✅ All required columns present")
            print("✅ Problematic query now works")
            print("\n🚀 You can now restart the backend and try again!")
            print("   python start_backend.py")
        else:
            print("\n❌ Query test failed - there may be other issues")
    else:
        print("\n❌ Database fix failed - please check the error messages above")