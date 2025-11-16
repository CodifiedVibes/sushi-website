#!/usr/bin/env python3
"""
Migrate data from local SQLite database to PostgreSQL on Railway
This script reads from sushi.db and loads into PostgreSQL
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def get_sqlite_connection():
    """Connect to local SQLite database"""
    return sqlite3.connect('sushi.db')

def get_postgres_connection():
    """Connect to PostgreSQL database"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return None
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"ERROR: Failed to connect to PostgreSQL: {e}")
        return None

def clear_all_data(postgres_conn):
    """Clear all data in correct order (respecting foreign keys)"""
    print("\n🗑️  Clearing existing data...")
    postgres_cursor = postgres_conn.cursor()
    
    # Delete in order: relationships first, then items, then base tables
    postgres_cursor.execute("DELETE FROM menu_item_ingredients")
    postgres_cursor.execute("DELETE FROM menu_items")
    postgres_cursor.execute("DELETE FROM ingredients")
    postgres_cursor.execute("DELETE FROM categories")
    postgres_cursor.execute("DELETE FROM runbook_items")
    
    postgres_conn.commit()
    print("✅ Cleared existing data")

def migrate_categories(sqlite_conn, postgres_conn):
    """Migrate categories"""
    print("\n📋 Migrating categories...")
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    sqlite_cursor.execute("SELECT id, name, color, sort_order FROM categories ORDER BY id")
    categories = sqlite_cursor.fetchall()
    
    for cat in categories:
        postgres_cursor.execute("""
            INSERT INTO categories (id, name, color, sort_order)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                color = EXCLUDED.color,
                sort_order = EXCLUDED.sort_order
        """, (cat[0], cat[1], cat[2], cat[3]))
    
    postgres_conn.commit()
    print(f"✅ Migrated {len(categories)} categories")

def migrate_ingredients(sqlite_conn, postgres_conn):
    """Migrate ingredients"""
    print("\n📋 Migrating ingredients...")
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    sqlite_cursor.execute("""
        SELECT id, name, category, store, cost, quantity, unit_cost, brand, 
               shopping_cart_name, uses_per_purchase
        FROM ingredients ORDER BY id
    """)
    ingredients = sqlite_cursor.fetchall()
    
    for ing in ingredients:
        postgres_cursor.execute("""
            INSERT INTO ingredients (id, name, category, store, cost, quantity, unit_cost, brand, 
                                   shopping_cart_name, uses_per_purchase)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                category = EXCLUDED.category,
                store = EXCLUDED.store,
                cost = EXCLUDED.cost,
                quantity = EXCLUDED.quantity,
                unit_cost = EXCLUDED.unit_cost,
                brand = EXCLUDED.brand,
                shopping_cart_name = EXCLUDED.shopping_cart_name,
                uses_per_purchase = EXCLUDED.uses_per_purchase
        """, (ing[0], ing[1], ing[2], ing[3], ing[4], ing[5], ing[6], ing[7], ing[8], ing[9]))
    
    postgres_conn.commit()
    print(f"✅ Migrated {len(ingredients)} ingredients")

def migrate_menu_items(sqlite_conn, postgres_conn):
    """Migrate menu items"""
    print("\n📋 Migrating menu items...")
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    sqlite_cursor.execute("""
        SELECT id, name, category_id, description, price, image_path, is_active, sort_order
        FROM menu_items ORDER BY id
    """)
    menu_items = sqlite_cursor.fetchall()
    
    for item in menu_items:
        # Convert SQLite boolean (0/1) to PostgreSQL boolean
        is_active = bool(item[6]) if item[6] is not None else True
        
        postgres_cursor.execute("""
            INSERT INTO menu_items (id, name, category_id, description, price, image_path, is_active, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                category_id = EXCLUDED.category_id,
                description = EXCLUDED.description,
                price = EXCLUDED.price,
                image_path = EXCLUDED.image_path,
                is_active = EXCLUDED.is_active,
                sort_order = EXCLUDED.sort_order
        """, (item[0], item[1], item[2], item[3], item[4], item[5], is_active, item[7]))
    
    postgres_conn.commit()
    print(f"✅ Migrated {len(menu_items)} menu items")

