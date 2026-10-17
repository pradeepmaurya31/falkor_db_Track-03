# Maurya Corporation Enterprise Agent Platform

An enterprise-grade dashboard and AI assistant designed to manage people, projects, tickets, attendance, holidays, and role-based access for an organization.

This project combines a FastAPI backend, React + Vite frontend, and a graph-backed enterprise data model to provide role-aware dashboards and AI-driven workflows.

## Project overview

The application is built around a simple enterprise operating model:

- Users belong to roles such as SuperAdmin, Admin, Manager, and Employee
- Each role has specific permissions for reading and writing users, projects, tickets, attendance, and holidays
- A dashboard presents summary metrics and organization data based on the current user's access level
- A chat assistant can handle restricted operational requests and supports employee creation through approved roles
- The system supports FalkorDB-backed graph data and Gemini-based AI interactions

## Product specification

### Core modules

1. Authentication and authorization
   - Login using email + password
   - JWT token generation for authenticated sessions
   - Role-based permission enforcement on protected endpoints

2. Enterprise dashboard
   - Users summary cards
   - Projects list
   - Tickets overview
   - Attendance and holiday information
   - Role controls and permission visibility

3. AI assistant / chat layer
   - Natural language handling for tickets, attendance, project, and employee operations
   - Guardrails to restrict access according to user role
   - Employee creation through chat for authorized roles only

4. Enterprise data model
   - Role permissions map
   - In-memory enterprise catalog for users, projects, tickets, attendance, and holidays
   - Soft-delete behavior for user/project/ticket records

## Architecture

### Frontend
- Location: `frontend/`
- Stack: React, Vite
- Purpose: login page, enterprise dashboard, chat drawer, and role-based UI

### Backend
- Location: `backend/`
- Stack: FastAPI, JWT auth, Python
- Purpose: API layer, auth, permission checks, data access, AI orchestration

### Files and responsibilities

- `backend/main.py` — API routes and permission enforcement
- `backend/auth.py` — JWT generation and password verification
- `backend/database.py` — FalkorDB connection and initialization logic
- `backend/agent.py` — chat/AI intent classification, guardrails, and employee creation logic
- `backend/enterprise_data.py` — enterprise records, permissions, and dashboard data helpers
- `backend/env.example` — environment template for secrets and cloud configuration
- `frontend/src/App.jsx` — main dashboard and login UI
- `frontend/src/ChatDrawer.jsx` — chat interface

## Environment configuration

Create a local environment file in `backend/.env` by copying `backend/env.example`.

Example values:

```env
FALKORDB_HOST=your_falkordb_host
FALKORDB_PORT=58251
FALKORDB_USERNAME=your_falkordb_username
FALKORDB_PASSWORD=your_falkordb_password

GEMINI_API_KEY=your_gemini_api_key
GEMINI_PROJECT_ID=your_gemini_project_id
GEMINI_MODEL=gemini-3.8-flash

SUPER_ADMIN_EMAIL=superadmin@company.com
SUPER_ADMIN_PASSWORD=ChangeMe@123
```

Important:
- Never commit your real `.env` file to version control
- Use the sample file as a safe starting point

## Prerequisites

Before running the project, make sure you have:

- Python 3.10+
- Node.js 18+
- npm
- Access to a FalkorDB instance or a valid cloud configuration
- Gemini API access if AI chat features must run with live model calls

## Setup

### 1. Open the project folder

```powershell
cd C:\Users\pm923\OneDrive\Documents\Pradeep\Hackathon\folker_db_Track-03
```

### 2. Create and activate the Python virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install backend dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn python-dotenv PyJWT bcrypt google-genai langgraph
```

If your environment already has the project dependencies installed in `.venv`, you can skip this step.

### 4. Set up frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

### 5. Configure environment variables

```powershell
copy backend\env.example backend\.env
```

Then edit `backend/.env` and replace the placeholder values with your actual configuration.

## Start the app

### Start backend

From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

The backend will run on:
- http://localhost:8000

### Start frontend

```powershell
cd frontend
npm run dev
```

The frontend will run on:
- http://localhost:5173

## Stop the app

- In each running terminal, press `Ctrl + C`
- Or terminate the corresponding process from your terminal/IDE process list

## Demo credentials

The app includes default demo accounts for testing local functionality:

- Super Admin: `superadmin@company.com` / `SuperAdmin@123`
- Admin: `admin@company.com` / `Admin@123`
- Manager: `manager@company.com` / `Manager@123`
- Employee: `employee@company.com` / `Employee@123`

## Role permissions summary

- SuperAdmin: full access to users, roles, permissions, projects, tickets, attendance, and dashboard
- Admin: manages users and business workflows with restricted admin controls
- Manager: manages project, ticket, and team attendance workflows; can add employees in chat if granted
- Employee: access to own attendance, tickets, holidays, and project visibility

## Notes

- This project supports a graph-first enterprise model and can run in demo mode even without a live FalkorDB connection when fallback data is used.
- If live cloud services are unavailable, many features still render using the in-memory enterprise dataset.
- For production usage, validate the actual cloud environment and secure keys before deployment.

## Useful commands

```powershell
# run backend
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# run frontend
cd frontend
npm run dev

# build frontend for production
cd frontend
npm run build
```

## Summary

This application is a role-aware enterprise operations platform with AI assistance, dashboard analytics, and secure user management. Its purpose is to simulate a real company operating system where people, workflows, and decisions are connected in a single intelligent workspace.
