# Sushi Website

A modern React-based sushi restaurant website with menu management, shopping cart, runbook, and ingredient tracking. Features a Solana-inspired UI with teal/purple gradients and a comprehensive data import/export workflow.

## 🏗️ File Structure

```
sushi-website/
├── app.js                # Main React application (836es)
├── index.html            # HTML entry point
├── data/
│   └── sushi_data.json   # Main data file (auto-generated)
├── import-export/        # CSV files for data editing
│   ├── menu_imports.csv      # Edit menu items here
│   ├── ingredients_imports.csv # Edit ingredients and costs here
│   ├── runbook_imports.csv    # Edit preparation timeline here
│   ├── menu.csv              # Original menu data
│   ├── ingredients.csv       # Original ingredients data
│   └── runbook.csv           # Original runbook data
├── pictures/             # Menu item images
├── export_json_to_csv.py # Export JSON to CSV for editing
├── convert_imports_to_json.py # Import CSV back to JSON
└── README.md             # This file
```

## 🚀 Running the Website

1. **Start the server:**
   ```bash
   cd sushi-website
   python3 -m http.server 8000
   ```

2. **Open in browser:**
   ```
   http://localhost:8000
   ```

## 📊 Data Management Workflow

### Export Current Data (for editing)
```bash
cd sushi-website
python3 export_json_to_csv.py
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
python3 convert_imports_to_json.py
```
This reads the `_imports` files and updates `sushi_data.json`.

#### Selective Import Options
You can import only specific types of data using command-line options:

- Import only the menu:
  ```bash
  python3 convert_imports_to_json.py --menu
  ```
- Import only the ingredients:
  ```bash
  python3 convert_imports_to_json.py --ingredients
  ```
- Import only the runbook:
  ```bash
  python3 convert_imports_to_json.py --runbook
  ```
- Import menu and runbook only:
  ```bash
  python3 convert_imports_to_json.py --menu --runbook
  ```

**Note**: If you run the script with **no arguments**, it will import all three files (menu, ingredients, and runbook).

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

## 🔧 Technical Stack

- **Frontend**: React (via CDN), Tailwind CSS, Vanilla JavaScript
- **Backend**: Python for data processing
- **Data Format**: JSON for runtime, CSV for editing
- **Server**: Python HTTP server (no build process required)

## 🚀 Quick Start

1. Clone or download the project
2. Navigate to the `sushi-website` directory
3. Run `python3 -m http.server 8000`
4. Open `http://localhost:8000` in your browser
5. Start browsing the menu and adding items to your cart!

## 📝 Development Notes

- All data editing is done through CSV files in the `import-export/` folder
- The main `sushi_data.json` file is auto-generated and should not be edited directly
- The website automatically loads the latest data on page refresh
- No build process or compilation required - just edit files and refresh! 