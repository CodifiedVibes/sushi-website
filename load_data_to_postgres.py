#!/usr/bin/env python3
"""
Load data from CSV files into PostgreSQL database on Railway
This script can be run once to populate the database.
"""

import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Create PostgreSQL database connection"""
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

def get_or_create_category(cursor, category_name, color_map):
    """Get category ID or create if it doesn't exist"""
    cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
    result = cursor.fetchone()
    if result:
        return result['id']
    else:
        # Create new category with default color and sort order
        color = color_map.get(category_name, "#CCCCCC")
        cursor.execute(
            "INSERT INTO categories (name, color, sort_order) VALUES (%s, %s, %s) RETURNING id",
            (category_name, color, 999)
        )
        return cursor.fetchone()['id']

def get_or_create_ingredient(cursor, ingredient_name):
    """Get ingredient ID or create if it doesn't exist"""
    cursor.execute("SELECT id FROM ingredients WHERE name = %s", (ingredient_name,))
    result = cursor.fetchone()
    if result:
        return result['id']
    else:
        # Create new ingredient with default values
        cursor.execute(
            "INSERT INTO ingredients (name, category, store, cost, quantity, uses_per_purchase, unit_cost) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (ingredient_name, "Other", "", 0, 1, 1, 0)
        )
        return cursor.fetchone()['id']

def import_menu_from_csv(conn, csv_file):
    """Import menu data from CSV to PostgreSQL"""
    if not os.path.exists(csv_file):
        print(f"⚠️  Menu CSV file not found: {csv_file}")
        return
    
    cursor = conn.cursor()
    
    try:
        # Clear existing menu items (but keep categories)
        cursor.execute("DELETE FROM menu_item_ingredients")
        cursor.execute("DELETE FROM menu_items")
        
        # Category color mapping
        color_map = {
            'Appetizer': '#FF69B4',
            'Nigiri': '#9945FF',
            'Maki Rolls': '#3B82F6',
            'Speciality Rolls': '#00D4AA'
        }
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            menu_items_imported = 0
            
            for row in reader:
                category_name = row.get('category', '').strip()
                if not category_name:
                    continue
                
                # Get or create category
                category_id = get_or_create_category(cursor, category_name, color_map)
                
                # Insert menu item (PostgreSQL uses true/false for booleans)
                cursor.execute("""
                    INSERT INTO menu_items (category_id, name, description, price, image_path, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    category_id,
                    row.get('name', '').strip(),
                    row.get('description', '').strip(),
                    float(row.get('price', 0)) if row.get('price') else 0,
                    row.get('image_path', '').strip(),
                    True  # is_active = true
                ))
                
                menu_item_id = cursor.fetchone()['id']
                
                # Handle ingredients
                inside_ingredients = row.get('ingredients_inside', '').strip()
                on_top_ingredients = row.get('ingredients_on_top', '').strip()
                
                # Process inside ingredients
                if inside_ingredients:
                    for ingredient_name in inside_ingredients.split(';'):
                        ingredient_name = ingredient_name.strip()
                        if ingredient_name:
                            ingredient_id = get_or_create_ingredient(cursor, ingredient_name)
                            cursor.execute("""
                                INSERT INTO menu_item_ingredients (menu_item_id, ingredient_id, position)
                                VALUES (%s, %s, %s)
                            """, (menu_item_id, ingredient_id, 'inside'))
                
                # Process on-top ingredients
                if on_top_ingredients:
                    for ingredient_name in on_top_ingredients.split(';'):
                        ingredient_name = ingredient_name.strip()
                        if ingredient_name:
                            ingredient_id = get_or_create_ingredient(cursor, ingredient_name)
                            cursor.execute("""
                                INSERT INTO menu_item_ingredients (menu_item_id, ingredient_id, position)
                                VALUES (%s, %s, %s)
                            """, (menu_item_id, ingredient_id, 'on_top'))
                
                menu_items_imported += 1
            
            conn.commit()
            print(f"✅ Imported {menu_items_imported} menu items")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing menu: {e}")
        raise

def import_ingredients_from_csv(conn, csv_file):
    """Import ingredients data from CSV to PostgreSQL"""
    if not os.path.exists(csv_file):
        print(f"⚠️  Ingredients CSV file not found: {csv_file}")
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM ingredients")
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            ingredients_imported = 0
            
            for row in reader:
                cursor.execute("""
                    INSERT INTO ingredients (name, category, store, cost, quantity, unit_cost, brand, shopping_cart_name, uses_per_purchase)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row.get('name', '').strip(),
                    row.get('category', '').strip(),
                    row.get('store', '').strip(),
                    float(row.get('cost', 0)) if row.get('cost') else 0,
                    row.get('quantity', '').strip(),
                    float(row.get('unit_cost', 0)) if row.get('unit_cost') else 0,
                    row.get('brand', '').strip(),
                    row.get('shopping_cart_name', '').strip(),
                    int(row.get('uses_per_purchase', 1)) if row.get('uses_per_purchase') else 1
                ))
                ingredients_imported += 1
            
            conn.commit()
            print(f"✅ Imported {ingredients_imported} ingredients")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing ingredients: {e}")
        raise

def import_runbook_from_csv(conn, csv_file):
    """Import runbook data from CSV to PostgreSQL"""
    if not os.path.exists(csv_file):
        print(f"⚠️  Runbook CSV file not found: {csv_file}")
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM runbook_items")
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            runbook_items_imported = 0
            
            for row in reader:
                has_beginner = bool(row.get('beginner_steps', '').strip())
                has_advanced = bool(row.get('advanced_steps', '').strip())
                
                cursor.execute("""
                    INSERT INTO runbook_items (timeline, activity, beginner_steps, advanced_steps, estimated_duration, notes, has_beginner, has_advanced, sort_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row.get('timeline', '').strip(),
                    row.get('activity', '').strip(),
                    row.get('beginner_steps', '').strip() or None,
                    row.get('advanced_steps', '').strip() or None,
                    row.get('estimated_duration', '').strip() or None,
                    row.get('notes', '').strip() or None,
                    has_beginner,
                    has_advanced,
                    int(row.get('sort_order', 0)) if row.get('sort_order') else 0
                ))
                runbook_items_imported += 1
            
            conn.commit()
            print(f"✅ Imported {runbook_items_imported} runbook items")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing runbook: {e}")
        raise

def main():
    """Main function to load all data"""
    print("🚀 Starting data import to PostgreSQL...")
    
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database. Exiting.")
        return
    
    try:
        # Import data from CSV files
        csv_dir = 'import-export'
        
        print("\n📋 Importing menu items...")
        import_menu_from_csv(conn, os.path.join(csv_dir, 'menu_imports.csv'))
        
        print("\n📋 Importing ingredients...")
        import_ingredients_from_csv(conn, os.path.join(csv_dir, 'ingredients_imports.csv'))
        
        print("\n📋 Importing runbook items...")
        import_runbook_from_csv(conn, os.path.join(csv_dir, 'runbook_imports.csv'))
        
        print("\n🎉 Data import completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()