def migrate_menu_item_ingredients(sqlite_conn, postgres_conn):
    """Migrate menu item ingredient relationships"""
    print("\n📋 Migrating menu item ingredients...")
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    sqlite_cursor.execute("""
        SELECT menu_item_id, ingredient_id, quantity, position, sort_order
        FROM menu_item_ingredients ORDER BY menu_item_id, sort_order
    """)
    relationships = sqlite_cursor.fetchall()
    
    for rel in relationships:
        postgres_cursor.execute("""
            INSERT INTO menu_item_ingredients (menu_item_id, ingredient_id, quantity, position, sort_order)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (menu_item_id, ingredient_id, position) DO UPDATE SET
                quantity = EXCLUDED.quantity,
                sort_order = EXCLUDED.sort_order
        """, (rel[0], rel[1], rel[2], rel[3], rel[4]))
    
    postgres_conn.commit()
    print(f"✅ Migrated {len(relationships)} ingredient relationships")

def migrate_runbook_items(sqlite_conn, postgres_conn):
    """Migrate runbook items"""
    print("\n📋 Migrating runbook items...")
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    sqlite_cursor.execute("""
        SELECT id, timeline, activity, beginner_steps, advanced_steps, estimated_duration, 
               notes, has_beginner, has_advanced, sort_order
        FROM runbook_items ORDER BY id
    """)
    runbook_items = sqlite_cursor.fetchall()
    
    for item in runbook_items:
        # Convert SQLite boolean (0/1) to PostgreSQL boolean
        has_beginner = bool(item[7]) if item[7] is not None else False
        has_advanced = bool(item[8]) if item[8] is not None else False
        
        postgres_cursor.execute("""
            INSERT INTO runbook_items (id, timeline, activity, beginner_steps, advanced_steps, 
                                      estimated_duration, notes, has_beginner, has_advanced, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                timeline = EXCLUDED.timeline,
                activity = EXCLUDED.activity,
                beginner_steps = EXCLUDED.beginner_steps,
                advanced_steps = EXCLUDED.advanced_steps,
                estimated_duration = EXCLUDED.estimated_duration,
                notes = EXCLUDED.notes,
                has_beginner = EXCLUDED.has_beginner,
                has_advanced = EXCLUDED.has_advanced,
                sort_order = EXCLUDED.sort_order
        """, (item[0], item[1], item[2], item[3], item[4], item[5], item[6], 
              has_beginner, has_advanced, item[9]))
    
    postgres_conn.commit()
    print(f"✅ Migrated {len(runbook_items)} runbook items")

def main():
    """Main migration function"""
    print("🚀 Starting migration from SQLite to PostgreSQL...")
    
    # Check if SQLite database exists
    if not os.path.exists('sushi.db'):
        print("❌ SQLite database (sushi.db) not found!")
        return
    
    sqlite_conn = get_sqlite_connection()
    postgres_conn = get_postgres_connection()
    
    if not postgres_conn:
        print("❌ Cannot connect to PostgreSQL. Exiting.")
        sqlite_conn.close()
        return
    
    try:
        # Clear all data first
        clear_all_data(postgres_conn)
        
        # Migrate in order (respecting foreign keys)
        migrate_categories(sqlite_conn, postgres_conn)
        migrate_ingredients(sqlite_conn, postgres_conn)
        migrate_menu_items(sqlite_conn, postgres_conn)
        migrate_menu_item_ingredients(sqlite_conn, postgres_conn)
        migrate_runbook_items(sqlite_conn, postgres_conn)
        
        # Reset sequences to match max IDs
        print("\n🔄 Resetting PostgreSQL sequences...")
        postgres_cursor = postgres_conn.cursor()
        postgres_cursor.execute("SELECT setval('categories_id_seq', (SELECT MAX(id) FROM categories))")
        postgres_cursor.execute("SELECT setval('ingredients_id_seq', (SELECT MAX(id) FROM ingredients))")
        postgres_cursor.execute("SELECT setval('menu_items_id_seq', (SELECT MAX(id) FROM menu_items))")
        postgres_cursor.execute("SELECT setval('runbook_items_id_seq', (SELECT MAX(id) FROM runbook_items))")
        postgres_conn.commit()
        print("✅ Sequences reset")
        
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        postgres_conn.rollback()
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    main()

