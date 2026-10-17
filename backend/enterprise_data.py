from copy import deepcopy
from datetime import datetime
from uuid import uuid4

ROLE_PERMISSIONS = {
    "SuperAdmin": [
        "users.read", "users.write", "users.delete",
        "roles.read", "roles.write", "roles.delete",
        "permissions.read", "permissions.write",
        "projects.read", "projects.write", "projects.delete",
        "tickets.read", "tickets.write", "tickets.delete",
        "attendance.read", "attendance.write",
        "salary.read", "salary.write",
        "holidays.read", "holidays.write",
        "assets.read", "assets.write",
        "travel.read", "travel.write",
        "team.read", "team.write",
        "dashboard.read"
    ],
    "Admin": [
        "users.read", "users.write",
        "roles.read",
        "permissions.read",
        "projects.read", "projects.write",
        "tickets.read", "tickets.write",
        "attendance.read", "attendance.write",
        "team.read",
        "dashboard.read"
    ],
    "Manager": [
        "users.read", "users.write",
        "projects.read", "projects.write",
        "tickets.read", "tickets.write",
        "attendance.read", "attendance.write",
        "team.read",
        "dashboard.read"
    ],
    "Employee": [
        "tickets.read", "tickets.write",
        "attendance.read",
        "projects.read",
        "holidays.read",
        "dashboard.read"
    ],
}

USER_CATALOG = [
    {
        "id": "usr-super-001",
        "name": "Super Admin",
        "email": "superadmin@company.com",
        "password": "SuperAdmin@123",
        "role": "SuperAdmin",
        "status": "ACTIVE",
        "mobile": "+1-555-1001",
        "address": "HQ, New York",
        "created_at": "2024-01-10T09:12:00Z",
        "updated_at": "2024-01-10T09:12:00Z",
        "is_deleted": False,
        "comments": "System owner"
    },
    {
        "id": "usr-admin-001",
        "name": "Operations Admin",
        "email": "admin@company.com",
        "password": "Admin@123",
        "role": "Admin",
        "status": "ACTIVE",
        "mobile": "+1-555-1002",
        "address": "Operations, Chicago",
        "created_at": "2024-02-05T10:00:00Z",
        "updated_at": "2024-02-05T10:00:00Z",
        "is_deleted": False,
        "comments": "Admin rights"
    },
    {
        "id": "usr-manager-001",
        "name": "Project Manager",
        "email": "manager@company.com",
        "password": "Manager@123",
        "role": "Manager",
        "status": "ACTIVE",
        "mobile": "+1-555-1003",
        "address": "Delivery, Austin",
        "created_at": "2024-03-03T12:00:00Z",
        "updated_at": "2024-03-03T12:00:00Z",
        "is_deleted": False,
        "comments": "Approves tickets"
    },
    {
        "id": "usr-emp-001",
        "name": "Employee User",
        "email": "employee@company.com",
        "password": "Employee@123",
        "role": "Employee",
        "status": "ACTIVE",
        "mobile": "+1-555-1004",
        "address": "Engineering, Seattle",
        "created_at": "2024-04-12T08:00:00Z",
        "updated_at": "2024-04-12T08:00:00Z",
        "is_deleted": False,
        "comments": "Regular employee"
    },
]

PROJECTS = [
    {
        "id": "prj-001",
        "name": "Enterprise Brain",
        "client_name": "Internal Platform",
        "cost": 250000,
        "start_date": "2025-01-01",
        "end_date": "2025-06-30",
        "status": "ACTIVE",
        "is_deleted": False,
        "created_by": "superadmin@company.com",
        "updated_by": "superadmin@company.com",
        "comments": "Core internal productivity platform",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    },
    {
        "id": "prj-002",
        "name": "Travel Automation",
        "client_name": "Operations",
        "cost": 90000,
        "start_date": "2025-02-15",
        "end_date": "2025-05-15",
        "status": "PENDING",
        "is_deleted": False,
        "created_by": "manager@company.com",
        "updated_by": "manager@company.com",
        "comments": "Cab and travel optimization",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    },
]

TICKETS = [
    {
        "id": "tik-001",
        "type": "ASSET_ALLOCATION",
        "status": "PENDING_MANAGER_APPROVAL",
        "priority": "HIGH",
        "user_email": "employee@company.com",
        "comments": "Need new laptop for project work",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "created_by": "employee@company.com",
        "updated_by": "manager@company.com",
        "is_deleted": False,
    },
    {
        "id": "tik-002",
        "type": "ATTENDANCE_REGULARIZATION",
        "status": "APPROVED",
        "priority": "MEDIUM",
        "user_email": "employee@company.com",
        "comments": "Late arrival due to traffic",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "created_by": "employee@company.com",
        "updated_by": "manager@company.com",
        "is_deleted": False,
    },
]

