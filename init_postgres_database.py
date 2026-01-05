#!/usr/bin/env python3
"""
Initialize KeLiva PostgreSQL database
Run this script to set up the database schema for production
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.postgres_database import db_manager

async def main():
    """Initialize PostgreSQL database"""
    print("🚀 Initializing KeLiva PostgreSQL Database...")
    
    try:
        # Initialize database connection and schema
        await db_manager.init_pool()
        print("✅ PostgreSQL database initialized successfully!")
        
        # Test the connection
        async with db_manager.get_connection() as conn:
            result = await conn.fetchval("SELECT version()")
            print(f"📊 PostgreSQL Version: {result}")
            
            # Check tables
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            table_names = [table['table_name'] for table in tables]
            print(f"📋 Created tables: {table_names}")
            
        # Close connections
        await db_manager.close_pool()
        print("🎉 Database setup complete!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())