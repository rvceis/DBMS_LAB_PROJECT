# 🎨 MetaDB Frontend - Modern React Application

A premium dark-themed frontend for the MetaDB dynamic schema management platform, built with React 18, TypeScript, Material-UI, and Zustand.

## ✨ Features Implemented

- ✅ **Authentication**: JWT-based login with role-based access control
- ✅ **Dashboard**: Real-time stats and recent activity overview
- ✅ **Schema Manager**: Complete CRUD for schemas and fields
- ✅ **Metadata Records**: Dynamic forms based on schema definitions
- ✅ **Premium Dark/Light Theme**: Glassmorphic design with Inter font
- ✅ **State Management**: Zustand stores for predictable state
- ✅ **Responsive Design**: Mobile-first with MUI Grid
- ✅ **Toast Notifications**: Real-time user feedback
- ✅ **Full TypeScript**: Type-safe development

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

App runs at **http://localhost:5173**

## 🔐 Demo Credentials

```
Email: admin@test.com
Password: password
```

## 📊 Tech Stack

- React 18.3 + TypeScript 5.3
- Material-UI 5.15 (Premium theme)
- Zustand 4.4 (State management)
- React Router 7.1
- React Hook Form + Zod
- Recharts (Charts)
- Vite 7.2 (Build tool)

## 🎯 Key Pages

1. **Dashboard** (`/dashboard`) - Stats cards + recent records
2. **Schemas** (`/schemas`) - Schema/field CRUD with visual editor
3. **Metadata** (`/metadata`) - Dynamic forms + data table
4. **Login** (`/login`) - JWT authentication

## 📁 Project Structure

```
src/
├── components/layout/    # AppShell, Header, Sidebar
├── components/common/    # LoadingSpinner, ConfirmDialog, EmptyState
├── pages/                # Dashboard, Schemas, Metadata, Login
├── stores/               # Zustand stores (auth, schema, metadata, ui)
├── theme/                # MUI custom theme
└── App.tsx               # Routes
```

## 🔧 Environment Setup

Create `.env`:
```
VITE_API_URL=http://localhost:5000
```

## 📝 Available Scripts

```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run preview      # Preview build
npm run type-check   # TypeScript check
npm run lint         # ESLint
```

## 🎨 Theme Colors

- **Primary**: #6366F1 (Indigo)
- **Secondary**: #10B981 (Emerald)
- **Dark BG**: #0F172A (Slate 900)
- **Light BG**: #F8FAFC (Slate 50)

## 📦 Build for Production

```bash
npm run build
# Output: build/
```

Deploy to Vercel, Netlify, or Cloudflare Pages.

## 🔄 API Integration

All stores use Zustand + fetch API with automatic JWT headers. Token stored in localStorage.

## 📚 Documentation

See `FRONTEND_IMPLEMENTATION_GUIDE.md` for complete architecture details.

---

**Built with ❤️ for MetaDB - Dynamic Schema Management Platform**

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
