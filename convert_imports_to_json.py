#!/usr/bin/env python3
"""
Import CSV files with _imports suffix back to JSON format
This script reads the exported CSV files and converts them back to sushi_data.json:
- menu_imports.csv
- ingredients_imports.csv  
- runbook_imports.csv
"""

import pandas as pd
import json
import os
from pathlib import Path

def import_menu_from_csv(csv_file):
    """Import menu data from CSV format"""
    try:
        # Try different encodings
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_file, encoding='latin-1')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_file, encoding='cp1252')
        menu_data = {}
        
        for _, row in df.iterrows():
            category = str(row.get('category', '')).strip()
            name = str(row.get('name', '')).strip()
            
            if not category or not name:
                continue
            
            # Split ingredients back into arrays
            inside_ingredients = []
            if row.get('ingredients_inside'):
                inside_ingredients = [ing.strip() for ing in str(row['ingredients_inside']).split(';') if ing.strip() and ing.strip().lower() != 'nan']
            
            on_top_ingredients = []
            if row.get('ingredients_on_top'):
                on_top_ingredients = [ing.strip() for ing in str(row['ingredients_on_top']).split(';') if ing.strip() and ing.strip().lower() != 'nan']
            
            item = {
                'category': category,
                'name': name,
                'ingredients_inside': inside_ingredients,
                'ingredients_on_top': on_top_ingredients,
                'description': row.get('description', '')
            }
            
            if category not in menu_data:
                menu_data[category] = []
            menu_data[category].append(item)
        
        print(f"✅ Imported {sum(len(items) for items in menu_data.values())} menu items from {csv_file}")
        return menu_data
        
    except Exception as e:
        print(f"❌ Error importing menu from {csv_file}: {e}")
        return {}

def import_ingredients_from_csv(csv_file):
    """Import ingredients data from CSV format, supporting shopping cart fields and extra columns, and cleaning NaN/None values."""
    try:
        # Try different encodings
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_file, encoding='latin-1')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_file, encoding='cp1252')
        # Clean up column names
        df.columns = [str(col).strip() for col in df.columns]
        # Remove duplicate rows based on all columns
        df = df.drop_duplicates()
        # List of numeric fields
        numeric_fields = ['cost', 'unit_cost', 'uses_per_purchase']
        # List of string fields
        string_fields = ['brand', 'name', 'shopping_cart_name', 'store', 'quantity', 'category']
        # Clean up NaN/None/invalid values
        for col in numeric_fields:
            if col in df.columns:
                df[col] = pd.Series(pd.to_numeric(df[col], errors='coerce')).fillna(0)
                if col == 'uses_per_purchase':
                    df[col] = df[col].replace(0, 1)
        for col in string_fields:
            if col in df.columns:
                df[col] = pd.Series(df[col].astype(str)).replace(['nan', 'None', 'NaN'], '').fillna('')
        # Build output grouped by category
        ingredients = {}
        for _, row in df.iterrows():
            cat = row.get('category', '')
            if cat is None:
                cat = ''
            cat = str(cat).strip()
            if not cat:
                continue
            item = {}
            for col in df.columns:
                val = row.get(col, '')
                if pd.isna(val) or val in ['nan', 'NaN', 'None', None]:
                    if col in numeric_fields:
                        val = 0
                        if col == 'uses_per_purchase':
                            val = 1
                    else:
                        val = ''
                if col in numeric_fields:
                    try:
                        val = float(val)
                        if col == 'uses_per_purchase':
                            val = int(val)
                    except Exception:
                        val = 0
                        if col == 'uses_per_purchase':
                            val = 1
                else:
                    if val is None:
                        val = ''
                    val = str(val).strip()
                item[col] = val
            # Remove obviously broken entries (e.g., missing name or shopping_cart_name)
            if not item.get('name') and not item.get('shopping_cart_name'):
                continue
            if cat not in ingredients:
                ingredients[cat] = []
            # Avoid adding duplicates by comparing dicts only if ingredients[cat] is a list
            if isinstance(ingredients[cat], list):
                if not any(all(item.get(k) == existing.get(k) for k in item) for existing in ingredients[cat]):
                    ingredients[cat].append(item)
        return ingredients
    except Exception as e:
        print(f"❌ Error importing ingredients from {csv_file}: {e}")
        return {};

def import_runbook_from_csv(csv_file):
    """Import runbook data from CSV format"""
    try:
        # Try different encodings
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_file, encoding='latin-1')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_file, encoding='cp1252')
        runbook_data = []
        
        for _, row in df.iterrows():
            timeline = str(row.get('timeline', '')).strip()
            activity = str(row.get('activity', '')).strip()
            
            if not timeline or not activity:
                continue
            
            # Check if beginner or advanced steps exist (look for 'x' in flag columns)
            has_beginner = str(row.get('beginner_steps', '')).strip().lower() == 'x'
            has_advanced = str(row.get('advanced_steps', '')).strip().lower() == 'x'
            
            # Clean up NaN values
            def cleanValue(val):
                val_str = str(val).strip()
                return '' if val_str.lower() in ['nan', ''] else val_str
            
            item = {
                'timeline': timeline,
                'activity': activity,
                'beginner_steps': cleanValue(row.get('Beginner Steps', '')),
                'advanced_steps': cleanValue(row.get('Advanced Steps', '')),
                'estimated_duration': cleanValue(row.get('Estimated Duration', '')),
                'notes': cleanValue(row.get('Notes', '')),
                'has_beginner': has_beginner,
                'has_advanced': has_advanced,
                'completed': bool(row.get('completed', False))
            }
            runbook_data.append(item)
        
        print(f"✅ Imported {len(runbook_data)} runbook items from {csv_file}")
        return runbook_data
        
    except Exception as e:
        print(f"❌ Error importing runbook from {csv_file}: {e}")
        return []

