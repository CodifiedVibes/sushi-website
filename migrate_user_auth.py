#!/usr/bin/env python3
"""
Migration script to add authentication columns to users table
and created_by column to event_menus table
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Create database connection"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect('sushi.db')
        conn.row_factory = sqlite3.Row
    
    return conn

def migrate_database():
    """Add authentication columns and event ownership"""
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgres')
    
    try:
        if is_postgres:
            cursor = conn.cursor()
            
            # Add columns to users table
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE")
                print("✅ Added email_verified to users")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("⚠️  email_verified column already exists")
                else:
                    raise
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN verification_token VARCHAR(255)")
                print("✅ Added verification_token to users")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("⚠️  verification_token column already exists")
                else:
                    raise
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN verification_token_expires TIMESTAMP")
                print("✅ Added verification_token_expires to users")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("⚠️  verification_token_expires column already exists")
                else:
                    raise
            
            # Add created_by to event_menus
            try:
                cursor.execute("ALTER TABLE event_menus ADD COLUMN created_by INTEGER REFERENCES users(id)")
                print("✅ Added created_by to event_menus")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("⚠️  created_by column already exists")
                else:
                    raise
            
            conn.commit()
            
        else:
            # SQLite
            cursor = conn.cursor()
            
            # Add columns to users table
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0")
                print("✅ Added email_verified to users")
            except Exception as e:
                if 'duplicate' in str(e).lower():
                    print("⚠️  email_verified column already exists")
                else:
                    raise
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN verification_token TEXT")
                print("✅ Added verification_token to users")
            except Exception as e:
                if 'duplicate' in str(e).lower():
                    print("⚠️  verification_token column already exists")
                else:
                    raise
            
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN verification_token_expires TIMESTAMP")
                print("✅ Added verification_token_expires to users")
            except Exception as e:
                if 'duplicate' in str(e).lower():
                    print("⚠️  verification_token_expires column already exists")
                else:
                    raise
            
            # Add created_by to event_menus
            try:
                cursor.execute("ALTER TABLE event_menus ADD COLUMN created_by INTEGER REFERENCES users(id)")
                print("✅ Added created_by to event_menus")
            except Exception as e:
                if 'duplicate' in str(e).lower():
                    print("⚠️  created_by column already exists")
                else:
                    raise
            
            conn.commit()
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)

