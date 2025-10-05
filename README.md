# Sushi Website

A modern React-based sushi restaurant website with menu management, shopping cart, runbook, and ingredient tracking. Features a Solana-inspired UI with teal/purple gradients and a comprehensive data import/export workflow.

## 🏗️ File Structure

```
sushi-website/
├── app.js                    # Main React application (1070+ lines)
├── index.html                # HTML entry point
├── data/
│   └── sushi_data.json       # Legacy data file (now served via API)
├── import-export/            # CSV files for data editing
│   ├── menu_imports.csv      # Edit menu items here
│   ├── ingredients_imports.csv # Edit ingredients and costs here
│   ├── runbook_imports.csv   # Edit preparation timeline here
│   ├── menu_exports.csv      # Exported menu data
│   ├── ingredients_exports.csv # Exported ingredients data
│   ├── runbook_exports.csv   # Exported runbook data
│   ├── sauce_recipes.csv     # Sauce recipe data
│   ├── menu.csv              # Original menu data
│   ├── ingredients.csv       # Original ingredients data
│   └── runbook.csv           # Original runbook data
├── pictures/                 # Menu item images
├── export_json_to_csv.py     # Export JSON to CSV for editing
├── export_database_to_csv.py # Export database to CSV
├── convert_imports_to_json.py # Import CSV back to JSON
├── convert_imports_to_database.py # Import CSV to database
├── database_schema.sql       # SQLite database schema
├── postgresql_schema.sql     # PostgreSQL database schema
├── postgresql_data.sql       # PostgreSQL initial data
├── init_database.py          # Database initialization script
├── test_database_connection.py # Database connection test
├── migrate_to_sqlite.py      # Migration script from JSON to SQLite
├── migrate_to_postgresql.py  # Migration script to PostgreSQL
├── api_server.py             # Flask API server with auto-initialization
├── requirements.txt          # Python dependencies (including PostgreSQL)
├── railway.json              # Railway deployment configuration
├── sushi.db                  # SQLite database (local development)
└── README.md                 # This file
```

## 🌐 Live Website

