-- PostgreSQL Database Schema for Sushi Restaurant Website
-- This schema is compatible with PostgreSQL and includes proper data types

-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- Create ingredients table
CREATE TABLE IF NOT EXISTS ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    supplier VARCHAR(100),
    cost_per_unit DECIMAL(10,2),
    unit VARCHAR(20),
    storage_conditions TEXT,
    expiry_days INTEGER
);

-- Create menu_items table
CREATE TABLE IF NOT EXISTS menu_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    category_id INTEGER REFERENCES categories(id),
    ingredients TEXT,
    allergens TEXT,
    dietary_info TEXT
);

-- Create runbook_items table
CREATE TABLE IF NOT EXISTS runbook_items (
    id SERIAL PRIMARY KEY,
    activity VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    description TEXT,
    steps TEXT,
    time_estimate VARCHAR(50),
    difficulty VARCHAR(20),
    tools_needed TEXT,
    tips TEXT,
    safety_notes TEXT,
    related_items TEXT
);

-- Create recipes table
CREATE TABLE IF NOT EXISTS recipes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    instructions TEXT,
    prep_time INTEGER,
    cook_time INTEGER,
    total_time INTEGER,
    difficulty VARCHAR(20),
    yield VARCHAR(50),
    storage_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create recipe_ingredients table
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_name VARCHAR(100) NOT NULL,
    quantity VARCHAR(50) NOT NULL,
    unit VARCHAR(20),
    notes TEXT,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create event_menus table
CREATE TABLE IF NOT EXISTS event_menus (
    id SERIAL PRIMARY KEY,
    unique_id VARCHAR(8) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    menu_data JSONB,
    read_only BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create users table (for future authentication)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table (for future order management)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_menu_id INTEGER REFERENCES event_menus(id),
    order_data JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create order_items table (for future order management)
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id INTEGER REFERENCES menu_items(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    price DECIMAL(10,2),
    notes TEXT
);

-- Create menu_item_ingredients table (for many-to-many relationship)
CREATE TABLE IF NOT EXISTS menu_item_ingredients (
    id SERIAL PRIMARY KEY,
    menu_item_id INTEGER NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    quantity VARCHAR(50),
    unit VARCHAR(20)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category_id);
CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_recipe ON recipe_ingredients(recipe_id);
CREATE INDEX IF NOT EXISTS idx_event_menus_unique_id ON event_menus(unique_id);
CREATE INDEX IF NOT EXISTS idx_event_menus_expires ON event_menus(expires_at);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_event_menu ON orders(event_menu_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_menu_item_ingredients_menu ON menu_item_ingredients(menu_item_id);
CREATE INDEX IF NOT EXISTS idx_menu_item_ingredients_ingredient ON menu_item_ingredients(ingredient_id);
