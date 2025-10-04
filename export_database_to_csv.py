#!/usr/bin/env python3
"""
Export SQLite database data to CSV files for editing
This script extracts data from sushi.db into separate CSV files:
- menu_exports.csv
- ingredients_exports.csv  
- runbook_exports.csv
"""

import sqlite3
import csv
import os
from pathlib import Path

def export_menu_to_csv(db_path, output_file):
    """Export menu data from database to CSV format"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get menu items with their ingredients
    query = """
    SELECT 
        mi.id,
        c.name as category,
        mi.name,
        mi.description,
        mi.price,
        mi.image_path,
        GROUP_CONCAT(CASE WHEN mii.position = 'inside' THEN i.name END, ';') as ingredients_inside,
        GROUP_CONCAT(CASE WHEN mii.position = 'on_top' THEN i.name END, ';') as ingredients_on_top
    FROM menu_items mi
    LEFT JOIN categories c ON mi.category_id = c.id
    LEFT JOIN menu_item_ingredients mii ON mi.id = mii.menu_item_id
    LEFT JOIN ingredients i ON mii.ingredient_id = i.id
    GROUP BY mi.id
    ORDER BY c.sort_order, mi.name
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Write to CSV
    if rows:
        fieldnames = ['category', 'name', 'ingredients_inside', 'ingredients_on_top', 'description', 'price', 'image_path']
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    'category': row['category'],
                    'name': row['name'],
                    'ingredients_inside': row['ingredients_inside'] or '',
                    'ingredients_on_top': row['ingredients_on_top'] or '',
                    'description': row['description'] or '',
                    'price': row['price'] or 0,
                    'image_path': row['image_path'] or ''
                })
        print(f"✅ Exported {len(rows)} menu items to {output_file}")
    
    conn.close()

def export_ingredients_to_csv(db_path, output_file):
    """Export ingredients data from database to CSV format"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT 
        i.name,
        i.category,
        i.store,
        i.cost,
        i.quantity,
        i.uses_per_purchase,
        i.unit_cost
    FROM ingredients i
    ORDER BY i.category, i.name
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Write to CSV
    if rows:
        fieldnames = ['category', 'name', 'store', 'cost', 'quantity', 'uses_per_purchase', 'unit_cost']
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    'category': row['category'],
                    'name': row['name'],
                    'store': row['store'] or '',
                    'cost': row['cost'] or '',
                    'quantity': row['quantity'] or '',
                    'uses_per_purchase': row['uses_per_purchase'] or '',
                    'unit_cost': row['unit_cost'] or ''
                })
        print(f"✅ Exported {len(rows)} ingredients to {output_file}")
    
    conn.close()

def export_runbook_to_csv(db_path, output_file):
    """Export runbook data from database to CSV format"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT 
        timeline,
        activity,
        beginner_steps,
        advanced_steps,
        estimated_duration,
        notes,
        has_beginner,
        has_advanced,
        sort_order
    FROM runbook_items
    ORDER BY sort_order, timeline
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Write to CSV
    if rows:
        fieldnames = ['timeline', 'activity', 'beginner_steps', 'advanced_steps', 'estimated_duration', 'notes', 'has_beginner', 'has_advanced', 'sort_order']
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    'timeline': row['timeline'],
                    'activity': row['activity'],
                    'beginner_steps': row['beginner_steps'] or '',
                    'advanced_steps': row['advanced_steps'] or '',
                    'estimated_duration': row['estimated_duration'] or '',
                    'notes': row['notes'] or '',
                    'has_beginner': row['has_beginner'],
                    'has_advanced': row['has_advanced'],
                    'sort_order': row['sort_order']
                })
        print(f"✅ Exported {len(rows)} runbook items to {output_file}")
    
    conn.close()

def main():
    """Main function to export database to CSV files"""
    # Setup paths
    script_dir = Path(__file__).parent
    db_file = script_dir / 'sushi.db'
    import_export_dir = script_dir / 'import-export'
    
    # Ensure import-export directory exists
    import_export_dir.mkdir(exist_ok=True)
    
    # Check if database exists
    if not db_file.exists():
        print(f"❌ Database file not found: {db_file}")
        return
    
    print("🔄 Exporting database to CSV files...")
    
    # Export each data type
    export_menu_to_csv(db_file, import_export_dir / 'menu_exports.csv')
    export_ingredients_to_csv(db_file, import_export_dir / 'ingredients_exports.csv')
    export_runbook_to_csv(db_file, import_export_dir / 'runbook_exports.csv')
    
    print("\n✅ Export complete! Files created in import-export/ directory:")
    print("   - menu_exports.csv")
    print("   - ingredients_exports.csv")
    print("   - runbook_exports.csv")
    print("\n📝 Next steps:")
    print("   1. Rename *_exports.csv to *_imports.csv")
    print("   2. Edit the CSV files in Excel/Google Sheets")
    print("   3. Run convert_imports_to_database.py to import changes")

if __name__ == "__main__":
    main() 