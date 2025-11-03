#!/usr/bin/env python3
"""
Flask API server for Sushi Restaurant
Serves data from SQLite database
"""

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import re

app = Flask(__name__, static_folder='.', static_url_path='')

# Session configuration for authentication
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-' + str(uuid.uuid4()))
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('DATABASE_URL') is not None  # HTTPS only in production

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

mail = Mail(app)

# Security: Configure CORS with specific origins
CORS(app, origins=[
    "https://cassaroll.io",
    "https://www.cassaroll.io", 
    "https://sushi-website-production.up.railway.app",
    "http://localhost:8000",  # For local development
    "http://127.0.0.1:8000",   # For local development
    "http://localhost:5001"   # For local API
], supports_credentials=True)

# Security: Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Rate limiting setup
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Security: Input validation functions
def validate_event_name(name):
    """Validate event name - alphanumeric, spaces, hyphens, underscores only"""
    if not name or len(name.strip()) == 0:
        return False
    if len(name) > 100:
        return False
    # Allow alphanumeric, spaces, hyphens, underscores, apostrophes
    return bool(re.match(r"^[a-zA-Z0-9\s\-_'\.]+$", name))

def validate_event_description(description):
    """Validate event description"""
    if not description:
        return True  # Description is optional
    if len(description) > 500:
        return False
    # Allow most characters except potential XSS
    return not re.search(r'<script|javascript:|on\w+\s*=', description, re.IGNORECASE)

def validate_host_name(host_name):
    """Validate host name"""
    if not host_name:
        return True  # Host name is optional
    if len(host_name) > 50:
        return False
    return bool(re.match(r"^[a-zA-Z0-9\s\-_'\.]+$", host_name))

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return text
    # Remove potential XSS attempts
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    return text.strip()

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

