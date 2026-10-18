from copy import deepcopy
from datetime import date, datetime
from uuid import uuid4

from backend.auth import hash_password, verify_password
from backend.database import get_falkordb_connection

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
        "attendance.read", "attendance.write",
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
        "id": "INCIDENT001",
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
        "id": "INCIDENT002",
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
        "date": "2026-10-18",
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
        "date": "2026-10-18",
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
        "date": "2026-10-18",
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
    {"id": "hol-001", "holiday_name": "Dussehra", "year": 2026, "holiday_date": "2026-10-21", "holiday_type": "PUBLIC", "is_deleted": False},
    {"id": "hol-002", "holiday_name": "Diwali", "year": 2026, "holiday_date": "2026-11-08", "holiday_type": "PUBLIC", "is_deleted": False},
    {"id": "hol-003", "holiday_name": "Annual Leave", "year": 2025, "holiday_date": "2025-12-25", "holiday_type": "COMPANY", "is_deleted": False},
]


def _coerce_permission_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value)]


def _load_role_permissions_from_graph(role):
    try:
        graph = get_falkordb_connection()
        result = graph.query(
            "MATCH (r:Role {name: $role}) RETURN coalesce(r.permissions, []) AS permissions",
            {"role": role},
        )
        if result.result_set and result.result_set[0]:
            permissions = result.result_set[0][0]
            return _coerce_permission_list(permissions)
    except Exception:
        pass
    return ROLE_PERMISSIONS.get(role, [])


def _load_tickets_from_graph():
    try:
        graph = get_falkordb_connection()
        result = graph.query(
            """
            MATCH (t:Ticket)
            WHERE coalesce(t.is_deleted, false) = false
            OPTIONAL MATCH (owner:User {email: t.user_email})
            OPTIONAL MATCH (owner)-[:REPORTS_TO]->(manager:User)
            RETURN t.id AS id,
                   coalesce(t.type, 'GENERAL') AS type,
                   coalesce(t.status, 'PENDING_MANAGER_APPROVAL') AS status,
                   coalesce(t.priority, 'MEDIUM') AS priority,
                   coalesce(t.user_email, '') AS user_email,
                   coalesce(t.comments, '') AS comments,
                   coalesce(t.created_at, timestamp()) AS created_at,
                   coalesce(t.updated_at, timestamp()) AS updated_at,
                   coalesce(t.created_by, '') AS created_by,
                   coalesce(t.updated_by, '') AS updated_by,
                   CASE
                       WHEN coalesce(t.assigned_to, '') <> '' THEN t.assigned_to
                       WHEN coalesce(owner.reporting_manager, '') <> '' THEN owner.reporting_manager
                       ELSE coalesce(manager.email, '')
                   END AS assigned_to
            ORDER BY t.created_at DESC
            """
        )
        tickets = []
        for row in result.result_set:
            tickets.append({
                "id": row[0],
                "type": row[1],
                "status": row[2],
                "priority": row[3],
                "user_email": row[4],
                "comments": row[5],
                "created_at": row[6],
                "updated_at": row[7],
                "created_by": row[8],
                "updated_by": row[9],
                "assigned_to": row[10],
                "is_deleted": False,
            })
        if tickets:
            return tickets
    except Exception:
        pass
    return [t for t in TICKETS if not t.get("is_deleted", False)]


def _load_projects_from_graph():
    try:
        graph = get_falkordb_connection()
        result = graph.query(
            """
            MATCH (p:Project)
            WHERE coalesce(p.is_deleted, false) = false
            RETURN p.id AS id,
                   coalesce(p.name, 'Project') AS name,
                   coalesce(p.client_name, '') AS client_name,
                   coalesce(p.cost, 0) AS cost,
                   coalesce(p.start_date, '') AS start_date,
                   coalesce(p.end_date, '') AS end_date,
                   coalesce(p.status, 'PENDING') AS status,
                   coalesce(p.created_by, '') AS created_by,
                   coalesce(p.updated_by, '') AS updated_by,
                   coalesce(p.comments, '') AS comments,
                   coalesce(p.created_at, timestamp()) AS created_at,
                   coalesce(p.updated_at, timestamp()) AS updated_at
            ORDER BY p.created_at DESC
            """
        )
        projects = []
        for row in result.result_set:
            projects.append({
                "id": row[0],
                "name": row[1],
                "client_name": row[2],
                "cost": row[3],
                "start_date": row[4],
                "end_date": row[5],
                "status": row[6],
                "created_by": row[7],
                "updated_by": row[8],
                "comments": row[9],
                "created_at": row[10],
                "updated_at": row[11],
                "is_deleted": False,
            })
        if projects:
            return projects
    except Exception:
        pass
    return [p for p in PROJECTS if not p.get("is_deleted", False)]


