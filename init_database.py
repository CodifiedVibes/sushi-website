#!/usr/bin/env python3
"""
Database initialization script for Railway deployment
This script sets up the PostgreSQL database with schema and data
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

def get_db_connection():
    """Create database connection"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return None
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        return None

def run_sql_file(conn, filename):
    """Run SQL commands from a file"""
    try:
        with open(filename, 'r') as f:
            sql_content = f.read()
        
        cursor = conn.cursor()
        cursor.execute(sql_content)
        conn.commit()
        print(f"✅ Successfully executed {filename}")
        return True
    except Exception as e:
        print(f"❌ Error executing {filename}: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Starting database initialization...")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database. Exiting.")
        return
    
    try:
        # Check if tables already exist
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row['table_name'] for row in cursor.fetchall()]
        
        if existing_tables:
            print(f"📋 Database already has tables: {existing_tables}")
            print("🔄 Skipping schema creation")
        else:
            print("📋 No tables found, creating schema...")
            # Run schema creation
            if run_sql_file(conn, 'postgresql_schema.sql'):
                print("✅ Database schema created successfully")
            else:
                print("❌ Failed to create schema")
                return
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) as count FROM categories")
        category_count = cursor.fetchone()['count']
        
        if category_count > 0:
            print(f"📊 Database already has {category_count} categories")
            print("🔄 Skipping data import")
        else:
            print("📊 No data found, importing data...")
            # Import data
            if run_sql_file(conn, 'postgresql_data.sql'):
                print("✅ Database data imported successfully")
            else:
                print("❌ Failed to import data")
                return
        
        print("🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
