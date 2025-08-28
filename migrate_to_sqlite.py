#!/usr/bin/env python3
"""
Migration script to convert JSON data to SQLite database
Converts sushi_data.json to a proper relational database
"""

import json
import sqlite3
import os
from datetime import datetime

def create_database():
    """Create the SQLite database and tables"""
    # Remove existing database if it exists
    if os.path.exists('sushi.db'):
        os.remove('sushi.db')
    
    # Create new database
    conn = sqlite3.connect('sushi.db')
    cursor = conn.cursor()
    
    # Read and execute schema
    with open('database_schema.sql', 'r') as f:
        schema = f.read()
        cursor.executescript(schema)
    
    conn.commit()
    return conn, cursor

def migrate_ingredients(cursor, ingredients_data):
    """Migrate ingredients from JSON to SQLite"""
    print("Migrating ingredients...")
    
    for category, items in ingredients_data.items():
        for item in items:
            cursor.execute("""
                INSERT INTO ingredients (
                    name, category, store, cost, quantity, unit_cost, brand, 
                    shopping_cart_name, uses_per_purchase
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get('name', ''),
                item.get('category', category),
                item.get('store', ''),
                item.get('cost', 0.0),
                item.get('quantity', ''),
                item.get('unit_cost', 0.0),
                item.get('brand', ''),
                item.get('shopping_cart_name', ''),
                item.get('uses_per_purchase', 1)
            ))
    
    print(f"Migrated {sum(len(items) for items in ingredients_data.values())} ingredients")

def migrate_menu_items(cursor, menu_data):
    """Migrate menu items from JSON to SQLite"""
    print("Migrating menu items...")
    
    # Get category IDs
    cursor.execute("SELECT id, name FROM categories")
    category_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Create ingredient name to ID mapping
    cursor.execute("SELECT id, name FROM ingredients")
    ingredient_map = {row[1].lower(): row[0] for row in cursor.fetchall()}
    
    menu_count = 0
    for category_name, items in menu_data.items():
        category_id = category_map.get(category_name)
        if not category_id:
            print(f"Warning: Category '{category_name}' not found in categories table")
            continue
            
        for item in items:
            # Insert menu item
            cursor.execute("""
                INSERT INTO menu_items (
                    name, category_id, description, price, image_path
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                item.get('name', ''),
                category_id,
                item.get('description', ''),
                item.get('price', 0.0),
                item.get('image_path', '')
            ))
            
            menu_item_id = cursor.lastrowid
            menu_count += 1
            
            # Handle ingredients_inside
            ingredients_inside = item.get('ingredients_inside', [])
            for i, ing_name in enumerate(ingredients_inside):
                ing_id = ingredient_map.get(ing_name.lower())
                if ing_id:
                    cursor.execute("""
                        INSERT INTO menu_item_ingredients (
                            menu_item_id, ingredient_id, quantity, position, sort_order
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (menu_item_id, ing_id, 1.0, 'inside', i))
                else:
                    print(f"Warning: Ingredient '{ing_name}' not found for menu item '{item.get('name')}'")
            
            # Handle ingredients_on_top
            ingredients_on_top = item.get('ingredients_on_top', [])
            for i, ing_name in enumerate(ingredients_on_top):
                ing_id = ingredient_map.get(ing_name.lower())
                if ing_id:
                    cursor.execute("""
                        INSERT INTO menu_item_ingredients (
                            menu_item_id, ingredient_id, quantity, position, sort_order
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (menu_item_id, ing_id, 1.0, 'on_top', i))
                else:
                    print(f"Warning: Ingredient '{ing_name}' not found for menu item '{item.get('name')}'")
    
    print(f"Migrated {menu_count} menu items")

def migrate_runbook(cursor, runbook_data):
    """Migrate runbook items from JSON to SQLite"""
    print("Migrating runbook items...")
    
    for item in runbook_data:
        cursor.execute("""
            INSERT INTO runbook_items (
                timeline, activity, beginner_steps, advanced_steps, 
                estimated_duration, notes, has_beginner, has_advanced
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get('timeline', ''),
            item.get('activity', ''),
            item.get('beginner_steps', ''),
            item.get('advanced_steps', ''),
            item.get('estimated_duration', ''),
            item.get('notes', ''),
            bool(item.get('has_beginner', False)),
            bool(item.get('has_advanced', False))
        ))
    
    print(f"Migrated {len(runbook_data)} runbook items")

def main():
    """Main migration function"""
    print("Starting migration from JSON to SQLite...")
    
    # Load JSON data
    try:
        with open('data/sushi_data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: data/sushi_data.json not found!")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in sushi_data.json: {e}")
        return
    
    # Create database
    conn, cursor = create_database()
    
    try:
        # Migrate data
        migrate_ingredients(cursor, data.get('ingredients', {}))
        migrate_menu_items(cursor, data.get('menu', {}))
        migrate_runbook(cursor, data.get('runbook', []))
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print(f"Database created: sushi.db")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM menu_items")
        menu_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        ingredient_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM runbook_items")
        runbook_count = cursor.fetchone()[0]
        
        print(f"\nSummary:")
        print(f"- Menu items: {menu_count}")
        print(f"- Ingredients: {ingredient_count}")
        print(f"- Runbook items: {runbook_count}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 