def _load_attendance_from_graph():
    try:
        graph = get_falkordb_connection()
        result = graph.query(
            """
            MATCH (a:Attendance)
            WHERE coalesce(a.is_deleted, false) = false
            RETURN a.id AS id,
                   coalesce(a.user_email, '') AS user_email,
                   coalesce(a.date, '') AS date,
                   coalesce(a.in_time, '') AS in_time,
                   coalesce(a.out_time, '') AS out_time,
                   coalesce(a.type, 'FULL_DAY') AS type,
                   coalesce(a.is_leave, false) AS is_leave,
                   coalesce(a.is_approved, true) AS is_approved,
                   coalesce(a.is_regularized, false) AS is_regularized,
                   coalesce(a.created_by, '') AS created_by,
                   coalesce(a.updated_by, '') AS updated_by,
                   coalesce(a.comments, '') AS comments
            ORDER BY a.date DESC
            """
        )
        attendance = []
        for row in result.result_set:
            attendance.append({
                "id": row[0],
                "user_email": row[1],
                "date": row[2],
                "in_time": row[3],
                "out_time": row[4],
                "type": row[5],
                "is_leave": bool(row[6]),
                "is_approved": bool(row[7]),
                "is_regularized": bool(row[8]),
                "created_by": row[9],
                "updated_by": row[10],
                "comments": row[11],
                "is_deleted": False,
            })
        if attendance:
            return attendance
    except Exception:
        pass
    return [a for a in ATTENDANCE if not a.get("is_deleted", False)]


def _load_users_from_graph():
    try:
        graph = get_falkordb_connection()
        result = graph.query(
            """
            MATCH (u:User)
            OPTIONAL MATCH (u)-[:HAS_ROLE]->(r:Role)
            RETURN u.id AS id, u.email AS email, u.name AS name, u.password AS password,
                   coalesce(r.name, 'Employee') AS role,
                   coalesce(u.status, 'ACTIVE') AS status,
                   coalesce(u.mobile, '') AS mobile,
                   coalesce(u.address, '') AS address,
                   coalesce(u.created_at, timestamp()) AS created_at,
                   coalesce(u.updated_at, timestamp()) AS updated_at,
                   coalesce(u.is_deleted, false) AS is_deleted,
                   coalesce(u.comments, '') AS comments,
                   coalesce(u.created_by, '') AS created_by,
                   coalesce(u.updated_by, '') AS updated_by,
                   coalesce(u.reporting_manager, '') AS reporting_manager
            ORDER BY u.email
            """
        )
        users = []
        for row in result.result_set:
            user = {
                "id": row[0],
                "email": row[1],
                "name": row[2],
                "password": row[3],
                "role": row[4],
                "status": row[5],
                "mobile": row[6],
                "address": row[7],
                "created_at": row[8],
                "updated_at": row[9],
                "is_deleted": bool(row[10]),
                "comments": row[11],
                "created_by": row[12],
                "updated_by": row[13],
                "reporting_manager": row[14],
            }
            users.append(user)
        return users
    except Exception:
        return []


def _resolve_reporting_manager(value, fallback_email=None):
    if value is None or str(value).strip() == "":
        return (fallback_email or "").strip().lower()

    ref = str(value).strip()
    if "@" in ref:
        return ref.lower()

    for user in list_active_users():
        if user.get("id") == ref or user.get("email", "").lower() == ref.lower():
            return str(user.get("email", "")).lower()

    return (fallback_email or ref).strip().lower()


def list_active_users():
    graph_users = _load_users_from_graph()
    if graph_users:
        USER_CATALOG[:] = graph_users
    return [u for u in USER_CATALOG if not u.get("is_deleted", False)]


def find_user_by_email(email):
    normalized = (email or "").strip().lower()
    for user in list_active_users():
        if user["email"].lower() == normalized:
            return deepcopy(user)
    return None


def validate_demo_credentials(email, password):
    user = find_user_by_email(email)
    if not user:
        return None
    stored = user.get("password")
    if stored == password:
        return deepcopy(user)
    try:
        if verify_password(password, stored):
            return deepcopy(user)
    except Exception:
        pass
    return None