ATTENDANCE = [
    {
        "id": "att-001",
        "user_email": "employee@company.com",
        "date": "2025-10-17",
        "in_time": "09:00",
        "out_time": "18:30",
        "type": "FULL_DAY",
        "is_leave": False,
        "is_approved": True,
        "is_regularized": False,
        "is_deleted": False,
        "created_by": "manager@company.com",
        "updated_by": "manager@company.com",
        "comments": "Present",
    },
    {
        "id": "att-002",
        "user_email": "manager@company.com",
        "date": "2025-10-17",
        "in_time": "08:50",
        "out_time": "18:00",
        "type": "FULL_DAY",
        "is_leave": False,
        "is_approved": True,
        "is_regularized": False,
        "is_deleted": False,
        "created_by": "superadmin@company.com",
        "updated_by": "superadmin@company.com",
        "comments": "Team review",
    },
    {
        "id": "att-003",
        "user_email": "admin@company.com",
        "date": "2025-10-17",
        "in_time": "09:15",
        "out_time": "18:15",
        "type": "FULL_DAY",
        "is_leave": False,
        "is_approved": True,
        "is_regularized": False,
        "is_deleted": False,
        "created_by": "superadmin@company.com",
        "updated_by": "superadmin@company.com",
        "comments": "Operations monitoring",
    },
]

HOLIDAYS = [
    {"id": "hol-001", "holiday_name": "Diwali", "year": 2025, "holiday_type": "PUBLIC", "is_deleted": False},
    {"id": "hol-002", "holiday_name": "Christmas", "year": 2025, "holiday_type": "PUBLIC", "is_deleted": False},
    {"id": "hol-003", "holiday_name": "Annual Leave", "year": 2025, "holiday_type": "COMPANY", "is_deleted": False},
]


def list_active_users():
    return [u for u in USER_CATALOG if not u.get("is_deleted", False)]


def find_user_by_email(email):
    normalized = (email or "").strip().lower()
    for user in list_active_users():
        if user["email"].lower() == normalized:
            return deepcopy(user)
    return None


def validate_demo_credentials(email, password):
    user = find_user_by_email(email)
    if user and user.get("password") == password:
        return deepcopy(user)
    return None


def get_role_permissions(role):
    return ROLE_PERMISSIONS.get(role, [])


def get_user_summary(role):
    users = list_active_users()
    counts = {
        "total_users": len(users),
        "active_admins": sum(1 for u in users if u["role"] in {"SuperAdmin", "Admin"}),
        "managers": sum(1 for u in users if u["role"] == "Manager"),
        "employees": sum(1 for u in users if u["role"] == "Employee"),
    }
    if role == "SuperAdmin":
        return counts
    if role == "Admin":
        return {"total_users": counts["total_users"], "managers": counts["managers"], "employees": counts["employees"]}
    if role == "Manager":
        return {"employees": counts["employees"], "pending_tickets": len([t for t in TICKETS if not t["is_deleted"] and t["status"] == "PENDING_MANAGER_APPROVAL"]) }
    return {"attendance_records": len([a for a in ATTENDANCE if not a["is_deleted"] and a["user_email"] == "employee@company.com"]) }


def get_dashboard_for_user(email, role):
    user = find_user_by_email(email) or {"name": "User", "role": role}
    summary = get_user_summary(role)
    tickets = [t for t in TICKETS if not t["is_deleted"]]
    projects = [p for p in PROJECTS if not p["is_deleted"]]
    attendance = [a for a in ATTENDANCE if not a["is_deleted"]]
    holidays = [h for h in HOLIDAYS if not h["is_deleted"]]
    users = list_active_users()

    return {
        "user": {
            "name": user.get("name", "User"),
            "email": user.get("email", email),
            "role": role,
            "status": user.get("status", "ACTIVE"),
        },
        "permissions": ROLE_PERMISSIONS.get(role, []),
        "summary": {
            "cards": [
                {"label": "Total Users", "value": summary.get("total_users", len(users))},
                {"label": "Active Admins", "value": summary.get("active_admins", 0)},
                {"label": "Pending Tickets", "value": len([t for t in tickets if t["status"] == "PENDING_MANAGER_APPROVAL"])},
                {"label": "Projects", "value": len(projects)},
            ]
        },
        "admins": [u for u in users if u["role"] in {"SuperAdmin", "Admin"}],
        "managers": [u for u in users if u["role"] == "Manager"],
        "employees": [u for u in users if u["role"] == "Employee"],
        "projects": projects,
        "tickets": tickets,
        "attendance": attendance,
        "holidays": holidays,
        "access_controls": {
            "can_manage_users": "users.write" in ROLE_PERMISSIONS.get(role, []),
            "can_manage_roles": "roles.write" in ROLE_PERMISSIONS.get(role, []),
            "can_approve_tickets": "tickets.write" in ROLE_PERMISSIONS.get(role, []),
            "can_manage_projects": "projects.write" in ROLE_PERMISSIONS.get(role, []),
        },
    }


