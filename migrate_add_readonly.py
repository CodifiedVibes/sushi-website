#!/usr/bin/env python3
"""
Migration script to add read_only column to event_menus table
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def migrate_database():
    """Add read_only column to event_menus table"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found. This script should be run on Railway.")
        return False
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Check if read_only column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'event_menus' AND column_name = 'read_only'
        """)
        
        if cursor.fetchone():
            print("✅ read_only column already exists")
            conn.close()
            return True
        
        # Add read_only column
        print("🔄 Adding read_only column to event_menus table...")
        cursor.execute("""
            ALTER TABLE event_menus 
            ADD COLUMN read_only BOOLEAN DEFAULT FALSE
        """)
        
        conn.commit()
        print("✅ Successfully added read_only column")
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'event_menus' AND column_name = 'read_only'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Column verified: {result['column_name']} ({result['data_type']}) with default {result['column_default']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Starting database migration...")
    success = migrate_database()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