def get_role_permissions(role):
    permissions = _load_role_permissions_from_graph(role)
    if permissions:
        return permissions
    return ROLE_PERMISSIONS.get(role, [])


def get_user_summary(role):
    users = list_active_users()
    tickets = _load_tickets_from_graph()
    attendance = _load_attendance_from_graph()
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
        return {"employees": counts["employees"], "pending_tickets": len([t for t in tickets if not t.get("is_deleted", False) and t.get("status") == "PENDING_MANAGER_APPROVAL"]) }
    return {"attendance_records": len([a for a in attendance if not a.get("is_deleted", False) and a.get("user_email") == "employee@company.com"]) }


def get_dashboard_for_user(email, role):
    user = find_user_by_email(email) or {"name": "User", "role": role}
    summary = get_user_summary(role)
    tickets = _load_tickets_from_graph()
    projects = _load_projects_from_graph()
    attendance = _load_attendance_from_graph()
    holidays = [h for h in HOLIDAYS if not h["is_deleted"]]
    users = list_active_users()

    if role == "Manager":
        team_employees = [
            u for u in users
            if u["role"] == "Employee" and (u.get("reporting_manager") or u.get("created_by") or "").lower() == email.lower()
        ]
        my_projects = [p for p in projects if p.get("created_by") == email or p.get("updated_by") == email]
        my_tickets = [
            t for t in tickets
            if t.get("user_email") in {u["email"] for u in team_employees} or t.get("created_by") == email
        ]
        team_attendance = [a for a in attendance if a.get("user_email") in {u["email"] for u in team_employees}]
        my_attendance = [a for a in attendance if a.get("user_email") == email]
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
                    {"label": "My Team", "value": len(team_employees)},
                    {"label": "Pending Tickets", "value": len([t for t in my_tickets if t["status"] == "PENDING_MANAGER_APPROVAL"])},
                    {"label": "Project Count", "value": len(my_projects)},
                    {"label": "Attendance Logs", "value": len(team_attendance)},
                ]
            },
            "admins": [],
            "managers": [u for u in users if u["role"] == "Manager" and u["email"] == email],
            "employees": team_employees,
            "projects": my_projects,
            "tickets": my_tickets,
            "attendance": team_attendance,
            "my_attendance": my_attendance,
            "holidays": holidays,
            "access_controls": {
                "can_manage_users": "users.write" in ROLE_PERMISSIONS.get(role, []),
                "can_manage_roles": "roles.write" in ROLE_PERMISSIONS.get(role, []),
                "can_approve_tickets": "tickets.write" in ROLE_PERMISSIONS.get(role, []),
                "can_manage_projects": "projects.write" in ROLE_PERMISSIONS.get(role, []),
            },
        }

    if role == "Employee":
        own_tickets = [t for t in tickets if t.get("user_email") == email or t.get("created_by") == email]
        own_attendance = [a for a in attendance if a.get("user_email") == email]
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
                    {"label": "My Tickets", "value": len(own_tickets)},
                    {"label": "My Attendance", "value": len(own_attendance)},
                    {"label": "My Projects", "value": len(projects)},
                    {"label": "Holidays", "value": len(holidays)},
                ]
            },
            "admins": [],
            "managers": [],
            "employees": [u for u in users if u["email"] == email],
            "projects": projects,
            "tickets": own_tickets,
            "attendance": own_attendance,
            "my_attendance": own_attendance,
            "holidays": holidays,
            "access_controls": {
                "can_manage_users": False,
                "can_manage_roles": False,
                "can_approve_tickets": False,
                "can_manage_projects": False,
            },
        }

    own_attendance = [a for a in attendance if a.get("user_email") == email]
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
        "my_attendance": own_attendance,
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
    email = (payload.get("email") or "").strip()
    if not email:
        raise ValueError("Email is required for user creation.")
    if find_user_by_email(email):
        raise ValueError("This email is already in use. Please provide a unique email address.")

    reporting_manager = _resolve_reporting_manager(
        payload.get("reporting_manager") or payload.get("reporting_manager_email") or payload.get("reporting_manager_id"),
        created_by,
    )

    user = {
        "id": str(uuid4()),
        "name": payload.get("name", "New User"),
        "email": email,
        "password": payload.get("password", "Welcome@123"),
        "role": payload.get("role", "Employee"),
        "status": payload.get("status", "ACTIVE"),
        "mobile": payload.get("mobile", ""),
        "address": payload.get("address", ""),
        "reporting_manager": reporting_manager,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "created_by": created_by,
        "updated_by": created_by,
        "is_deleted": False,
        "comments": payload.get("comments", "Created from enterprise workflow"),
    }
    try:
        graph = get_falkordb_connection()
        graph.query(
            """
            MERGE (u:User {email: $email})
            SET u.id = $id,
                u.name = $name,
                u.password = $password,
                u.status = $status,
                u.mobile = $mobile,
                u.address = $address,
                u.reporting_manager = $reporting_manager,
                u.created_at = $created_at,
                u.updated_at = $updated_at,
                u.is_deleted = false,
                u.comments = $comments,
                u.created_by = $created_by,
                u.updated_by = $updated_by
            WITH u
            MERGE (r:Role {name: $role})
            SET r.permissions = $permissions
            MERGE (u)-[:HAS_ROLE]->(r)
            WITH u
            OPTIONAL MATCH (manager:User {email: $reporting_manager})
            WHERE manager.email <> u.email
            MERGE (u)-[:REPORTS_TO]->(manager)
            """,
            {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "password": hash_password(user["password"]),
                "status": user["status"],
                "mobile": user["mobile"],
                "address": user["address"],
                "reporting_manager": user["reporting_manager"],
                "created_at": user["created_at"],
                "updated_at": user["updated_at"],
                "comments": user["comments"],
                "created_by": user["created_by"],
                "updated_by": user["updated_by"],
                "role": user["role"],
                "permissions": get_role_permissions(user["role"]),
            },
        )
    except Exception:
        raise
    USER_CATALOG.append(user)
    return deepcopy(user)


