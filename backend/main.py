import asyncio
import os

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from dotenv import load_dotenv

load_dotenv()

from backend.agent import compiled_agent
from backend.auth import create_access_token, get_current_user, verify_password
from backend.database import get_falkordb_connection, init_super_admin
from backend.enterprise_data import (
    ROLE_PERMISSIONS,
    create_project_record,
    create_ticket_record,
    create_user_record,
    delete_project_record,
    delete_ticket_record,
    delete_user_record,
    get_dashboard_for_user,
    get_role_permissions,
    get_users_for_role,
    list_attendance_for_role,
    list_holidays_for_role,
    list_projects_for_role,
    list_tickets_for_role,
    update_project_record,
    update_ticket_record,
    update_user_record,
    validate_demo_credentials,
)

app = FastAPI(title="Enterprise Agentic Brain")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_permission(role: str, permission: str):
    permissions = set(ROLE_PERMISSIONS.get(role, []))
    if permission not in permissions:
        raise HTTPException(status_code=403, detail=f"Role '{role}' does not have access to '{permission}'.")


@app.on_event("startup")
def startup_event():
    init_super_admin()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Enterprise Agentic Brain"}


@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    demo_user = validate_demo_credentials(form_data.username, form_data.password)
    if demo_user:
        access_token = create_access_token({"sub": demo_user["email"], "role": demo_user["role"]})
        return {"access_token": access_token, "token_type": "bearer", "role": demo_user["role"]}

    try:
        graph = get_falkordb_connection()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    query = "MATCH (u:User {email: $email})-[:HAS_ROLE]->(r:Role) RETURN u.password, r.name"
    res = graph.query(query, {"email": form_data.username})

    if len(res.result_set) == 0:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    hashed_pwd, role = res.result_set[0]
    if not verify_password(form_data.password, hashed_pwd):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token({"sub": form_data.username, "role": role})
    return {"access_token": access_token, "token_type": "bearer", "role": role}


@app.get("/api/dashboard")
def get_dashboard(current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "dashboard.read")
    return get_dashboard_for_user(current_user["email"], current_user["role"])


@app.get("/api/roles")
def get_roles(current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "roles.read")
    return {"roles": {role: get_role_permissions(role) for role in sorted(ROLE_PERMISSIONS)}}


@app.get("/api/users")
def read_users(current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "users.read")
    return {"items": get_users_for_role(current_user["role"])}


@app.post("/api/users")
def create_user(payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "users.write")
    user = create_user_record(payload, current_user["email"])
    return {"message": "User created successfully", "user": user}


@app.patch("/api/users/{user_id}")
def update_user(user_id: str, payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "users.write")
    user = update_user_record(user_id, payload, current_user["email"])
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully", "user": user}


@app.delete("/api/users/{user_id}")
def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "users.delete")
    user = delete_user_record(user_id, current_user["email"])
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User soft deleted successfully", "user": user}


@app.get("/api/projects")
def read_projects(current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "projects.read")
    return {"items": list_projects_for_role(current_user["role"])}


@app.post("/api/projects")
def create_project(payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "projects.write")
    project = create_project_record(payload, current_user["email"])
    return {"message": "Project created successfully", "project": project}


@app.patch("/api/projects/{project_id}")
def update_project(project_id: str, payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "projects.write")
    project = update_project_record(project_id, payload, current_user["email"])
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project updated successfully", "project": project}


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "projects.delete")
    project = delete_project_record(project_id, current_user["email"])
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project soft deleted successfully", "project": project}


@app.get("/api/tickets")
def read_tickets(current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "tickets.read")
    return {"items": list_tickets_for_role(current_user["role"])}


@app.post("/api/tickets")
def create_ticket(payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "tickets.write")
    ticket = create_ticket_record(payload, current_user["email"])
    return {"message": "Ticket created successfully", "ticket": ticket}


@app.patch("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: str, payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "tickets.write")
    ticket = update_ticket_record(ticket_id, payload, current_user["email"])
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket updated successfully", "ticket": ticket}


@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "tickets.delete")
    ticket = delete_ticket_record(ticket_id, current_user["email"])
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket soft deleted successfully", "ticket": ticket}


@app.get("/api/attendance")
def read_attendance(current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "attendance.read")
    return {"items": list_attendance_for_role(current_user["role"])}


@app.get("/api/holidays")
def read_holidays(current_user: dict = Depends(get_current_user)):
    require_permission(current_user["role"], "holidays.read")
    return {"items": list_holidays_for_role(current_user["role"])}


@app.post("/api/chat/stream")
async def chat_stream(payload: dict = Body(...), current_user: dict = Depends(get_current_user)):
    message = payload.get("message")

    async def event_generator():
        yield f"data: [Agent] Analyzing query...\n\n"
        await asyncio.sleep(0.5)

        initial_state = {
            "user_email": current_user["email"],
            "user_role": current_user["role"],
            "message": message,
            "intent": "",
            "extracted_data": {},
            "chat_history": [],
            "response": "",
            "requires_approval": False,
        }

        result = compiled_agent.invoke(initial_state)
        yield f"data: {result['response']}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")