def get_users_for_role(role):
    users = list_active_users()
    if role == "SuperAdmin":
        return users
    if role == "Admin":
        return [u for u in users if u["role"] in {"Manager", "Employee"}]
    if role == "Manager":
        return [u for u in users if u["role"] == "Employee"]
    return [u for u in users if u["email"] == "employee@company.com"]


def create_user_record(payload, created_by):
    user = {
        "id": str(uuid4()),
        "name": payload.get("name", "New User"),
        "email": payload.get("email", f"user-{uuid4().hex[:6]}@company.com"),
        "password": payload.get("password", "Welcome@123"),
        "role": payload.get("role", "Employee"),
        "status": payload.get("status", "ACTIVE"),
        "mobile": payload.get("mobile", ""),
        "address": payload.get("address", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "created_by": created_by,
        "updated_by": created_by,
        "is_deleted": False,
        "comments": payload.get("comments", "Created from enterprise workflow"),
    }
    USER_CATALOG.append(user)
    return deepcopy(user)


def update_user_record(user_id, payload, updated_by):
    for user in USER_CATALOG:
        if user["id"] == user_id:
            user.update({
                "name": payload.get("name", user["name"]),
                "email": payload.get("email", user["email"]),
                "role": payload.get("role", user["role"]),
                "status": payload.get("status", user["status"]),
                "mobile": payload.get("mobile", user.get("mobile", "")),
                "address": payload.get("address", user.get("address", "")),
                "comments": payload.get("comments", user.get("comments", "")),
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "updated_by": updated_by,
            })
            return deepcopy(user)
    return None


def delete_user_record(user_id, deleted_by):
    for user in USER_CATALOG:
        if user["id"] == user_id:
            user["is_deleted"] = True
            user["updated_at"] = datetime.utcnow().isoformat() + "Z"
            user["updated_by"] = deleted_by
            return deepcopy(user)
    return None


def create_project_record(payload, created_by):
    project = {
        "id": str(uuid4()),
        "name": payload.get("name", "New Project"),
        "client_name": payload.get("client_name", "Internal Client"),
        "cost": payload.get("cost", 0),
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date"),
        "status": payload.get("status", "PENDING"),
        "is_deleted": False,
        "created_by": created_by,
        "updated_by": created_by,
        "comments": payload.get("comments", "") ,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    PROJECTS.append(project)
    return deepcopy(project)


def update_project_record(project_id, payload, updated_by):
    for project in PROJECTS:
        if project["id"] == project_id:
            project.update({
                "name": payload.get("name", project["name"]),
                "client_name": payload.get("client_name", project["client_name"]),
                "cost": payload.get("cost", project["cost"]),
                "start_date": payload.get("start_date", project["start_date"]),
                "end_date": payload.get("end_date", project["end_date"]),
                "status": payload.get("status", project["status"]),
                "comments": payload.get("comments", project.get("comments", "")),
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "updated_by": updated_by,
            })
            return deepcopy(project)
    return None


def delete_project_record(project_id, deleted_by):
    for project in PROJECTS:
        if project["id"] == project_id:
            project["is_deleted"] = True
            project["updated_at"] = datetime.utcnow().isoformat() + "Z"
            project["updated_by"] = deleted_by
            return deepcopy(project)
    return None


def create_ticket_record(payload, created_by):
    ticket = {
        "id": str(uuid4()),
        "type": payload.get("type", "GENERAL"),
        "status": payload.get("status", "PENDING_MANAGER_APPROVAL"),
        "priority": payload.get("priority", "MEDIUM"),
        "user_email": payload.get("user_email", created_by),
        "comments": payload.get("comments", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "created_by": created_by,
        "updated_by": created_by,
        "is_deleted": False,
    }
    TICKETS.append(ticket)
    return deepcopy(ticket)


def update_ticket_record(ticket_id, payload, updated_by):
    for ticket in TICKETS:
        if ticket["id"] == ticket_id:
            ticket.update({
                "type": payload.get("type", ticket["type"]),
                "status": payload.get("status", ticket["status"]),
                "priority": payload.get("priority", ticket["priority"]),
                "comments": payload.get("comments", ticket["comments"]),
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "updated_by": updated_by,
            })
            return deepcopy(ticket)
    return None


def delete_ticket_record(ticket_id, deleted_by):
    for ticket in TICKETS:
        if ticket["id"] == ticket_id:
            ticket["is_deleted"] = True
            ticket["updated_at"] = datetime.utcnow().isoformat() + "Z"
            ticket["updated_by"] = deleted_by
            return deepcopy(ticket)
    return None


def list_projects_for_role(role):
    return [p for p in PROJECTS if not p["is_deleted"]]


def list_tickets_for_role(role):
    return [t for t in TICKETS if not t["is_deleted"]]


def list_attendance_for_role(role):
    return [a for a in ATTENDANCE if not a["is_deleted"]]


def list_holidays_for_role(role):
    return [h for h in HOLIDAYS if not h["is_deleted"]]
