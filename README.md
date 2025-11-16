# CASSaROLL - Sushi Knowledge Base

A modern React-based sushi restaurant website with menu management, event creation, shopping cart, runbook, and ingredient tracking. Features a Solana-inspired UI with teal/purple gradients and user authentication.

## 🌐 Live Website

**Production URL**: [https://cassaroll.io](https://cassaroll.io)

The website is deployed on Railway with PostgreSQL database and includes:
- ✅ Full menu browsing with categorized sushi items
- ✅ User authentication and email verification
- ✅ Event menu creation and sharing
- ✅ Recipe lookup with detailed instructions
- ✅ Runbook timeline for preparation
- ✅ Ingredient tracking and shopping lists
- ✅ Responsive design for all screen sizes

## 🏗️ File Structure

```
sushi-website/
├── app.js                    # Main React application
├── index.html                # HTML entry point
├── api_server.py             # Flask API server with auto-initialization
├── requirements.txt          # Python dependencies
├── railway.json              # Railway deployment configuration
├── postgresql_schema.sql     # PostgreSQL database schema (auto-loaded)
├── postgresql_data.sql       # PostgreSQL initial data (auto-loaded)
├── sushi.db                  # SQLite database (local development only)
├── import-export/            # CSV files (legacy, not actively used)
│   ├── menu_imports.csv
│   ├── ingredients_imports.csv
│   ├── runbook_imports.csv
│   └── sauce_recipes.csv
├── pictures/                 # Menu item images
└── README.md                 # This file
```

## 🚀 Running Locally

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

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
   
   **Note**: The server automatically:
   - Uses SQLite (`sushi.db`) for local development
   - Initializes the database if it doesn't exist
   - Serves the React frontend at the root URL

3. **Open in browser:**
   ```
   http://localhost:5001
   ```

### Local Development Notes

- **Database**: Local development uses SQLite (`sushi.db`). The database is automatically created on first run.
- **API Endpoints**: Available at `http://localhost:5001/api/`
- **Frontend**: Automatically detects local vs. production environment
- **Hot Reload**: Just refresh the browser after making changes

## 📊 Data Management

### Production Database (PostgreSQL)

The production database on Railway is managed directly through PostgreSQL:

1. **Connect to Railway PostgreSQL:**
   - Use Railway's PostgreSQL console
   - Or connect via `psql` with the connection string from Railway dashboard

2. **Edit Data:**
   - Edit data directly in PostgreSQL using SQL commands
   - Or use a PostgreSQL GUI tool (pgAdmin, DBeaver, etc.)

3. **Schema Updates:**
   - The `api_server.py` automatically handles schema migrations on startup
   - New columns are added via `ensure_auth_schema()` function

### Local Database (SQLite)

For local development, the SQLite database (`sushi.db`) can be edited using:
- SQLite command-line tool
- SQLite browser GUI
- Direct SQL commands

## 🎨 Features

### Core Functionality
- **Menu Management**: Browse and filter sushi menu items by category (Appetizer, Nigiri, Maki Rolls, Speciality Rolls)
- **Shopping Cart**: Add items with quantity selection (1-5), view cart in table format
- **Event Menus**: Create, share, and manage event menus with unique shareable links
- **User Accounts**: Registration, login, email verification, and event ownership
- **Ingredient Tracking**: Automatic ingredient list generation for cart items
- **Runbook**: Interactive timeline for sushi preparation with filtering and tips
- **Shopping List**: Complete ingredient list with costs and store information
- **Recipes**: Detailed recipe cards with ingredients, instructions, and difficulty ratings

### UI/UX Features
- **Solana-inspired Design**: Modern teal/purple gradient color scheme
- **Responsive Layout**: Optimized for desktop, tablet, and mobile viewing
- **Collapsible Categories**: Menu items grouped by category with sticky headers
- **Side Panels**: Shopping cart and runbook tips in expandable side panels
- **Event Detail Pages**: Beautiful spreadsheet-style event menu display
- **My Events Hub**: Manage all your event menus in one place

## 🔧 Technical Stack

- **Frontend**: React (via CDN), Tailwind CSS, Vanilla JavaScript
- **Backend**: Flask API server with automatic database initialization
- **Database**: PostgreSQL (production) / SQLite (local development)
- **Authentication**: Flask sessions with email verification via Resend API
- **Deployment**: Railway with automatic GitHub integration
- **Email**: Resend API for email verification

## 🚀 Deployment (Railway)

The website is deployed on [Railway](https://railway.app) with the following setup:

### Architecture
- **Frontend**: React app served by Flask static file routes
- **Backend**: Flask API server with automatic database initialization
- **Database**: PostgreSQL (production) / SQLite (local development)
- **Hosting**: Railway with automatic deployments from GitHub

### Environment Variables (Railway)

Required environment variables:
- `DATABASE_URL` - PostgreSQL connection string (automatically set by Railway)
- `SECRET_KEY` - Flask session secret key (auto-generated if not set)
- `MAIL_SERVER` - Email server (e.g., `smtp.resend.com`)
- `MAIL_PORT` - Email port (e.g., `587`)
- `MAIL_USE_TLS` - Use TLS (`True` for port 587)
- `MAIL_USERNAME` - Email username (Resend API key)
- `MAIL_PASSWORD` - Email password (Resend API key)
- `MAIL_DEFAULT_SENDER` - Sender email address
- `BASE_URL` - Base URL for email links (e.g., `https://cassaroll.io`)

### Automatic Features
- **Database Initialization**: App automatically creates tables and imports data on first startup
- **Schema Migrations**: Auth schema columns are automatically added if missing
- **Dynamic API URLs**: Frontend automatically detects local vs. production environment
- **Rate Limiting**: API endpoints protected with Flask-Limiter
- **CORS**: Configured for cross-origin requests

### Custom Domain Setup
The site uses a custom domain (`cassaroll.io`):
1. Custom domain configured in Railway dashboard
2. DNS records point to Railway
3. SSL certificate automatically provisioned

## 📝 Development Notes

- **No Build Process**: Just edit files and refresh the browser
- **Database Auto-Init**: Database schema and data are automatically loaded on first startup
- **Schema Migrations**: Auth-related columns are automatically added via `ensure_auth_schema()`
- **API Endpoints**: Available at `/api/*` for programmatic access
- **Static Files**: Served directly by Flask from the root directory

## 🔐 Authentication

The site includes user authentication with:
- User registration with email verification
- Login/logout functionality
- Event ownership (users can only see/edit their own events)
- Admin role support (for future admin features)
- Email verification via Resend API

## 📚 API Endpoints

### Menu & Data
- `GET /api/menu` - Get all menu items
- `GET /api/menu/<id>` - Get specific menu item
- `GET /api/ingredients` - Get all ingredients
- `GET /api/runbook` - Get runbook items
- `GET /api/categories` - Get categories
- `GET /api/recipes` - Get all recipes
- `GET /api/recipes/<id>` - Get specific recipe

### Events
- `GET /api/event-menus` - List all event menus (user's own)
- `GET /api/event-menus/<id>` - Get specific event menu
- `POST /api/event-menus` - Create event menu (requires auth)
- `PUT /api/event-menus/<id>` - Update event menu (requires auth)
- `DELETE /api/event-menus/<id>` - Delete event menu (requires auth)

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login user
- `POST /api/logout` - Logout user
- `GET /api/me` - Get current user info
- `GET /api/verify-email/<token>` - Verify email address

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Local: Ensure `sushi.db` file exists or let the server create it
   - Production: Verify `DATABASE_URL` environment variable in Railway

2. **Email Not Sending**:
   - Check Resend API credentials in environment variables
   - Verify `MAIL_SERVER`, `MAIL_PORT`, and `MAIL_USE_TLS` settings
   - Check Railway logs for email sending errors

3. **API Not Responding**:
   - Verify port configuration (default: 5001)
   - Check Railway service logs
   - Ensure all environment variables are set

4. **Frontend Not Loading**:
   - Clear browser cache
   - Check browser console for errors
   - Verify API server is running

### Support
- Railway Documentation: https://docs.railway.app
- Railway Community: https://railway.app/discord

## 📄 License

This project is private and proprietary.
