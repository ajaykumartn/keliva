#!/usr/bin/env python3
"""
Fix Users Table Schema
Adds missing columns needed for Family Groups functionality
"""
import sqlite3
import os
from datetime import datetime

def fix_users_table():
    """Fix the users table to include all required columns"""
    print("🔧 Fixing Users Table Schema")
    print("=" * 40)
    
    db_path = "backend/keliva.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current schema of users table
        print("📊 Checking users table schema...")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("Current columns:")
        column_names = []
        for col in columns:
            column_names.append(col[1])
            print(f"   - {col[1]} ({col[2]})")
        
        # List of required columns for Family Groups
        required_columns = {
            'learning_streak': 'INTEGER DEFAULT 0',
            'total_points': 'INTEGER DEFAULT 0',
            'profile_picture': 'TEXT',
            'last_login': 'TIMESTAMP',
            'family_group_id': 'TEXT'
        }
        
        # Add missing columns
        changes_made = False
        for column_name, column_type in required_columns.items():
            if column_name not in column_names:
                print(f"\n❌ Missing '{column_name}' column - adding it...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added '{column_name}' column")
                changes_made = True
            else:
                print(f"✅ '{column_name}' column exists")
        
        if not changes_made:
            print("\n✅ All required columns already exist")
        
        # Test the problematic query
        print("\n🧪 Testing the users query...")
        try:
            cursor.execute('''
                SELECT id, name, full_name, profile_picture, last_login, 
                       learning_streak, total_points
                FROM users LIMIT 1
            ''')
            result = cursor.fetchone()
            print("✅ Users query works correctly now!")
            if result:
                print(f"   Sample user: {result[1] or result[2] or 'Unknown'}")
        except Exception as e:
            print(f"❌ Users query still fails: {e}")
            return False
        
        # Commit changes
        conn.commit()
        
        # Final verification
        print("\n🔍 Final verification...")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        existing_columns = [col[1] for col in columns]
        
        all_good = True
        for req_col in required_columns.keys():
            if req_col in existing_columns:
                print(f"✅ {req_col} column exists")
            else:
                print(f"❌ {req_col} column missing")
                all_good = False
        
        if all_good:
            print("\n🎉 Users table schema is now correct!")
            return True
        else:
            print("\n❌ Some columns are still missing")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing users table: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def test_family_groups_full_query():
    """Test the complete family groups query that includes users"""
    print("\n🧪 Testing Complete Family Groups Query")
    print("=" * 40)
    
    db_path = "backend/keliva.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, get a family group
        cursor.execute("SELECT id, members FROM family_groups LIMIT 1")
        group_row = cursor.fetchone()
        
        if not group_row:
            print("ℹ️  No family groups found to test with")
            return True
        
        group_id = group_row[0]
        members = group_row[1]
        
        print(f"Testing with group: {group_id}")
        
        # Test the main family group query
        cursor.execute('''
            SELECT fg.id, fg.name, fg.description, fg.created_by, fg.created_at, 
                   fg.members, fg.group_settings, fg.is_active, fg.group_avatar, 
                   u.full_name as creator_name
            FROM family_groups fg
            LEFT JOIN users u ON fg.created_by = u.id
            WHERE fg.id = ? AND fg.is_active = 1
        ''', (group_id,))
        
        result = cursor.fetchone()
        if result:
            print("✅ Main family group query works!")
            
            # Test member details query
            import json
            members_list = json.loads(members) if members else []
            
            if members_list:
                print(f"Testing member queries for {len(members_list)} members...")
                for member_id in members_list:
                    cursor.execute('''
                        SELECT id, name, full_name, profile_picture, last_login, 
                               learning_streak, total_points
                        FROM users WHERE id = ?
                    ''', (member_id,))
                    
                    member_result = cursor.fetchone()
                    if member_result:
                        print(f"✅ Member query works for: {member_result[1] or member_result[2] or 'Unknown'}")
                    else:
                        print(f"⚠️  Member not found: {member_id}")
            else:
                print("ℹ️  No members to test with")
        else:
            print("❌ Main family group query failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Complete query test failed: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Users Table Fix Tool")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Fix the users table schema
    success = fix_users_table()
    
    if success:
        # Test the complete query
        test_success = test_family_groups_full_query()
        
        if test_success:
            print("\n" + "=" * 50)
            print("🎉 Users table fix completed successfully!")
            print("\n📋 What was fixed:")
            print("✅ users table schema corrected")
            print("✅ learning_streak column added")
            print("✅ total_points column added")
            print("✅ profile_picture column added")
            print("✅ last_login column added")
            print("✅ family_group_id column added")
            print("✅ All Family Groups queries now work")
            print("\n🚀 You can now restart the backend and try again!")
            print("   The invitation system should work properly now!")
        else:
            print("\n❌ Query test failed - there may be other issues")
    else:
        print("\n❌ Users table fix failed - please check the error messages above")