def update_user_record(user_id, payload, updated_by):
    for user in USER_CATALOG:
        if user["id"] == user_id:
            updated_email = payload.get("email", user["email"])
            if "password" in payload and payload.get("password"):
                user["password"] = payload["password"]
            if "reporting_manager" in payload or "reporting_manager_email" in payload or "reporting_manager_id" in payload:
                user["reporting_manager"] = _resolve_reporting_manager(
                    payload.get("reporting_manager") or payload.get("reporting_manager_email") or payload.get("reporting_manager_id"),
                    user.get("reporting_manager") or updated_by,
                )
            user.update({
                "name": payload.get("name", user["name"]),
                "email": updated_email,
                "role": payload.get("role", user["role"]),
                "status": payload.get("status", user["status"]),
                "mobile": payload.get("mobile", user.get("mobile", "")),
                "address": payload.get("address", user.get("address", "")),
                "comments": payload.get("comments", user.get("comments", "")),
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "updated_by": updated_by,
            })
            try:
                graph = get_falkordb_connection()
                graph.query(
                    """
                    MATCH (u:User {id: $id})
                    SET u.name = $name,
                        u.email = $email,
                        u.status = $status,
                        u.mobile = $mobile,
                        u.address = $address,
                        u.reporting_manager = $reporting_manager,
                        u.comments = $comments,
                        u.updated_at = $updated_at,
                        u.updated_by = $updated_by
                    WITH u
                    OPTIONAL MATCH (u)-[r:HAS_ROLE]->(:Role)
                    DELETE r
                    WITH u
                    MERGE (r:Role {name: $role})
                    CREATE (u)-[:HAS_ROLE]->(r)
                    WITH u
                    OPTIONAL MATCH (u)-[old:REPORTS_TO]->(:User)
                    DELETE old
                    WITH u
                    OPTIONAL MATCH (manager:User {email: $reporting_manager})
                    WHERE manager.email <> u.email
                    MERGE (u)-[:REPORTS_TO]->(manager)
                    """,
                    {
                        "id": user_id,
                        "name": user["name"],
                        "email": user["email"],
                        "status": user["status"],
                        "mobile": user.get("mobile", ""),
                        "address": user.get("address", ""),
                        "reporting_manager": user.get("reporting_manager") or updated_by,
                        "comments": user.get("comments", ""),
                        "updated_at": user["updated_at"],
                        "updated_by": updated_by,
                        "role": user["role"],
                    },
                )
                if "password" in payload and payload.get("password"):
                    graph.query(
                        "MATCH (u:User {id: $id}) SET u.password = $password",
                        {"id": user_id, "password": hash_password(payload["password"])},
                    )
            except Exception:
                pass
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
    try:
        graph = get_falkordb_connection()
        graph.query(
            """
            CREATE (p:Project {
                id: $id,
                name: $name,
                client_name: $client_name,
                cost: $cost,
                start_date: $start_date,
                end_date: $end_date,
                status: $status,
                is_deleted: false,
                created_by: $created_by,
                updated_by: $updated_by,
                comments: $comments,
                created_at: $created_at,
                updated_at: $updated_at
            })
            """,
            {
                "id": project["id"],
                "name": project["name"],
                "client_name": project["client_name"],
                "cost": project["cost"],
                "start_date": project["start_date"],
                "end_date": project["end_date"],
                "status": project["status"],
                "created_by": project["created_by"],
                "updated_by": project["updated_by"],
                "comments": project["comments"],
                "created_at": project["created_at"],
                "updated_at": project["updated_at"],
            },
        )
    except Exception:
        pass
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


