-- Sushi Restaurant Database Schema
-- SQLite database for menu management, ingredients, and future features

-- Categories table
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingredients table
CREATE TABLE ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    store TEXT,
    cost REAL DEFAULT 0.0,
    quantity TEXT,
    unit_cost REAL DEFAULT 0.0,
    brand TEXT,
    shopping_cart_name TEXT,
    uses_per_purchase INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Menu items table
CREATE TABLE menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    description TEXT,
    price REAL DEFAULT 0.0,
    image_path TEXT,
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

-- Menu item ingredients relationship table
CREATE TABLE menu_item_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_item_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    quantity REAL DEFAULT 1.0,
    position TEXT NOT NULL, -- 'inside' or 'on_top'
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items (id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients (id) ON DELETE CASCADE,
    UNIQUE(menu_item_id, ingredient_id, position)
);

-- Runbook table
CREATE TABLE runbook_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timeline TEXT NOT NULL,
    activity TEXT NOT NULL,
    beginner_steps TEXT,
    advanced_steps TEXT,
    estimated_duration TEXT,
    notes TEXT,
    has_beginner BOOLEAN DEFAULT 0,
    has_advanced BOOLEAN DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Event menus table for shareable sushi night menus
CREATE TABLE event_menus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    menu_data TEXT NOT NULL, -- JSON string of selected menu items
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Future tables for enhanced features
-- Users table (for future authentication)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'customer',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table (for future ordering system)
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    status TEXT DEFAULT 'pending',
    total_amount REAL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Order items table
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL,
    total_price REAL NOT NULL,
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
);

-- Indexes for better performance
CREATE INDEX idx_menu_items_category ON menu_items(category_id);
CREATE INDEX idx_menu_items_active ON menu_items(is_active);
CREATE INDEX idx_ingredients_category ON ingredients(category);
CREATE INDEX idx_menu_item_ingredients_menu_item ON menu_item_ingredients(menu_item_id);
CREATE INDEX idx_menu_item_ingredients_ingredient ON menu_item_ingredients(ingredient_id);
CREATE INDEX idx_runbook_timeline ON runbook_items(timeline);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_event_menus_unique_id ON event_menus(unique_id);
CREATE INDEX idx_event_menus_expires ON event_menus(expires_at);

-- Insert default categories
INSERT INTO categories (name, color, sort_order) VALUES 
('Appetizer', '#FF69B4', 1),
('Nigiri', '#9945FF', 2),
('Maki Rolls', '#3B82F6', 3),
('Speciality Rolls', '#00D4AA', 4); 