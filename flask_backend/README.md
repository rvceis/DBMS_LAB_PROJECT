# MMS Flask Backend (MVP)

This is a minimal Flask backend scaffold for the Metadata Management System (MMS) MVP.

Quick start (local development):

1. Create a virtualenv and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and adjust values.

3. Run database migrations (after installing `alembic` and initializing):

```powershell
flask db init
flask db migrate -m "init"
flask db upgrade
```

4. Start app:

```powershell
python main.py
```

Or with docker-compose:

```powershell
docker-compose up --build
```

Endpoints:

- `POST /auth/register` — register user
- `POST /auth/login` — login
- `GET /users/me` — get current user
- `GET /asset-types` — list types
- `POST /asset-types` — create (admin)
- `GET /schemas` — list schemas
- `POST /schemas` — create schema (admin/editor)
- `GET /metadata` — list metadata
- `POST /metadata` — create metadata (admin/editor)
