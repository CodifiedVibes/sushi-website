#!/usr/bin/env python3
"""
Test script to verify database connection and check what's in the database
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def test_database_connection():
    """Test the database connection and show what's in the database"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("You need to add DATABASE_URL=${{ Postgres.DATABASE_URL }} to your Railway service variables.")
        return False
    
    print(f"🔗 Testing connection to: {database_url.split('@')[-1] if '@' in database_url else 'database'}")
    
    try:
        # Test connection
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        print("✅ Successfully connected to PostgreSQL database!")
        
        # Check what tables exist
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            if tables:
                print(f"\n📋 Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table['table_name']}")
                    
                    # Count rows in each table
                    try:
                        cursor.execute(f"SELECT COUNT(*) as count FROM {table['table_name']}")
                        count = cursor.fetchone()['count']
                        print(f"    └─ {count} rows")
                    except Exception as e:
                        print(f"    └─ Error counting rows: {e}")
            else:
                print("\n⚠️  No tables found in the database!")
                print("The database needs to be initialized with schema and data.")
                
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == '__main__':
    test_database_connection()