# Authentication helper functions
def get_current_user():
    """Get current logged in user from session"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgres')
    
    try:
        if is_postgres:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, role, email_verified FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        else:
            cursor = conn.execute("SELECT id, username, email, role, email_verified FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                # SQLite returns tuple, map to dict
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'role': row[3] if len(row) > 3 else 'user',
                    'email_verified': row[4] if len(row) > 4 else False
                }
        return None
    except Exception:
        return None
    finally:
        conn.close()

def require_auth(f):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        if not user.get('email_verified'):
            return jsonify({'error': 'Email verification required'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def require_admin(f):
    """Decorator to require admin role"""
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        if user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def send_verification_email(email, verification_token):
    """Send email verification link"""
    # Check if email is configured
    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        print("Email not configured (MAIL_USERNAME/MAIL_PASSWORD not set)")
        return False
    
    try:
        # Use frontend URL for verification link
        base_url = os.getenv('BASE_URL', 'https://cassaroll.io')
        if 'localhost' in base_url:
            base_url = 'http://localhost:5001'
        verify_url = f"{base_url}/verify-email/{verification_token}"
        msg = Message(
            'Verify your CASSaROLL account',
            recipients=[email],
            html=f"""
            <h2>Welcome to CASSaROLL!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verify_url}">{verify_url}</a></p>
            <p>This link will expire in 24 hours.</p>
            """
        )
        mail.send(msg)
        print(f"Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def migrate_readonly_column():
    """Add read_only column to event_menus table if it doesn't exist"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ No DATABASE_URL found")
        return False
    
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
                return True
            
            # Add read_only column
            print("🔄 Adding read_only column to event_menus table...")
            cursor.execute("""
                ALTER TABLE event_menus 
                ADD COLUMN read_only BOOLEAN DEFAULT FALSE
            """)
            
            conn.commit()
            print("✅ Successfully added read_only column to event_menus table")
            
            # Verify the column was added
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'event_menus' AND column_name = 'read_only'
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"✅ Column verified: {result['column_name']} ({result['data_type']}) with default {result['column_default']}")
            else:
                print("❌ Column verification failed")
                return False
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

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
@require_auth
def create_event_menu():
    """Create a new event menu"""
    conn = get_db_connection()
    
    try:
        data = request.get_json()
        if not data or not data.get('name') or not data.get('menu_data'):
            return jsonify({'error': 'Name and menu_data are required'}), 400
        
        # Security: Validate and sanitize inputs
        event_name = data.get('name', '').strip()
        event_description = data.get('description', '').strip()
        host_name = data.get('host_name', '').strip()
        
        if not validate_event_name(event_name):
            return jsonify({'error': 'Invalid event name. Use only letters, numbers, spaces, hyphens, and underscores.'}), 400
        
        if not validate_event_description(event_description):
            return jsonify({'error': 'Invalid event description. Contains potentially harmful content.'}), 400
            
        if not validate_host_name(host_name):
            return jsonify({'error': 'Invalid host name. Use only letters, numbers, spaces, hyphens, and underscores.'}), 400
        
        # Sanitize inputs
        event_name = sanitize_input(event_name)
        event_description = sanitize_input(event_description)
        host_name = sanitize_input(host_name)
        
        # Get current user (from @require_auth)
        user = get_current_user()
        user_id = user['id'] if user else None
        
        # Generate unique ID
        unique_id = str(uuid.uuid4())[:8]  # Short ID for easy sharing
        
        # Set expiration to 30 days from now
        expires_at = datetime.now() + timedelta(days=30)
        
        # Check which columns exist
        cursor = conn.cursor()
        database_url = os.getenv('DATABASE_URL')
        is_postgres = database_url and database_url.startswith('postgres')
        
        has_readonly_column = False
        has_hostname_column = False
        has_created_by_column = False
        
        if is_postgres:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'event_menus' AND column_name IN ('read_only', 'host_name', 'created_by')
            """)
            existing_cols = {row['column_name'] for row in cursor.fetchall()}
            has_readonly_column = 'read_only' in existing_cols
            has_hostname_column = 'host_name' in existing_cols
            has_created_by_column = 'created_by' in existing_cols
        else:
            cursor.execute("PRAGMA table_info(event_menus)")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            has_readonly_column = 'read_only' in col_names
            has_hostname_column = 'host_name' in col_names
            has_created_by_column = 'created_by' in col_names
        
        # Build INSERT statement based on available columns
        cols = ['unique_id', 'name', 'description', 'menu_data']
        vals = [unique_id, event_name, event_description, json.dumps(data['menu_data'])]
        
        if has_readonly_column:
            cols.append('read_only')
            vals.append(data.get('read_only', False))
        if has_hostname_column:
            cols.append('host_name')
            vals.append(host_name)
        if has_created_by_column:
            cols.append('created_by')
            vals.append(user_id)
        
        cols.append('expires_at')
        vals.append(expires_at)
        
        # Execute INSERT
        if is_postgres:
            placeholders = ', '.join(['%s'] * len(cols))
            query = f"INSERT INTO event_menus ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id"
            cursor.execute(query, tuple(vals))
            event_id = cursor.fetchone()['id']
        else:
            placeholders = ', '.join(['?'] * len(cols))
            query = f"INSERT INTO event_menus ({', '.join(cols)}) VALUES ({placeholders})"
            cursor.execute(query, tuple(vals))
            event_id = cursor.lastrowid
        
        conn.commit()
        
        response_data = {
            'id': event_id,
            'unique_id': unique_id,
            'name': event_name,
            'description': event_description,
            'expires_at': expires_at.isoformat()
        }
        
        if has_hostname_column:
            response_data['host_name'] = host_name
        
        if has_readonly_column:
            response_data['read_only'] = data.get('read_only', False)
        
        return jsonify(response_data), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/event-menus/<unique_id>', methods=['GET'])
def get_event_menu(unique_id):
    """Get an event menu by unique ID"""
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgres')
    
    try:
        if is_postgres:
            # PostgreSQL
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM event_menus 
                WHERE unique_id = %s AND expires_at > NOW()
            """, (unique_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Event menu not found or expired'}), 404
            
            event_menu = dict(row)
            # Handle JSONB - it might already be a dict or a string
            if isinstance(event_menu['menu_data'], str):
                event_menu['menu_data'] = json.loads(event_menu['menu_data'])
            elif isinstance(event_menu['menu_data'], dict):
                # Already parsed JSONB
                pass
        else:
            # SQLite
            cursor = conn.execute("""
                SELECT id, unique_id, name, description, menu_data, read_only, host_name, created_at, expires_at, created_by
                FROM event_menus 
                WHERE unique_id = ? AND expires_at > datetime('now')
            """, (unique_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Event menu not found or expired'}), 404
            
            # Map SQLite row to dict
            event_menu = {
                'id': row[0],
                'unique_id': row[1],
                'name': row[2],
                'description': row[3],
                'menu_data': json.loads(row[4]) if isinstance(row[4], str) else row[4],
                'read_only': row[5] if len(row) > 5 else False,
                'host_name': row[6] if len(row) > 6 else None,
                'created_at': row[7] if len(row) > 7 else None,
                'expires_at': row[8] if len(row) > 8 else None,
                'created_by': row[9] if len(row) > 9 else None
            }
        
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

@app.route('/api/debug-db', methods=['GET'])
def debug_database():
    """Debug endpoint to check database connection and table structure"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check if event_menus table exists
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'event_menus'
            """)
            table_exists = cursor.fetchone()
            
            # Check columns in event_menus table
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'event_menus'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
        conn.close()
        
        return jsonify({
            'table_exists': bool(table_exists),
            'columns': [dict(col) for col in columns],
            'database_url_set': bool(os.getenv('DATABASE_URL'))
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-readonly-column', methods=['POST'])
def add_readonly_column():
    """Simple endpoint to add read_only column"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Try to add the column
        cursor.execute("ALTER TABLE event_menus ADD COLUMN read_only BOOLEAN DEFAULT FALSE")
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'read_only column added successfully'}), 200
        
    except Exception as e:
        if 'already exists' in str(e) or 'duplicate column' in str(e):
            return jsonify({'message': 'read_only column already exists'}), 200
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-hostname-column', methods=['POST'])
def add_hostname_column():
    """Simple endpoint to add host_name column"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Try to add the column
        cursor.execute("ALTER TABLE event_menus ADD COLUMN host_name VARCHAR(100)")
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'host_name column added successfully'}), 200
        
    except Exception as e:
        if 'already exists' in str(e) or 'duplicate column' in str(e):
            return jsonify({'message': 'host_name column already exists'}), 200
        return jsonify({'error': str(e)}), 500

@app.route('/api/migrate-readonly', methods=['POST'])
def migrate_readonly_endpoint():
    """Manual endpoint to trigger read_only column migration"""
    try:
        success = migrate_readonly_column()
        if success:
            return jsonify({'message': 'Migration completed successfully'}), 200
        else:
            return jsonify({'error': 'Migration failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/event-menus', methods=['GET'])
def list_event_menus():
    """List event menus - filtered by user, or all for admin"""
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgres')
    
    try:
        user = get_current_user()
        filter_my_events = request.args.get('filter') == 'my_events'
        
        # Build WHERE clause
        where_clauses = ["expires_at > NOW()" if is_postgres else "expires_at > datetime('now')"]
        params = []
        
        if user:
            if filter_my_events or user.get('role') != 'admin':
                # Filter to user's events only (only if created_by column exists)
                # Check if created_by column exists first
                has_created_by = False
                if is_postgres:
                    cursor_check = conn.cursor()
                    cursor_check.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'event_menus' AND column_name = 'created_by'
                    """)
                    has_created_by = cursor_check.fetchone() is not None
                else:
                    cursor_check = conn.execute("PRAGMA table_info(event_menus)")
                    columns = cursor_check.fetchall()
                    col_names = [col[1] for col in columns]
                    has_created_by = 'created_by' in col_names
                
                if has_created_by:
                    where_clauses.append("created_by = " + ("%s" if is_postgres else "?"))
                    params.append(user['id'])
                else:
                    # If created_by column doesn't exist, return empty for security
                    # (we don't want to show events created before auth was added)
                    return jsonify([])
            # Admin sees all if not filtering
        else:
            # Not logged in - return empty (or could return public events)
            return jsonify([])
        
        where_sql = " AND ".join(where_clauses)
        
        if is_postgres:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, unique_id, name, description, menu_data, host_name, created_at, expires_at, created_by
                FROM event_menus 
                WHERE {where_sql}
                ORDER BY created_at DESC
            """, tuple(params))
            rows = cursor.fetchall()
            event_menus = []
            for row in rows:
                menu = {
                    'id': row['id'],
                    'unique_id': row['unique_id'],
                    'name': row['name'],
                    'description': row['description'],
                    'menu_data': row['menu_data'],  # JSONB or JSON string
                    'host_name': row['host_name'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'expires_at': row['expires_at'].isoformat() if row['expires_at'] else None,
                    'created_by': row['created_by']
                }
                event_menus.append(menu)
        else:
            # SQLite - need to check column count
            cursor = conn.execute(f"""
                SELECT id, unique_id, name, description, menu_data, host_name, created_at, expires_at, created_by
                FROM event_menus 
                WHERE {where_sql}
                ORDER BY created_at DESC
            """, tuple(params))
            
            event_menus = []
            for row in cursor.fetchall():
                # Parse menu_data if it's a string
                menu_data = row[4]
                if isinstance(menu_data, str):
                    try:
                        menu_data = json.loads(menu_data)
                    except:
                        pass
                
                menu = {
                    'id': row[0],
                    'unique_id': row[1],
                    'name': row[2],
                    'description': row[3],
                    'menu_data': menu_data,
                    'host_name': row[5],
                    'created_at': row[6],
                    'expires_at': row[7],
                    'created_by': row[8] if len(row) > 8 else None
                }
                event_menus.append(menu)
        
        return jsonify(event_menus)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Authentication endpoints
@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Register a new user"""
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgres')
    
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password') or not data.get('username'):
            return jsonify({'error': 'Email, username, and password are required'}), 400
        
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # Validate inputs
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Invalid email format'}), 400
        if len(username) < 3 or len(username) > 50:
            return jsonify({'error': 'Username must be 3-50 characters'}), 400
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return jsonify({'error': 'Username can only contain letters, numbers, and underscores'}), 400
        
        # Check if user already exists
        if is_postgres:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s OR username = %s", (email, username))
        else:
            cursor = conn.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, username))
        
        if cursor.fetchone():
            return jsonify({'error': 'Email or username already exists'}), 400
        
        # Create user
        password_hash = generate_password_hash(password)
        verification_token = str(uuid.uuid4())
        verification_expires = datetime.now() + timedelta(days=1)
        
        if is_postgres:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, verification_token, verification_token_expires, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (username, email, password_hash, verification_token, verification_expires))
            user_id = cursor.fetchone()['id']
        else:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, verification_token, verification_token_expires, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (username, email, password_hash, verification_token, verification_expires))
            user_id = cursor.lastrowid
        
        conn.commit()
        
        # Send verification email (non-blocking - don't fail registration if email fails)
        email_sent = False
        try:
            email_sent = send_verification_email(email, verification_token)
        except Exception as e:
            print(f"Email sending failed (non-critical): {e}")
        
        message = 'Registration successful. Please check your email to verify your account.'
        if not email_sent:
            message += f' (Note: Email verification not configured. Contact admin to verify account. Token: {verification_token})'
        
        return jsonify({
            'message': message,
            'user_id': user_id,
            'email_sent': email_sent,
            'verification_token': verification_token if not email_sent else None
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Login user"""
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgres')
    
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        
        database_url_env = os.getenv('DATABASE_URL')
        print(f"Login attempt for email: {email}")
        print(f"DATABASE_URL exists: {database_url_env is not None}")
        print(f"DATABASE_URL starts with postgres: {database_url_env.startswith('postgres') if database_url_env else False}")
        print(f"DB type: {'PostgreSQL' if is_postgres else 'SQLite'}")
        
        # Find user
        if is_postgres:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, password_hash, role, email_verified FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
        else:
            cursor = conn.execute("SELECT id, username, email, password_hash, role, email_verified FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
        
        if not row:
            print(f"User not found for email: {email}")
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Handle SQLite vs PostgreSQL row formats
        if is_postgres:
            user = dict(row)
        else:
            # SQLite returns tuple, map to dict
            user = {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'password_hash': row[3],
                'role': row[4] if len(row) > 4 else 'user',
                'email_verified': row[5] if len(row) > 5 else False
            }
        
        print(f"User found: {user['username']}, email_verified: {user.get('email_verified')}")
        
        # Check password
        password_valid = check_password_hash(user['password_hash'], password)
        if not password_valid:
            print(f"Password check failed for user: {user['username']}")
            return jsonify({'error': 'Invalid email or password'}), 401
        
        print(f"Login successful for user: {user['username']}")
        
        # Set session
        session['user_id'] = user['id']
        session.permanent = True
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'email_verified': bool(user['email_verified'])
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/me', methods=['GET'])
def get_current_user_info():
    """Get current user information"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'role': user['role'],
        'email_verified': bool(user.get('email_verified', False))
    }), 200

@app.route('/api/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Verify user email"""
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgres')
    
    try:
        # Find user by token
        if is_postgres:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, verification_token, verification_token_expires 
                FROM users 
                WHERE verification_token = %s
            """, (token,))
            row = cursor.fetchone()
        else:
            cursor = conn.execute("""
                SELECT id, verification_token, verification_token_expires 
                FROM users 
                WHERE verification_token = ?
            """, (token,))
            row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Invalid verification token'}), 400
        
        # Handle SQLite vs PostgreSQL row formats
        if is_postgres:
            user = dict(row)
        else:
            # SQLite returns tuple, map to dict
            user = {
                'id': row[0],
                'verification_token': row[1] if len(row) > 1 else None,
                'verification_token_expires': row[2] if len(row) > 2 else None
            }
        
        # Check if token expired (24 hours)
        if user.get('verification_token_expires'):
            expires = user['verification_token_expires']
            if isinstance(expires, str):
                expires = datetime.fromisoformat(expires.replace('Z', '+00:00'))
            if expires < datetime.now():
                return jsonify({'error': 'Verification token expired'}), 400
        
        # Verify email
        if is_postgres:
            cursor.execute("""
                UPDATE users 
                SET email_verified = TRUE, verification_token = NULL, verification_token_expires = NULL
                WHERE id = %s
            """, (user['id'],))
        else:
            cursor.execute("""
                UPDATE users 
                SET email_verified = 1, verification_token = NULL, verification_token_expires = NULL
                WHERE id = ?
            """, (user['id'],))
        
        conn.commit()
        
        return jsonify({'message': 'Email verified successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/get-verification-token', methods=['GET'])
def get_verification_token():
    """Get the current user's verification token (doesn't require email verification)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgres')
    
    try:
        if is_postgres:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT verification_token, verification_token_expires 
                FROM users 
                WHERE id = %s
            """, (user['id'],))
            row = cursor.fetchone()
        else:
            cursor = conn.execute("""
                SELECT verification_token, verification_token_expires 
                FROM users 
                WHERE id = ?
            """, (user['id'],))
            row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'User not found'}), 404
        
        # Handle SQLite vs PostgreSQL row formats
        if is_postgres:
            token_data = dict(row)
        else:
            # SQLite row is a tuple, map by index
            token_data = {
                'verification_token': row[0] if len(row) > 0 else None,
                'verification_token_expires': row[1] if len(row) > 1 else None
            }
        
        # If no token exists, generate a new one
        if not token_data.get('verification_token'):
            # Generate new verification token
            import secrets
            verification_token = secrets.token_urlsafe(32)
            verification_expires = datetime.now() + timedelta(hours=24)
            
            if is_postgres:
                cursor.execute("""
                    UPDATE users 
                    SET verification_token = %s, verification_token_expires = %s
                    WHERE id = %s
                """, (verification_token, verification_expires, user['id']))
            else:
                conn.execute("""
                    UPDATE users 
                    SET verification_token = ?, verification_token_expires = ?
                    WHERE id = ?
                """, (verification_token, verification_expires, user['id']))
            conn.commit()
            
            return jsonify({
                'verification_token': verification_token,
                'expires_at': verification_expires.isoformat()
            }), 200
        
        expires_at = token_data.get('verification_token_expires')
        if expires_at and isinstance(expires_at, str):
            # Already a string, use as is
            expires_iso = expires_at
        elif expires_at:
            # It's a datetime object, convert to ISO
            expires_iso = expires_at.isoformat() if hasattr(expires_at, 'isoformat') else str(expires_at)
        else:
            expires_iso = None
        
        return jsonify({
            'verification_token': token_data['verification_token'],
            'expires_at': expires_iso
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/verify-email', methods=['POST'])
@require_admin
def admin_verify_email():
    """Admin endpoint to verify any user's email"""
    data = request.get_json()
    user_id = data.get('user_id')
    username = data.get('username')
    
    if not user_id and not username:
        return jsonify({'error': 'user_id or username required'}), 400
    
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgres')
    
    try:
        # Find user
        if is_postgres:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            else:
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                return jsonify({'error': 'User not found'}), 404
            target_user_id = user_row['id']
            
            cursor.execute("""
                UPDATE users 
                SET email_verified = TRUE, verification_token = NULL, verification_token_expires = NULL
                WHERE id = %s
            """, (target_user_id,))
        else:
            if user_id:
                cursor = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            else:
                cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                return jsonify({'error': 'User not found'}), 404
            target_user_id = user_row[0]
            
            conn.execute("""
                UPDATE users 
                SET email_verified = 1, verification_token = NULL, verification_token_expires = NULL
                WHERE id = ?
            """, (target_user_id,))
        
        conn.commit()
        return jsonify({'message': 'Email verified successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/set-admin', methods=['POST'])
@require_admin
def set_admin():
    """Admin endpoint to set another user as admin"""
    data = request.get_json()
    user_id = data.get('user_id')
    username = data.get('username')
    
    if not user_id and not username:
        return jsonify({'error': 'user_id or username required'}), 400
    
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgres')
    
    try:
        if is_postgres:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("UPDATE users SET role = 'admin' WHERE id = %s", (user_id,))
            else:
                cursor.execute("UPDATE users SET role = 'admin' WHERE username = %s", (username,))
        else:
            if user_id:
                conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user_id,))
            else:
                conn.execute("UPDATE users SET role = 'admin' WHERE username = ?", (username,))
        
        conn.commit()
        return jsonify({'message': 'Admin role set successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/debug-db-info', methods=['GET'])
def debug_db_info():
    """Debug endpoint to see what database Railway is using"""
    database_url = os.getenv('DATABASE_URL', 'NOT SET')
    
    # Mask password for security
    if database_url != 'NOT SET' and '@' in database_url:
        parts = database_url.split('@')
        if len(parts) == 2:
            user_pass = parts[0].split('://')[-1]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                masked_url = database_url.replace(user_pass, f"{user}:***")
            else:
                masked_url = database_url
        else:
            masked_url = database_url
    else:
        masked_url = database_url
    
    try:
        conn = get_db_connection()
        is_postgres = database_url != 'NOT SET' and database_url.startswith('postgres')
        cursor = conn.cursor()
        
        # Get database name and connection info
        if is_postgres:
            cursor.execute("SELECT current_database(), inet_server_addr(), inet_server_port()")
            db_info = cursor.fetchone()
            database_name = db_info[0] if db_info else 'unknown'
            server_addr = db_info[1] if db_info and len(db_info) > 1 else 'unknown'
            server_port = db_info[2] if db_info and len(db_info) > 2 else 'unknown'
            
            # Check runbook count and sample
            cursor.execute("SELECT COUNT(*) as count FROM runbook_items")
            count = cursor.fetchone()['count']
            
            cursor.execute("SELECT activity, notes FROM runbook_items WHERE activity = 'Order Fish' LIMIT 1")
            order_fish = cursor.fetchone()
            notes_preview = order_fish['notes'][:100] if order_fish and order_fish.get('notes') else 'not found'
            
        else:
            # SQLite
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='runbook_items'")
            database_name = 'SQLite'
            server_addr = 'local'
            server_port = 'N/A'
            
            cursor.execute("SELECT COUNT(*) FROM runbook_items")
            count = cursor.fetchone()[0]
            
            cursor.execute("SELECT activity, notes FROM runbook_items WHERE activity = 'Order Fish' LIMIT 1")
            row = cursor.fetchone()
            notes_preview = row[1][:100] if row and len(row) > 1 and row[1] else 'not found'
        
        conn.close()
        
        return jsonify({
            'database_url_masked': masked_url,
            'database_type': 'PostgreSQL' if is_postgres else 'SQLite',
            'database_name': database_name,
            'server_address': server_addr,
            'server_port': server_port,
            'runbook_items_count': count,
            'order_fish_notes_preview': notes_preview,
            'has_yamaseafood_text': 'Yamaseafood.com' in notes_preview if notes_preview else False
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'database_url_masked': masked_url
        })

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