def generate_ticket_id():
    try:
        graph = get_falkordb_connection()
        result = graph.query("MATCH (t:Ticket) RETURN count(t) AS cnt")
        count = int(result.result_set[0][0]) if result.result_set else 0
    except Exception:
        count = len([t for t in TICKETS if not t.get("is_deleted", False)])
    return f"INCIDENT{count + 1:03d}"


def create_ticket_record(payload, created_by):
    ticket_id = payload.get("id") or generate_ticket_id()
    user_email = payload.get("user_email", created_by)
    user = find_user_by_email(user_email)
    assigned_to = payload.get("assigned_to") or (user or {}).get("reporting_manager", "")
    ticket = {
        "id": ticket_id,
        "type": payload.get("type", "GENERAL"),
        "status": payload.get("status", "PENDING_MANAGER_APPROVAL"),
        "priority": payload.get("priority", "MEDIUM"),
        "user_email": user_email,
        "assigned_to": assigned_to,
        "comments": payload.get("comments", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "created_by": created_by,
        "updated_by": created_by,
        "is_deleted": False,
    }
    try:
        graph = get_falkordb_connection()
        graph.query(
            """
            MERGE (t:Ticket {id: $id})
            SET t.type = $type,
                t.status = $status,
                t.priority = $priority,
                t.user_email = $user_email,
                t.assigned_to = $assigned_to,
                t.comments = $comments,
                t.created_by = $created_by,
                t.updated_by = $updated_by,
                t.created_at = $created_at,
                t.updated_at = $updated_at,
                t.is_deleted = false
            """,
            {
                "id": ticket["id"],
                "type": ticket["type"],
                "status": ticket["status"],
                "priority": ticket["priority"],
                "user_email": ticket["user_email"],
                "assigned_to": ticket["assigned_to"],
                "comments": ticket["comments"],
                "created_by": ticket["created_by"],
                "updated_by": ticket["updated_by"],
                "created_at": ticket["created_at"],
                "updated_at": ticket["updated_at"],
            },
        )
    except Exception:
        raise
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
    return _load_projects_from_graph()


def list_tickets_for_role(role, user_email=None):
    tickets = _load_tickets_from_graph()
    if not user_email or role == "SuperAdmin":
        return tickets

    email = user_email.strip().lower()
    if role == "Admin":
        return [
            ticket for ticket in tickets
            if email in {
                (ticket.get("user_email") or "").lower(),
                (ticket.get("created_by") or "").lower(),
                (ticket.get("assigned_to") or "").lower(),
            }
        ]
    if role == "Manager":
        return [
            ticket for ticket in tickets
            if (ticket.get("assigned_to") or "").lower() == email
        ]
    if role == "Employee":
        return [
            ticket for ticket in tickets
            if (ticket.get("user_email") or "").lower() == email
        ]
    return []


def approve_ticket_record(ticket_id, approved_by, role):
    if role not in {"SuperAdmin", "Admin", "Manager"}:
        raise PermissionError("This role cannot approve tickets.")

    graph = get_falkordb_connection()
    result = graph.query(
        """
        MATCH (t:Ticket {id: $id})
        OPTIONAL MATCH (owner:User {email: t.user_email})
        OPTIONAL MATCH (owner)-[:REPORTS_TO]->(manager:User)
        WITH t, CASE
            WHEN coalesce(t.assigned_to, '') <> '' THEN t.assigned_to
            WHEN coalesce(owner.reporting_manager, '') <> '' THEN owner.reporting_manager
            ELSE coalesce(manager.email, '')
        END AS assigned_to
        WHERE coalesce(t.status, 'PENDING_MANAGER_APPROVAL') = 'PENDING_MANAGER_APPROVAL'
          AND ($role <> 'Manager' OR assigned_to = $approver)
        SET t.status = 'APPROVED',
            t.updated_by = $approver,
            t.updated_at = $updated_at
        RETURN t.id AS id
        """,
        {
            "id": ticket_id,
            "role": role,
            "approver": approved_by.strip().lower(),
            "updated_at": datetime.utcnow().isoformat() + "Z",
        },
    )
    if result.result_set:
        for ticket in TICKETS:
            if ticket.get("id") == ticket_id:
                ticket["status"] = "APPROVED"
                ticket["updated_by"] = approved_by
                break
        return ticket_id

    existing = graph.query("MATCH (t:Ticket {id: $id}) RETURN t.id", {"id": ticket_id})
    if not existing.result_set:
        raise LookupError(f"Ticket {ticket_id} was not found.")
    raise PermissionError("Ticket is not pending or is not assigned to this manager.")


def upsert_attendance_for_user(email, in_time=None, out_time=None, comment=None):
    if not email:
        raise ValueError("User email is required for attendance capture.")

    today = date.today().isoformat()
    normalized_email = str(email).strip().lower()
    record = next(
        (
            item for item in ATTENDANCE
            if not item.get("is_deleted", False)
            and str(item.get("user_email", "")).strip().lower() == normalized_email
            and str(item.get("date", "")).strip() == today
        ),
        None,
    )

    current_time = datetime.utcnow().strftime("%H:%M")
    if record is None:
        record = {
            "id": f"att-{uuid4().hex[:8]}",
            "user_email": email,
            "date": today,
            "in_time": in_time or current_time,
            "out_time": out_time or "",
            "type": "FULL_DAY",
            "is_leave": False,
            "is_approved": True,
            "is_regularized": False,
            "is_deleted": False,
            "created_by": email,
            "updated_by": email,
            "comments": comment or "Attendance captured on login/logout",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        ATTENDANCE.append(record)
    else:
        if in_time and not record.get("in_time"):
            record["in_time"] = in_time
        if out_time:
            record["out_time"] = out_time
        if comment:
            record["comments"] = comment
        record["updated_by"] = email
        record["updated_at"] = datetime.utcnow().isoformat() + "Z"

    try:
        graph = get_falkordb_connection()
        graph.query(
            """
            MERGE (a:Attendance {user_email: $user_email, date: $date})
            SET a.id = $id,
                a.in_time = $in_time,
                a.out_time = $out_time,
                a.type = $type,
                a.is_leave = $is_leave,
                a.is_approved = $is_approved,
                a.is_regularized = $is_regularized,
                a.created_by = coalesce(a.created_by, $created_by),
                a.updated_by = $updated_by,
                a.comments = $comments,
                a.updated_at = $updated_at,
                a.is_deleted = false
            """,
            {
                "user_email": email,
                "date": today,
                "id": record["id"],
                "in_time": record.get("in_time", ""),
                "out_time": record.get("out_time", ""),
                "type": record.get("type", "FULL_DAY"),
                "is_leave": bool(record.get("is_leave", False)),
                "is_approved": bool(record.get("is_approved", True)),
                "is_regularized": bool(record.get("is_regularized", False)),
                "created_by": record.get("created_by", email),
                "updated_by": email,
                "comments": record.get("comments", "Attendance captured on login/logout"),
                "updated_at": record["updated_at"],
            },
        )
    except Exception:
        pass

    return deepcopy(record)


def list_attendance_for_role(role):
    return _load_attendance_from_graph()


def create_holiday_record(payload, created_by):
    if created_by is None:
        raise PermissionError("Only admin and super admin can add holidays.")
    holiday_name = (payload.get("holiday_name") or payload.get("name") or "").strip()
    if not holiday_name:
        raise ValueError("Holiday name is required.")

    holiday = {
        "id": payload.get("id") or f"hol-{uuid4().hex[:8]}",
        "holiday_name": holiday_name,
        "year": int(payload.get("year") or datetime.utcnow().year),
        "holiday_date": payload.get("holiday_date") or "",
        "holiday_type": payload.get("holiday_type", "PUBLIC"),
        "created_by": created_by,
        "updated_by": created_by,
        "is_deleted": False,
    }
    HOLIDAYS.append(holiday)
    return deepcopy(holiday)


def list_holidays_for_role(role):
    return [h for h in HOLIDAYS if not h.get("is_deleted", False)]