**Production URL**: [https://sushi-website-production.up.railway.app](https://sushi-website-production.up.railway.app)

The website is deployed on Railway with PostgreSQL database and includes:
- ✅ Full menu browsing with 25+ sushi items
- ✅ Event menu creation and sharing
- ✅ Recipe lookup with detailed instructions
- ✅ Runbook timeline for preparation
- ✅ Ingredient tracking and shopping lists
- ✅ Responsive design for all devices

## 🚀 Running Locally

### Option 1: Database Mode (Recommended)
1. **Install Python dependencies:**
   ```bash
   cd sushi-website
   pip3 install -r requirements.txt
   ```

2. **Start the API server:**
   ```bash
   python3 api_server.py
   ```
   The API will be available at `http://localhost:5001`

   **Kill the API server:**
    ```bash
   $ lsof -ti:5001 | xargs kill -9
   ```
   
3. **Start the web server:**
   ```bash
   python3 -m http.server 8000
   ```

4. **Open in browser:**
   ```
   http://localhost:8000
   ```

### Option 2: Legacy JSON Mode
1. **Start the server:**
   ```bash
   cd sushi-website
   python3 -m http.server 8000
   ```

2. **Open in browser:**
   ```
   http://localhost:8000
   ```
   Note: This mode uses the local `sushi_data.json` file instead of the database.

## 📊 Data Management Workflow

### Export Current Data (for editing)
```bash
cd sushi-website
python3 export_database_to_csv.py
```
This creates CSV files in the `import-export/` folder:
- `import-export/menu_exports.csv`
- `import-export/ingredients_exports.csv`
- `import-export/runbook_exports.csv`

### Edit Data
1. Rename exported files to have `_imports` suffix:
   - `menu_exports.csv` → `menu_imports.csv`
   - `ingredients_exports.csv` → `ingredients_imports.csv`
   - `runbook_exports.csv` → `runbook_imports.csv`

2. Edit the CSV files in your preferred editor (Excel, Google Sheets, etc.)

### Import Edited Data
```bash
cd sushi-website
python3 convert_imports_to_database.py
```
This reads the `_imports` files and updates the SQLite database directly.

#### Selective Import Options
You can import only specific types of data using command-line options:

- Import only the menu:
  ```bash
  python3 convert_imports_to_database.py --menu
  ```
- Import only the ingredients:
  ```bash
  python3 convert_imports_to_database.py --ingredients
  ```
- Import only the runbook:
  ```bash
  python3 convert_imports_to_database.py --runbook
  ```
- Import menu and runbook only:
  ```bash
  python3 convert_imports_to_database.py --menu --runbook
  ```

**Note**: If you run the script with **no arguments**, it will import all three files (menu, ingredients, and runbook).

### Legacy JSON Workflow (Deprecated)
The old JSON-based workflow is still available but not recommended:
- `export_json_to_csv.py` - Export from legacy JSON
- `convert_imports_to_json.py` - Import to legacy JSON

## 🎨 Features

### Core Functionality
- **Menu Management**: Browse and filter sushi menu items by category
- **Shopping Cart**: Add items with quantity selection (1-5), view cart summary
- **Shopping Cart Page**: Dedicated page with item removal, total pricing, and print/export functionality
- **Ingredient Tracking**: Automatic ingredient list generation for cart items
- **Runbook**: Interactive timeline for sushi preparation with filtering and tips
- **Shopping Items**: Complete ingredient list with costs and store information

### UI/UX Features
- **Solana-inspired Design**: Modern teal/purple gradient color scheme
- **Responsive Layout**: Optimized for desktop and mobile viewing
- **Collapsible Categories**: Menu items grouped by category with sticky headers
- **Detail Drawer**: Right-side panel showing item details and ingredients
- **Floating Cart Summary**: Always-visible cart summary in top-left corner
- **Print-Friendly Views**: Optimized printing for shopping lists and cart contents
- **Copy to Clipboard**: Easy export of ingredient lists to notes apps

### Navigation
- **Left Sidebar**: Main navigation with Menu, Runbook, Shopping Items, and Cart
- **Sticky Headers**: Category headers that stay visible while scrolling
- **Cart Access**: Click cart summary to access full shopping cart page

## 📁 Data Structure

### Menu Items
Each menu item includes:
- Name, description, price, category
- Ingredient list with quantities
- Image reference (if available)

### Ingredients
Each ingredient includes:
- Name, store, category, cost per unit
- Standardized naming (e.g., "Kani (Imitation Crab)", Maguro (Tuna)")

### Runbook
Each runbook item includes:
- Step description, time, category
- Tips and notes for preparation

## 🚀 Deployment (Railway)

The website is deployed on [Railway](https://railway.app) with the following setup:

### Architecture
- **Frontend**: React app served by Flask static file routes
- **Backend**: Flask API server with automatic database initialization
- **Database**: PostgreSQL (production) / SQLite (local development)
- **Hosting**: Railway with automatic deployments from GitHub

### Deployment Files
- `railway.json` - Railway deployment configuration
- `requirements.txt` - Python dependencies including `psycopg2-binary` for PostgreSQL
- `postgresql_schema.sql` - Database schema for PostgreSQL
- `postgresql_data.sql` - Initial data for PostgreSQL
- `init_database.py` - Database initialization script

### Environment Variables (Railway)
- `DATABASE_URL` - PostgreSQL connection string (automatically set by Railway)

### Automatic Features
- **Database Initialization**: App automatically creates tables and imports data on first startup
- **Dynamic API URLs**: Frontend automatically detects local vs. production environment
- **Rate Limiting**: API endpoints protected with Flask-Limiter
- **CORS**: Configured for cross-origin requests

### Custom Domain Setup
To connect your custom domain (e.g., `cassaroll.io`):
1. Add custom domain in Railway dashboard
2. Update DNS records in GoDaddy to point to Railway
3. SSL certificate automatically provisioned

## 🔧 Technical Stack

- **Frontend**: React (via CDN), Tailwind CSS, Vanilla JavaScript
- **Backend**: Flask API server, Python for data processing
- **Database**: PostgreSQL (production) / SQLite (local development)
- **Data Format**: JSON for runtime, CSV for editing, SQL for database
- **Server**: Python HTTP server (no build process required)
- **Deployment**: Railway with automatic GitHub integration

## 🚀 Quick Start

1. Clone or download the project
2. Navigate to the `sushi-website` directory
3. Install dependencies: `pip3 install -r requirements.txt`
4. Start the API server: `python3 api_server.py` (runs on port 5001)
5. Start the web server: `python3 -m http.server 8000`
6. Open `http://localhost:8000` in your browser
7. Start browsing the menu and adding items to your cart!

## 📝 Development Notes

- All data editing is done through CSV files in the `import-export/` folder
- The main `sushi_data.json` file is auto-generated and should not be edited directly
- The website automatically loads the latest data on page refresh
- No build process or compilation required - just edit files and refresh!
- The database is automatically populated from the JSON data during migration
- API endpoints are available at `http://localhost:5001/api/` for programmatic access 