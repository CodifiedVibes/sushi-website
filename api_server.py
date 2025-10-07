#!/usr/bin/env python3
"""
Flask API server for Sushi Restaurant
Serves data from SQLite database
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for frontend

# Rate limiting setup
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def get_db_connection():
    """Create database connection - supports both SQLite (local) and PostgreSQL (Railway)"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # PostgreSQL connection for Railway
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        # SQLite connection for local development
        conn = sqlite3.connect('sushi.db')
        conn.row_factory = sqlite3.Row
    
    return conn

def migrate_readonly_column():
    """Add read_only column to event_menus table if it doesn't exist"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        return
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check if read_only column already exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'event_menus' AND column_name = 'read_only'
            """)
            
            if cursor.fetchone():
                print("✅ read_only column already exists")
                conn.close()
                return
            
            # Add read_only column
            print("🔄 Adding read_only column to event_menus table...")
            cursor.execute("""
                ALTER TABLE event_menus 
                ADD COLUMN read_only BOOLEAN DEFAULT FALSE
            """)
            
            conn.commit()
            print("✅ Successfully added read_only column to event_menus table")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

def check_and_initialize_database():
    """Check if database has data and initialize if empty"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Skip initialization for local SQLite
        return
    
    # First, run migration to add read_only column if needed
    migrate_readonly_column()
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check if menu_items table exists and has data
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_name = 'menu_items' AND table_schema = 'public'
            """)
            table_exists = cursor.fetchone()['count'] > 0
            
            if table_exists:
                cursor.execute("SELECT COUNT(*) as count FROM menu_items")
                menu_count = cursor.fetchone()['count']
                if menu_count > 0:
                    print("✅ Database already initialized with data")
                    conn.close()
                    return
            
            print("🔄 Database is empty, initializing...")
            
            # Read and execute schema
            with open('postgresql_schema.sql', 'r') as f:
                schema_sql = f.read()
                commands = [cmd.strip() for cmd in schema_sql.split(';') if cmd.strip()]
                for command in commands:
                    if command:
                        cursor.execute(command)
                conn.commit()
                print("✅ Schema created")
            
            # Read and execute data
            with open('postgresql_data.sql', 'r') as f:
                data_sql = f.read()
                commands = [cmd.strip() for cmd in data_sql.split(';') if cmd.strip()]
                for command in commands:
                    if command:
                        cursor.execute(command)
                conn.commit()
                print("✅ Data imported")
            
        conn.close()
        print("✅ Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Don't crash the app, just log the error

@app.route('/')
def serve_index():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/event/<event_id>')
def serve_event_page(event_id):
    """Serve the main HTML file for event pages (client-side routing)"""
    # Only serve HTML for event IDs (not static files)
    if '.' in event_id:
        # This is likely a static file request like /event/app.js
        return "Not Found", 404
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (JS, CSS, etc.)"""
    # Skip API routes
    if filename.startswith('api/'):
        return "Not Found", 404
    
    # Check if it's a static file that exists
    import os
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    
    # If it's not a static file, serve index.html for client-side routing
    return send_from_directory('.', 'index.html')

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
        
        return jsonify(menu_items)
        
    finally:
        conn.close()

@app.route('/api/ingredients', methods=['GET'])
def get_ingredients():
    """Get all ingredients grouped by category"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT name, category, store, cost, quantity, unit_cost, brand, 
                   shopping_cart_name, uses_per_purchase
            FROM ingredients
            ORDER BY category, name
        """)
        
        ingredients = {}
        for row in cursor.fetchall():
            ing = dict(row)
            category = ing['category']
            if category not in ingredients:
                ingredients[category] = []
            ingredients[category].append(ing)
        
        return jsonify(ingredients)
        
    finally:
        conn.close()

@app.route('/api/runbook', methods=['GET'])
def get_runbook():
    """Get all runbook items"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT * FROM runbook_items 
            ORDER BY sort_order ASC, timeline
        """)
        
        runbook_items = [dict(row) for row in cursor.fetchall()]
        
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
            ORDER BY sort_order, name
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
                mi.id, mi.name, mi.description, mi.price, mi.image_path,
                c.name as category, c.color as category_color
            FROM menu_items mi
            JOIN categories c ON mi.category_id = c.id
            WHERE mi.id = ? AND mi.is_active = 1
        """, (item_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Menu item not found'}), 404
        
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
    """Search menu items by name or description"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT 
                mi.id, mi.name, mi.description, mi.price, mi.image_path,
                c.name as category, c.color as category_color
            FROM menu_items mi
            JOIN categories c ON mi.category_id = c.id
            WHERE mi.is_active = 1 
            AND (mi.name LIKE ? OR mi.description LIKE ?)
            ORDER BY c.sort_order, mi.sort_order, mi.name
        """, (f'%{query}%', f'%{query}%'))
        
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
        
        return jsonify(menu_items)
        
    finally:
        conn.close()

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Get all recipes"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT * FROM recipes
            ORDER BY category, name
        """)
        
        recipes = [dict(row) for row in cursor.fetchall()]
        
        # Get ingredients for each recipe
        for recipe in recipes:
            cursor = conn.execute("""
                SELECT ingredient_name, quantity, unit, notes, order_index
                FROM recipe_ingredients 
                WHERE recipe_id = ?
                ORDER BY order_index
            """, (recipe['id'],))
            
            recipe['ingredients'] = [dict(row) for row in cursor.fetchall()]
        
        return jsonify(recipes)
        
    finally:
        conn.close()

@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a specific recipe by ID"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT * FROM recipes WHERE id = ?
        """, (recipe_id,))
        
        recipe = dict(cursor.fetchone())
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        
        # Get ingredients for the recipe
        cursor = conn.execute("""
            SELECT ingredient_name, quantity, unit, notes, order_index
            FROM recipe_ingredients 
            WHERE recipe_id = ?
            ORDER BY order_index
        """, (recipe_id,))
        
        recipe['ingredients'] = [dict(row) for row in cursor.fetchall()]
        
        return jsonify(recipe)
        
    finally:
        conn.close()

