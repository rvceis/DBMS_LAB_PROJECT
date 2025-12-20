# MMS Full Stack Setup Guide

Complete guide to run the Metadata Management System (Flask Backend + React Frontend)

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (optional, can use SQLite for dev)

## Backend Setup (Flask)

### 1. Navigate to Flask backend
```powershell
cd "d:\DBMS PROJECT\flask_backend"
```

### 2. Create virtual environment (if not exists)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure environment
```powershell
# Copy and edit .env file
cp .env.example .env
```

Edit `.env`:
```
FLASK_ENV=development
DATABASE_URL=sqlite:///dev.db
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
```

### 5. Initialize database
```powershell
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Run Flask backend
```powershell
python main.py
```

Backend will run on **http://localhost:5000**

## Frontend Setup (React + Vite)

### 1. Navigate to Frontend
```powershell
cd "d:\DBMS PROJECT\Frontend"
```

### 2. Install dependencies
```powershell
npm install
```

### 3. Configure environment
```powershell
# .env already exists, verify it points to Flask backend
```

`.env` should contain:
```
VITE_API_URL=http://localhost:5000
```

### 4. Run development server
```powershell
npm run dev
```

Frontend will run on **http://localhost:5173**

## Usage Flow

### 1. Register a new user
- Open http://localhost:5173
- Click "Register"
- Fill in username, email, password
- Select role (viewer/editor/admin)
- Click "Register"

### 2. Login
- Use email and password to login
- You'll be redirected to dashboard

### 3. Explore features

## Dynamic Schema Upgrade (MetaDB)

The backend now supports a fully dynamic schema system (EAV). If you have an existing database, run migrations:

```powershell
cd "d:\DBMS PROJECT\flask_backend"
$env:FLASK_ENV="development"; $env:DATABASE_URL="postgresql://user:pass@host:5432/dbname"  # set for your env
& "D:/DBMS PROJECT/venv/Scripts/python.exe" -m flask db migrate -m "dynamic schema upgrade"
& "D:/DBMS PROJECT/venv/Scripts/python.exe" -m flask db upgrade
```

Fresh setup (SQLite dev):

```powershell
cd "d:\DBMS PROJECT\flask_backend"
$env:FLASK_ENV="development"; $env:DATABASE_URL="sqlite:///dev.db"
& "D:/DBMS PROJECT/venv/Scripts/python.exe" -m flask db init  # only once if not initialized
& "D:/DBMS PROJECT/venv/Scripts/python.exe" -m flask db migrate -m "init dynamic"
& "D:/DBMS PROJECT/venv/Scripts/python.exe" -m flask db upgrade
```

Run unit tests (in-memory SQLite):

```powershell
cd "d:\DBMS PROJECT\flask_backend"
& "D:/DBMS PROJECT/venv/Scripts/python.exe" -m pytest -q
```

**All users can:**
- View dashboard
- View asset types, schemas, and metadata

**Editors can:**
- Create schemas
- Create metadata records

**Admins can:**
- Create asset types
- Create schemas
- Create metadata records
- View all users

## API Endpoints

### Auth
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user

### Users
- `GET /users/me` - Get current user
- `GET /users` - List all users (admin only)

### Asset Types
- `GET /asset-types` - List asset types
- `POST /asset-types` - Create asset type (admin only)

### Schemas
- `GET /schemas` - List schemas
- `POST /schemas` - Create schema (admin/editor)

### Metadata
- `GET /metadata` - List metadata records
- `GET /metadata/:id` - Get single record
- `POST /metadata` - Create record (admin/editor)

## Troubleshooting

### Backend issues
- **Port 5000 in use**: Change port in `main.py`
- **Database errors**: Delete `dev.db` and re-run migrations
- **Module not found**: Reinstall requirements `pip install -r requirements.txt`

### Frontend issues
- **API connection failed**: Verify backend is running on port 5000
- **Module not found**: Run `npm install`
- **Port 5173 in use**: Vite will auto-assign another port

### CORS errors
Backend already has CORS enabled for all origins in development. If issues persist:
1. Check Flask backend logs
2. Verify `VITE_API_URL` in Frontend `.env`
3. Ensure both servers are running

## Production Deployment

### Backend
```powershell
# Use gunicorn
gunicorn main:app -w 4 -b 0.0.0.0:5000
```

### Frontend
```powershell
# Build production bundle
npm run build

# Preview build
npm run preview

# Deploy dist/ folder to static hosting (Vercel, Netlify, etc.)
```

## Project Structure

```
DBMS PROJECT/
├── flask_backend/           # Flask API backend
│   ├── app/
│   │   ├── __init__.py     # App factory
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── extensions.py   # Flask extensions
│   ├── main.py             # Entry point
│   ├── requirements.txt    # Python deps
│   └── .env               # Config (create from .env.example)
│
└── Frontend/               # React frontend
    ├── src/
    │   ├── components/    # Reusable components
    │   ├── pages/         # Page components
    │   ├── services/      # API services
    │   ├── context/       # State management
    │   └── config/        # Configuration
    ├── package.json       # Node deps
    └── .env              # Config
```

## Next Steps

1. **Run both servers** (backend on :5000, frontend on :5173)
2. **Register an admin user** to access all features
3. **Create some asset types** (e.g., "Image", "Document", "Video")
4. **Define schemas** with JSON Schema format
5. **Add metadata records** linked to schemas and asset types

## Support

For issues or questions:
1. Check backend logs (Flask console)
2. Check frontend logs (Browser DevTools Console)
3. Verify both servers are running
4. Check `.env` configuration in both projects
