#!/usr/bin/env python3
"""
Export JSON data back to CSV files for editing
This script extracts the sushi_data.json file into separate CSV files:
- menu_exports.csv
- ingredients_exports.csv  
- runbook_exports.csv
"""

import json
import csv
import os
from pathlib import Path

def export_menu_to_csv(menu_data, output_file):
    """Export menu data to CSV format"""
    rows = []
    
    # Flatten the menu data by category
    for category, items in menu_data.items():
        for item in items:
            # Join ingredients arrays with semicolons
            inside_ingredients = ';'.join(item.get('ingredients_inside', []))
            on_top_ingredients = ';'.join(item.get('ingredients_on_top', []))
            
            row = {
                'category': item.get('category', ''),
                'name': item.get('name', ''),
                'ingredients_inside': inside_ingredients,
                'ingredients_on_top': on_top_ingredients,
                'description': item.get('description', '')
            }
            rows.append(row)
    
    # Write to CSV
    if rows:
        fieldnames = ['category', 'name', 'ingredients_inside', 'ingredients_on_top', 'description']
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ Exported {len(rows)} menu items to {output_file}")

def export_ingredients_to_csv(ingredients_data, output_file):
    """Export ingredients data to CSV format"""
    rows = []
    
    # Flatten the ingredients data by category
    for category, items in ingredients_data.items():
        for item in items:
            row = {
                'category': item.get('category', ''),
                'name': item.get('name', ''),
                'store': item.get('store', ''),
                'cost': item.get('cost', ''),
                'quantity': item.get('quantity', ''),
                'uses_per_purchase': item.get('uses_per_purchase', ''),
                'unit_cost': item.get('unit_cost', '')
            }
            rows.append(row)
    
    # Write to CSV
    if rows:
        fieldnames = ['category', 'name', 'store', 'cost', 'quantity', 'uses_per_purchase', 'unit_cost']
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ Exported {len(rows)} ingredients to {output_file}")

def export_runbook_to_csv(runbook_data, output_file):
    """Export runbook data to CSV format"""
    rows = []
    
    for item in runbook_data:
        row = {
            'timeline': item.get('timeline', ''),
            'activity': item.get('activity', ''),
            'beginner_steps': item.get('beginner_steps', ''),
            'advanced_steps': item.get('advanced_steps', ''),
            'hover_text': item.get('hover_text', ''),
            'completed': item.get('completed', False)
        }
        rows.append(row)
    
    # Write to CSV
    if rows:
        fieldnames = ['timeline', 'activity', 'beginner_steps', 'advanced_steps', 'hover_text', 'completed']
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ Exported {len(rows)} runbook items to {output_file}")

def main():
    """Main function to export JSON to CSV files"""
    # Setup paths
    script_dir = Path(__file__).parent
    data_dir = script_dir / 'data'
    json_file = data_dir / 'sushi_data.json'
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    # Check if JSON file exists
    if not json_file.exists():
        print(f"❌ Error: {json_file} not found!")
        return
    
    try:
        # Load JSON data
        print(f"📖 Loading data from {json_file}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Export each table to CSV
        print("\n🔄 Exporting data to CSV files...")
        
        # Export menu
        if 'menu' in data:
            menu_file = data_dir / 'menu_exports.csv'
            export_menu_to_csv(data['menu'], menu_file)
        else:
            print("❌ No menu data found in JSON")
        
        # Export ingredients
        if 'ingredients' in data:
            ingredients_file = data_dir / 'ingredients_exports.csv'
            export_ingredients_to_csv(data['ingredients'], ingredients_file)
        else:
            print("❌ No ingredients data found in JSON")
        
        # Export runbook
        if 'runbook' in data:
            runbook_file = data_dir / 'runbook_exports.csv'
            export_runbook_to_csv(data['runbook'], runbook_file)
        else:
            print("❌ No runbook data found in JSON")
        
        print(f"\n✅ Export complete! Files saved to {data_dir}/")
        print("\n📝 Next steps:")
        print("1. Rename the exported files to have '_imports' suffix:")
        print("   - menu_exports.csv → menu_imports.csv")
        print("   - ingredients_exports.csv → ingredients_imports.csv")
        print("   - runbook_exports.csv → runbook_imports.csv")
        print("2. Edit the '_imports' CSV files as needed")
        print("3. Run convert_imports_to_json.py to re-import the data")
        print("4. Refresh your website to see changes")
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 