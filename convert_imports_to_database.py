#!/usr/bin/env python3
"""
Import CSV data directly into SQLite database
This script reads CSV files from import-export/ and updates the database:
- menu_imports.csv -> menu_items table
- ingredients_imports.csv -> ingredients table  
- runbook_imports.csv -> runbook_items table
"""

import sqlite3
import csv
import os
import sys
import argparse
from pathlib import Path

def get_or_create_category(cursor, category_name):
    """Get category ID or create if it doesn't exist"""
    cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        # Create new category with default color and sort order
        cursor.execute(
            "INSERT INTO categories (name, color, sort_order) VALUES (?, ?, ?)",
            (category_name, "#CCCCCC", 999)
        )
        return cursor.lastrowid

def get_or_create_ingredient(cursor, ingredient_name):
    """Get ingredient ID or create if it doesn't exist"""
    cursor.execute("SELECT id FROM ingredients WHERE name = ?", (ingredient_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        # Create new ingredient with default values
        cursor.execute(
            "INSERT INTO ingredients (name, category, store, cost, quantity, uses_per_purchase, unit_cost) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ingredient_name, "Other", "", 0, 1, 1, 0)
        )
        return cursor.lastrowid

def import_menu_from_csv(db_path, csv_file):
    """Import menu data from CSV to database"""
    if not csv_file.exists():
        print(f"⚠️  Menu CSV file not found: {csv_file}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing menu items (but keep categories)
        cursor.execute("DELETE FROM menu_item_ingredients")
        cursor.execute("DELETE FROM menu_items")
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            menu_items_imported = 0
            
            for row in reader:
                category_name = row.get('category', '').strip()
                if not category_name:
                    continue
                
                # Get or create category
                category_id = get_or_create_category(cursor, category_name)
                
                # Insert menu item
                cursor.execute("""
                    INSERT INTO menu_items (category_id, name, description, price, image_path)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    category_id,
                    row.get('name', '').strip(),
                    row.get('description', '').strip(),
                    float(row.get('price', 0)) if row.get('price') else 0,
                    row.get('image_path', '').strip()
                ))
                
                menu_item_id = cursor.lastrowid
                
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
                                VALUES (?, ?, ?)
                            """, (menu_item_id, ingredient_id, 'inside'))
                
                # Process on-top ingredients
                if on_top_ingredients:
                    for ingredient_name in on_top_ingredients.split(';'):
                        ingredient_name = ingredient_name.strip()
                        if ingredient_name:
                            ingredient_id = get_or_create_ingredient(cursor, ingredient_name)
                            cursor.execute("""
                                INSERT INTO menu_item_ingredients (menu_item_id, ingredient_id, position)
                                VALUES (?, ?, ?)
                            """, (menu_item_id, ingredient_id, 'on_top'))
                
                menu_items_imported += 1
        
        conn.commit()
        print(f"✅ Imported {menu_items_imported} menu items from {csv_file}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing menu: {e}")
    finally:
        conn.close()

def import_ingredients_from_csv(db_path, csv_file):
    """Import ingredients data from CSV to database"""
    if not csv_file.exists():
        print(f"⚠️  Ingredients CSV file not found: {csv_file}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing ingredients
        cursor.execute("DELETE FROM ingredients")
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            ingredients_imported = 0
            
            for row in reader:
                cursor.execute("""
                    INSERT INTO ingredients (name, category, store, cost, quantity, uses_per_purchase, unit_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('name', '').strip(),
                    row.get('category', '').strip(),
                    row.get('store', '').strip(),
                    row.get('cost', '').strip(),
                    row.get('quantity', '').strip(),
                    row.get('uses_per_purchase', '').strip(),
                    row.get('unit_cost', '').strip()
                ))
                ingredients_imported += 1
        
        conn.commit()
        print(f"✅ Imported {ingredients_imported} ingredients from {csv_file}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing ingredients: {e}")
    finally:
        conn.close()

def import_runbook_from_csv(db_path, csv_file):
    """Import runbook data from CSV to database"""
    if not csv_file.exists():
        print(f"⚠️  Runbook CSV file not found: {csv_file}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing runbook items
        cursor.execute("DELETE FROM runbook_items")
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            runbook_items_imported = 0
            
            for row in reader:
                # Convert "x" values to boolean for has_beginner and has_advanced
                has_beginner = row.get('has_beginner', '').strip() == '1'
                has_advanced = row.get('has_advanced', '').strip() == '1'
                
                # Get sort order, default to 0 if not provided
                sort_order = 0
                if 'sort_order' in row and row.get('sort_order', '').strip():
                    try:
                        sort_order = int(row.get('sort_order', '0').strip())
                    except ValueError:
                        sort_order = 0
                
                cursor.execute("""
                    INSERT INTO runbook_items (timeline, activity, beginner_steps, advanced_steps, estimated_duration, notes, has_beginner, has_advanced, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('timeline', '').strip(),
                    row.get('activity', '').strip(),
                    row.get('beginner_steps', '').strip(),
                    row.get('advanced_steps', '').strip(),
                    row.get('estimated_duration', '').strip(),
                    row.get('notes', '').strip(),
                    has_beginner,
                    has_advanced,
                    sort_order
                ))
                runbook_items_imported += 1
        
        conn.commit()
        print(f"✅ Imported {runbook_items_imported} runbook items from {csv_file}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing runbook: {e}")
    finally:
        conn.close()

def main():
    """Main function to import CSV files to database"""
    parser = argparse.ArgumentParser(description='Import CSV data to SQLite database')
    parser.add_argument('--menu', action='store_true', help='Import menu data only')
    parser.add_argument('--ingredients', action='store_true', help='Import ingredients data only')
    parser.add_argument('--runbook', action='store_true', help='Import runbook data only')
    
    args = parser.parse_args()
    
    # Setup paths
    script_dir = Path(__file__).parent
    db_file = script_dir / 'sushi.db'
    import_export_dir = script_dir / 'import-export'
    
    # Check if database exists
    if not db_file.exists():
        print(f"❌ Database file not found: {db_file}")
        return
    
    print("🔄 Importing CSV files to database...")
    
    # Determine what to import
    import_all = not (args.menu or args.ingredients or args.runbook)
    
    if import_all or args.ingredients:
        import_ingredients_from_csv(db_file, import_export_dir / 'ingredients_imports.csv')
    
    if import_all or args.menu:
        import_menu_from_csv(db_file, import_export_dir / 'menu_imports.csv')
    
    if import_all or args.runbook:
        import_runbook_from_csv(db_file, import_export_dir / 'runbook_imports.csv')
    
    print("\n✅ Import complete!")
    print("🔄 Restart the API server to see changes: python3 api_server.py")

if __name__ == "__main__":
    main() 