def main():
    """Main function to import CSV files to JSON"""
    # Setup paths
    script_dir = Path(__file__).parent
    data_dir = script_dir / 'data'
    import_dir = script_dir / 'import-export'
    json_file = data_dir / 'sushi_data.json'
    
    # Check if data directory exists
    if not data_dir.exists():
        print(f"❌ Error: {data_dir} directory not found!")
        return
    # Check if import directory exists
    if not import_dir.exists():
        print(f"❌ Error: {import_dir} directory not found!")
        return
    # Check for import files
    menu_import_file = import_dir / 'menu_imports.csv'
    ingredients_import_file = import_dir / 'ingredients_imports.csv'
    runbook_import_file = import_dir / 'runbook_imports.csv'
    
    print("📖 Looking for import files...")
    
    # Import each table from CSV
    all_data = {}
    
    # Import menu
    if menu_import_file.exists():
        print(f"\n🔄 Importing menu from {menu_import_file}...")
        all_data['menu'] = import_menu_from_csv(menu_import_file)
    else:
        print(f"⚠️  {menu_import_file} not found - skipping menu import")
        all_data['menu'] = {}
    
    # Import ingredients
    if ingredients_import_file.exists():
        print(f"\n🔄 Importing ingredients from {ingredients_import_file}...")
        all_data['ingredients'] = import_ingredients_from_csv(ingredients_import_file)
    else:
        print(f"⚠️  {ingredients_import_file} not found - skipping ingredients import")
        all_data['ingredients'] = {}
    
    # Import runbook
    if runbook_import_file.exists():
        print(f"\n🔄 Importing runbook from {runbook_import_file}...")
        all_data['runbook'] = import_runbook_from_csv(runbook_import_file)
    else:
        print(f"⚠️  {runbook_import_file} not found - skipping runbook import")
        all_data['runbook'] = []
    
    # Save to JSON
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Import complete! Data saved to {json_file}")
        
        # Print summary
        print("\n📊 Import Summary:")
        if all_data.get('menu'):
            total_menu = sum(len(items) for items in all_data['menu'].values())
            print(f"  Menu: {total_menu} items across {len(all_data['menu'])} categories")
        if all_data.get('ingredients'):
            total_ingredients = sum(len(items) for items in all_data['ingredients'].values())
            print(f"  Ingredients: {total_ingredients} items across {len(all_data['ingredients'])} categories")
        if all_data.get('runbook'):
            print(f"  Runbook: {len(all_data['runbook'])} tasks")
        
        print("\n🔄 Next steps:")
        print("1. Refresh your website to see the updated data")
        print("2. The website will automatically load the new sushi_data.json")
        
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import CSV files to sushi_data.json')
    parser.add_argument('--menu', action='store_true', help='Import menu_imports.csv only')
    parser.add_argument('--ingredients', action='store_true', help='Import ingredients_imports.csv only')
    parser.add_argument('--runbook', action='store_true', help='Import runbook_imports.csv only')
    args = parser.parse_args()

    # If no args, import all
    import_menu = args.menu or not (args.menu or args.ingredients or args.runbook)
    import_ingredients = args.ingredients or not (args.menu or args.ingredients or args.runbook)
    import_runbook = args.runbook or not (args.menu or args.ingredients or args.runbook)

    script_dir = Path(__file__).parent
    data_dir = script_dir / 'data'
    import_dir = script_dir / 'import-export'
    json_file = data_dir / 'sushi_data.json'

    if not data_dir.exists():
        print(f"❌ Error: {data_dir} directory not found!")
        exit(1)
    if not import_dir.exists():
        print(f"❌ Error: {import_dir} directory not found!")
        exit(1)

    # Load existing data if present
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    else:
        data = {}

    if import_menu:
        menu_import_file = import_dir / 'menu_imports.csv'
        if menu_import_file.exists():
            print(f"🔄 Importing menu from {menu_import_file}...")
            data['menu'] = import_menu_from_csv(menu_import_file)
            print(f"✅ Imported {sum(len(items) for items in data['menu'].values())} menu items from {menu_import_file}")
        else:
            print(f"⚠️ Menu import file not found: {menu_import_file}")
    if import_ingredients:
        ingredients_import_file = import_dir / 'ingredients_imports.csv'
        if ingredients_import_file.exists():
            print(f"🔄 Importing ingredients from {ingredients_import_file}.")
            data['ingredients'] = import_ingredients_from_csv(ingredients_import_file)
            print(f"✅ Imported {sum(len(items) for items in data['ingredients'].values())} ingredients from {ingredients_import_file}")
        else:
            print(f"⚠️ Ingredients import file not found: {ingredients_import_file}")
    if import_runbook:
        runbook_import_file = import_dir / 'runbook_imports.csv'
        if runbook_import_file.exists():
            print(f"🔄 Importing runbook from {runbook_import_file}...")
            data['runbook'] = import_runbook_from_csv(runbook_import_file)
            print(f"✅ Imported {len(data['runbook'])} runbook items from {runbook_import_file}")
        else:
            print(f"⚠️ Runbook import file not found: {runbook_import_file}")

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Import complete! Data saved to {json_file}\n")
    print(f"📊 Import Summary:")
    print(f"  Menu: {sum(len(items) for items in data.get('menu', {}).values())} items across {len(data.get('menu', {}))} categories")
    print(f"  Runbook: {len(data.get('runbook', []))} tasks")
    print(f"\n🔄 Next steps:")
    print(f"1. Refresh your website to see the updated data")
    print(f"2. The website will automatically load the new sushi_data.json") 