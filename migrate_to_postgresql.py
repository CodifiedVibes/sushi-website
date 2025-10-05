#!/usr/bin/env python3
"""
Migration script to convert SQLite database to PostgreSQL format
This script reads from the existing SQLite database and outputs PostgreSQL INSERT statements
"""

import sqlite3
import json
from datetime import datetime

def get_sqlite_connection():
    """Connect to the SQLite database"""
    return sqlite3.connect('sushi.db')

def escape_sql_string(value):
    """Escape string values for SQL"""
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        # Escape single quotes and wrap in quotes
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return str(value)

def migrate_table_to_postgresql(table_name, columns, conn):
    """Generate PostgreSQL INSERT statements for a table"""
    cursor = conn.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        return []
    
    insert_statements = []
    column_names = [description[0] for description in cursor.description]
    
    for row in rows:
        values = []
        for i, value in enumerate(row):
            if column_names[i] in ['menu_data', 'runbook_data'] and value:
                # JSON fields - convert to PostgreSQL JSON format
                if isinstance(value, str):
                    try:
                        # Validate JSON
                        json.loads(value)
                        values.append(escape_sql_string(value))
                    except json.JSONDecodeError:
                        # If it's not valid JSON, treat as string
                        values.append(escape_sql_string(value))
                else:
                    values.append(escape_sql_string(value))
            elif isinstance(value, datetime):
                values.append(f"'{value.isoformat()}'")
            else:
                values.append(escape_sql_string(value))
        
        values_str = ', '.join(values)
        insert_statements.append(f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({values_str});")
    
    return insert_statements

def main():
    """Main migration function"""
    print("Starting SQLite to PostgreSQL migration...")
    
    # Connect to SQLite database
    conn = get_sqlite_connection()
    
    # Define table order (respecting foreign key constraints)
    tables = [
        ('categories', ['id', 'name', 'description']),
        ('menu_items', ['id', 'name', 'description', 'price', 'category_id', 'ingredients', 'allergens', 'dietary_info']),
        ('ingredients', ['id', 'name', 'category', 'supplier', 'cost_per_unit', 'unit', 'storage_conditions', 'expiry_days']),
        ('runbook_items', ['id', 'activity', 'category', 'description', 'steps', 'time_estimate', 'difficulty', 'tools_needed', 'tips', 'safety_notes', 'related_items']),
        ('recipes', ['id', 'name', 'category', 'description', 'instructions', 'prep_time', 'cook_time', 'total_time', 'difficulty', 'yield', 'storage_notes', 'created_at', 'updated_at']),
        ('recipe_ingredients', ['id', 'recipe_id', 'ingredient_name', 'quantity', 'unit', 'notes', 'order_index', 'created_at', 'updated_at']),
        ('event_menus', ['id', 'unique_id', 'name', 'description', 'menu_data', 'created_at', 'expires_at'])
    ]
    
    all_inserts = []
    
    # Generate INSERT statements for each table
    for table_name, columns in tables:
        print(f"Processing table: {table_name}")
        try:
            inserts = migrate_table_to_postgresql(table_name, columns, conn)
            all_inserts.extend(inserts)
            print(f"  Generated {len(inserts)} INSERT statements")
        except Exception as e:
            print(f"  Error processing {table_name}: {e}")
    
    conn.close()
    
    # Write to file
    output_file = 'postgresql_data.sql'
    with open(output_file, 'w') as f:
        f.write("-- PostgreSQL data migration from SQLite\n")
        f.write("-- Generated on: " + datetime.now().isoformat() + "\n\n")
        f.write("-- Disable foreign key checks temporarily\n")
        f.write("SET session_replication_role = replica;\n\n")
        
        for insert in all_inserts:
            f.write(insert + "\n")
        
        f.write("\n-- Re-enable foreign key checks\n")
        f.write("SET session_replication_role = DEFAULT;\n")
    
    print(f"\nMigration complete!")
    print(f"PostgreSQL INSERT statements written to: {output_file}")
    print(f"Total statements generated: {len(all_inserts)}")

if __name__ == "__main__":
    main()
