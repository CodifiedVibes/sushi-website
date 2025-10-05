# Sushi Website Deployment Guide

## Railway Deployment (Recommended)

### 1. Prepare Your Repository
- Ensure all changes are committed and pushed to GitHub
- The repository should include:
  - `api_server.py` (Flask API server)
  - `index.html` (Frontend)
  - `app.js` (React frontend)
  - `requirements.txt` (Python dependencies)
  - `railway.json` (Railway configuration)
  - `postgresql_schema.sql` (Database schema)
  - `postgresql_data.sql` (Database data)

### 2. Deploy to Railway

1. **Go to Railway.app**
   - Visit [railway.app](https://railway.app)
   - Sign up/login with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your sushi-website repository

3. **Add PostgreSQL Database**
   - In your project dashboard, click "+ New"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically provide connection details

4. **Configure Environment Variables**
   - In your project settings, add these environment variables:
     ```
     DATABASE_URL=<Railway PostgreSQL URL>
     FLASK_ENV=production
     PORT=5001
     ```

5. **Deploy**
   - Railway will automatically build and deploy your app
   - The build process will install Python dependencies
   - Your API will be available at the Railway-provided URL

### 3. Initialize Database

After deployment, you'll need to set up the database:

1. **Access Railway CLI** (optional):
   ```bash
   npm install -g @railway/cli
   railway login
   railway connect <your-project-id>
   ```

2. **Run Database Setup**:
   - Use Railway's PostgreSQL console or connect via psql
   - Run the schema: `postgresql_schema.sql`
   - Import the data: `postgresql_data.sql`

### 4. Update Frontend Configuration

Update your `app.js` to use the Railway URL instead of localhost:

```javascript
// Change this line in app.js:
const API_BASE_URL = 'https://your-app-name.railway.app/api';

// Instead of:
const API_BASE_URL = 'http://localhost:5001/api';
```

## Alternative: Static Deployment (Simpler)

If you prefer a simpler approach without a database:

1. **Convert to Static JSON**:
   - Run the export scripts to generate JSON files
   - Update `app.js` to use local JSON data instead of API calls

2. **Deploy to Vercel/Netlify**:
   - Push to GitHub
   - Connect to Vercel or Netlify
   - Deploy as a static site

## Environment Variables

For production deployment, set these environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `FLASK_ENV`: Set to `production`
- `PORT`: Port number (Railway will set this automatically)

## Security Features

The production version includes:
- Rate limiting (100 requests per minute per IP)
- CORS protection
- Input validation
- Error handling

## Monitoring

Railway provides:
- Automatic deployments from GitHub
- Built-in monitoring and logs
- Automatic HTTPS
- Custom domain support (paid plans)

## Troubleshooting

### Common Issues:

1. **Database Connection Errors**:
   - Verify `DATABASE_URL` environment variable
   - Check PostgreSQL service is running
   - Ensure database schema is created

2. **Build Failures**:
   - Check `requirements.txt` for all dependencies
   - Verify Python version compatibility
   - Check Railway build logs

3. **API Not Responding**:
   - Verify port configuration
   - Check Railway service logs
   - Ensure all environment variables are set

### Support:
- Railway Documentation: https://docs.railway.app
- Railway Community: https://railway.app/discord