@app.route('/api/recipes/category/<category>', methods=['GET'])
def get_recipes_by_category(category):
    """Get recipes by category"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT * FROM recipes 
            WHERE category = ?
            ORDER BY name
        """, (category,))
        
        recipes = [dict(row) for row in cursor.fetchall()]
        
        # Get ingredients for each recipe
        for recipe in recipes:
            cursor = conn.execute("""
                SELECT ingredient_name, quantity, unit, notes, order_index
                FROM recipe_ingredients 
                WHERE recipe_id = ?
                ORDER BY order_index
            """, (recipe['id'],))
            
            recipe['ingredients'] = [dict(row) for row in cursor.fetchall()]
        
        return jsonify(recipes)
        
    finally:
        conn.close()

# Event Menu API endpoints
@app.route('/api/event-menus', methods=['POST'])
@limiter.limit("10 per minute")  # Limit event creation to 10 per minute per IP
def create_event_menu():
    """Create a new event menu"""
    conn = get_db_connection()
    
    try:
        data = request.get_json()
        if not data or not data.get('name') or not data.get('menu_data'):
            return jsonify({'error': 'Name and menu_data are required'}), 400
        
        # Generate unique ID
        unique_id = str(uuid.uuid4())[:8]  # Short ID for easy sharing
        
        # Set expiration to 30 days from now
        expires_at = datetime.now() + timedelta(days=30)
        
        cursor = conn.execute("""
            INSERT INTO event_menus (unique_id, name, description, menu_data, read_only, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            unique_id,
            data['name'],
            data.get('description', ''),
            json.dumps(data['menu_data']),
            data.get('read_only', False),
            expires_at
        ))
        
        conn.commit()
        
        return jsonify({
            'id': cursor.lastrowid,
            'unique_id': unique_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'read_only': data.get('read_only', False),
            'expires_at': expires_at.isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/event-menus/<unique_id>', methods=['GET'])
def get_event_menu(unique_id):
    """Get an event menu by unique ID"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT * FROM event_menus 
            WHERE unique_id = ? AND expires_at > datetime('now')
        """, (unique_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Event menu not found or expired'}), 404
        
        event_menu = dict(row)
        event_menu['menu_data'] = json.loads(event_menu['menu_data'])
        
        return jsonify(event_menu)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/event-menus/<unique_id>', methods=['PUT'])
def update_event_menu(unique_id):
    """Update an event menu"""
    conn = get_db_connection()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Check if event menu exists and is not expired
        cursor = conn.execute("""
            SELECT id FROM event_menus 
            WHERE unique_id = ? AND expires_at > datetime('now')
        """, (unique_id,))
        
        if not cursor.fetchone():
            return jsonify({'error': 'Event menu not found or expired'}), 404
        
        # Update the menu data
        update_fields = []
        update_values = []
        
        if 'name' in data:
            update_fields.append('name = ?')
            update_values.append(data['name'])
        
        if 'description' in data:
            update_fields.append('description = ?')
            update_values.append(data['description'])
        
        if 'menu_data' in data:
            update_fields.append('menu_data = ?')
            update_values.append(json.dumps(data['menu_data']))
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        update_values.append(unique_id)
        
        cursor = conn.execute(f"""
            UPDATE event_menus 
            SET {', '.join(update_fields)}
            WHERE unique_id = ?
        """, update_values)
        
        conn.commit()
        
        return jsonify({'message': 'Event menu updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/event-menus/<unique_id>', methods=['DELETE'])
def delete_event_menu(unique_id):
    """Delete an event menu"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            DELETE FROM event_menus WHERE unique_id = ?
        """, (unique_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Event menu not found'}), 404
        
        conn.commit()
        return jsonify({'message': 'Event menu deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/migrate-readonly', methods=['POST'])
def migrate_readonly_endpoint():
    """Manual endpoint to trigger read_only column migration"""
    try:
        migrate_readonly_column()
        return jsonify({'message': 'Migration completed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/event-menus', methods=['GET'])
def list_event_menus():
    """List all non-expired event menus (for admin/debug purposes)"""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT id, unique_id, name, description, created_at, expires_at
            FROM event_menus 
            WHERE expires_at > datetime('now')
            ORDER BY created_at DESC
        """)
        
        event_menus = [dict(row) for row in cursor.fetchall()]
        return jsonify(event_menus)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print("Starting Sushi Restaurant API Server...")
    print(f"API will be available at: http://localhost:{port}")
    
    # Initialize database if needed (for Railway deployment)
    check_and_initialize_database()
    
    print("Available endpoints:")
    print("  GET /api/menu - Get all menu items")
    print("  GET /api/ingredients - Get all ingredients")
    print("  GET /api/runbook - Get runbook items")
    print("  GET /api/categories - Get categories")
    print("  GET /api/menu/<id> - Get specific menu item")
    print("  GET /api/search?q=<query> - Search menu items")
    print("  GET /api/recipes - Get all recipes")
    print("  GET /api/recipes/<id> - Get specific recipe")
    print("  GET /api/recipes/category/<category> - Get recipes by category")
    print("  GET /api/health - Health check")
    print("  POST /api/event-menus - Create event menu")
    print("  GET /api/event-menus/<id> - Get event menu")
    print("  PUT /api/event-menus/<id> - Update event menu")
    print("  DELETE /api/event-menus/<id> - Delete event menu")
    print("  GET /api/event-menus - List all event menus")
    app.run(debug=False, host='0.0.0.0', port=port)