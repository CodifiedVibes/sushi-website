#!/usr/bin/env python3
"""
Flask API server for Sushi Restaurant
Serves data from SQLite database
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect('sushi.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

@app.route('/api/menu', methods=['GET'])
def get_menu():
    """Get all menu items with their ingredients"""
    conn = get_db_connection()
    
    try:
        # Get menu items with category info
        cursor = conn.execute("""
            SELECT 
                mi.id, mi.name, mi.description, mi.price, mi.image_path,
                c.name as category, c.color as category_color
            FROM menu_items mi
            JOIN categories c ON mi.category_id = c.id
            WHERE mi.is_active = 1
            ORDER BY c.sort_order, mi.sort_order, mi.name
        """)
        
        menu_items = []
        for row in cursor.fetchall():
            item = dict(row)
            
            # Get ingredients for this menu item
            cursor2 = conn.execute("""
                SELECT 
                    i.name, i.category as ingredient_category,
                    mii.quantity, mii.position
                FROM menu_item_ingredients mii
                JOIN ingredients i ON mii.ingredient_id = i.id
                WHERE mii.menu_item_id = ?
                ORDER BY mii.position, mii.sort_order
            """, (item['id'],))
            
            ingredients_inside = []
            ingredients_on_top = []
            
            for ing_row in cursor2.fetchall():
                ing = dict(ing_row)
                if ing['position'] == 'inside':
                    ingredients_inside.append(ing['name'])
                else:
                    ingredients_on_top.append(ing['name'])
            
            item['ingredients_inside'] = ingredients_inside
            item['ingredients_on_top'] = ingredients_on_top
            
            menu_items.append(item)
        
        # Group by category
        menu_by_category = {}
        for item in menu_items:
            category = item['category']
            if category not in menu_by_category:
                menu_by_category[category] = []
            menu_by_category[category].append(item)
        
        return jsonify(menu_by_category)
        
    finally:
        conn.close()

@app.route('/api/ingredients', methods=['GET'])
def get_ingredients():
    """Get all ingredients"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT * FROM ingredients 
            ORDER BY category, name
        """)
        
        ingredients = [dict(row) for row in cursor.fetchall()]
        
        # Group by category
        ingredients_by_category = {}
        for ingredient in ingredients:
            category = ingredient['category']
            if category not in ingredients_by_category:
                ingredients_by_category[category] = []
            ingredients_by_category[category].append(ingredient)
        
        return jsonify(ingredients_by_category)
        
    finally:
        conn.close()

@app.route('/api/runbook', methods=['GET'])
def get_runbook():
    """Get all runbook items"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT * FROM runbook_items 
            ORDER BY sort_order, timeline
        """)
        
        runbook_items = [dict(row) for row in cursor.fetchall()]
        
        # Custom sorting function for timeline
        def timeline_sort_key(item):
            timeline = item['timeline']
            if timeline == 'T-0':
                return 0
            elif 'days' in timeline:
                # Extract number of days (e.g., "T-5 days" -> 5)
                days = int(timeline.split('-')[1].split()[0])
                return -days  # Negative so T-5 days comes before T-1 day
            elif 'hours' in timeline:
                # Extract number of hours (e.g., "T-4 hours" -> 4, "T-1.5 hours" -> 1.5)
                hours = float(timeline.split('-')[1].split()[0])
                return hours  # Positive so T-1 hour comes before T-4 hours
            elif 'min' in timeline:
                # Extract number of minutes (e.g., "T-30 min" -> 30)
                minutes = int(timeline.split('-')[1].split()[0])
                return minutes  # Positive so T-15 min comes before T-30 min
            else:
                return 999  # Unknown format goes to end
        
        # Sort by timeline
        runbook_items.sort(key=timeline_sort_key)
        
        return jsonify(runbook_items)
        
    finally:
        conn.close()

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT * FROM categories 
            ORDER BY sort_order
        """)
        
        categories = [dict(row) for row in cursor.fetchall()]
        return jsonify(categories)
        
    finally:
        conn.close()

@app.route('/api/menu/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    """Get a specific menu item by ID"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT 
                mi.*, c.name as category, c.color as category_color
            FROM menu_items mi
            JOIN categories c ON mi.category_id = c.id
            WHERE mi.id = ?
        """, (item_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Menu item not found'}), 404
        
        item = dict(row)
        
        # Get ingredients
        cursor2 = conn.execute("""
            SELECT 
                i.name, i.category as ingredient_category,
                mii.quantity, mii.position
            FROM menu_item_ingredients mii
            JOIN ingredients i ON mii.ingredient_id = i.id
            WHERE mii.menu_item_id = ?
            ORDER BY mii.position, mii.sort_order
        """, (item_id,))
        
        ingredients_inside = []
        ingredients_on_top = []
        
        for ing_row in cursor2.fetchall():
            ing = dict(ing_row)
            if ing['position'] == 'inside':
                ingredients_inside.append(ing['name'])
            else:
                ingredients_on_top.append(ing['name'])
        
        item['ingredients_inside'] = ingredients_inside
        item['ingredients_on_top'] = ingredients_on_top
        
        return jsonify(item)
        
    finally:
        conn.close()

@app.route('/api/search', methods=['GET'])
def search_menu():
    """Search menu items by name or ingredients"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT DISTINCT
                mi.id, mi.name, mi.description, mi.price,
                c.name as category, c.color as category_color
            FROM menu_items mi
            JOIN categories c ON mi.category_id = c.id
            JOIN menu_item_ingredients mii ON mi.id = mii.menu_item_id
            JOIN ingredients i ON mii.ingredient_id = i.id
            WHERE mi.is_active = 1 
            AND (LOWER(mi.name) LIKE ? OR LOWER(i.name) LIKE ?)
            ORDER BY c.sort_order, mi.name
        """, (f'%{query}%', f'%{query}%'))
        
        results = [dict(row) for row in cursor.fetchall()]
        return jsonify(results)
        
    finally:
        conn.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected'
    })

if __name__ == '__main__':
    print("Starting Sushi Restaurant API Server...")
    print("API will be available at: http://localhost:5001")
    print("Available endpoints:")
    print("  GET /api/menu - Get all menu items")
    print("  GET /api/ingredients - Get all ingredients")
    print("  GET /api/runbook - Get runbook items")
    print("  GET /api/categories - Get categories")
    print("  GET /api/menu/<id> - Get specific menu item")
    print("  GET /api/search?q=<query> - Search menu items")
    print("  GET /api/health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5001) 