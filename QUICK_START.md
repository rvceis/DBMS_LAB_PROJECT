# 🚀 MetaDB - Quick Start Guide

## Prerequisites
- Python 3.10+ with pip
- Node.js 18+ with npm
- PostgreSQL 14+ (or use SQLite for dev)

## Installation Steps

### 1. Clone & Setup Backend

```powershell
# Navigate to backend
cd "d:\DBMS PROJECT\flask_backend"

# Activate virtual environment (if not already active)
& "D:/DBMS PROJECT/venv/Scripts/Activate.ps1"

# Install dependencies (if not done)
pip install -r requirements.txt

# Set environment variables
$env:FLASK_ENV="development"
$env:DATABASE_URL="sqlite:///dev.db"  # Or use PostgreSQL URL

# Initialize database
python -m flask db init
python -m flask db migrate -m "initial migration"
python -m flask db upgrade

# Create admin user
python add_admin.py
# Follow prompts to create admin account

# Start backend
python main.py
```

**Backend runs on**: http://localhost:5000

---

### 2. Setup Frontend

```powershell
# Navigate to frontend
cd "d:\DBMS PROJECT\Frontend"

# Install dependencies
npm install --legacy-peer-deps

# Start dev server
npm run dev
```

**Frontend runs on**: http://localhost:5173

---

## 🔐 Login

Navigate to: **http://localhost:5173/login**

**Demo Credentials**:
```
Email: admin@test.com
Password: password
```

---

## 📚 What You Can Do

### **Dashboard** (`/dashboard`)
- View system statistics
- See recent metadata records
- Monitor activity

### **Schemas** (`/schemas`)
- Create new schemas with fields
- Edit existing schemas
- Add/modify/delete fields
- View field types and constraints

### **Metadata** (`/metadata`)
- Create metadata records
- Dynamic forms based on schema
- Filter and search records
- View record details

---

## 🎨 Features Implemented

✅ User authentication (JWT)
✅ Dynamic schema creation
✅ Field management (add/edit/delete)
✅ Metadata CRUD with dynamic forms
✅ Role-based access control
✅ Dark/Light theme toggle
✅ Responsive design
✅ Real-time notifications

---

## 📊 Architecture

### **Backend**
- Flask 2.2+ with SQLAlchemy
- JWT authentication
- EAV storage pattern
- Schema versioning
- Audit trail

### **Frontend**
- React 18.3 + TypeScript
- Material-UI 5.15
- Zustand state management
- React Hook Form
- Vite build tool

---

## 🔧 Development Commands

### Backend
```powershell
# Run backend
python main.py

# Run tests
pytest -q

# Database migrations
flask db migrate -m "description"
flask db upgrade
```

### Frontend
```powershell
# Start dev server
npm run dev

# Build for production
npm run build

# Type check
npm run type-check
```

---

## 📝 Environment Variables

### Backend (`.env` or set in terminal)
```
FLASK_ENV=development
DATABASE_URL=postgresql://user:pass@localhost:5432/metadb
# OR
DATABASE_URL=sqlite:///dev.db
SECRET_KEY=your-secret-key-here
```

### Frontend (`.env`)
```
VITE_API_URL=http://localhost:5000
```

---

## 🐛 Troubleshooting

**Backend not starting?**
- Check Python version: `python --version`
- Activate virtual environment
- Install requirements: `pip install -r requirements.txt`

**Frontend not starting?**
- Check Node version: `node --version`
- Delete `node_modules` and reinstall: `npm install --legacy-peer-deps`
- Clear npm cache: `npm cache clean --force`

**Can't login?**
- Make sure backend is running on port 5000
- Check `.env` file has correct `VITE_API_URL`
- Create admin user with `python add_admin.py`

**Database errors?**
- Run migrations: `flask db upgrade`
- Check DATABASE_URL is set correctly

---

## 📚 Documentation

- **Complete Backend API**: `BACKEND_ARCHITECTURE.md`
- **Frontend Guide**: `Frontend/FRONTEND_IMPLEMENTATION_GUIDE.md`
- **Project Summary**: `PROJECT_SUMMARY.md`
- **Setup Instructions**: `SETUP_GUIDE.md`

---

## 🎯 Next Steps

1. **Explore the app** - Create schemas, add fields, create metadata
2. **Check the docs** - Read architecture guides
3. **Add features** - Implement version timeline, rollback UI, analytics
4. **Deploy** - Build for production and deploy to cloud

---

**🎉 You're all set! Start exploring MetaDB!**

For issues or questions, check the documentation files listed above.
