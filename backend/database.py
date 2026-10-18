import os
from pathlib import Path

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv(Path(__file__).resolve().parent / ".env")

from backend.auth import hash_password


def normalize_bcrypt_password(value):
    if value is None:
        return ""
    text = str(value)
    return text.encode("utf-8")[:72].decode("utf-8", "ignore")


def get_falkordb_connection():
    host = os.getenv("FALKORDB_HOST") or os.getenv("GRAPH_DB_HOST", "localhost")
    port = int(os.getenv("FALKORDB_PORT") or os.getenv("GRAPH_DB_PORT", 6379))
    username = os.getenv("GRAPH_DB_USERNAME") or os.getenv("FALKORDB_USERNAME")
    password = os.getenv("GRAPH_DB_PASSWORD") or os.getenv("FALKORDB_PASSWORD")
    ssl_enabled = os.getenv("GRAPH_DB_SSL", "false").lower() in {"1", "true", "yes"}

    if host in {"localhost", "127.0.0.1", "0.0.0.0"} and not os.getenv("FALKORDB_HOST") and not os.getenv("GRAPH_DB_HOST"):
        print("Warning: default local FalkorDB/Redis endpoint is being used. It may be non-persistent and data can be wiped on restart.")

    connection_kwargs = {
        "host": host,
        "port": port,
        "username": username or None,
        "password": password or None,
        "ssl": ssl_enabled,
    }

    try:
        db = FalkorDB(**connection_kwargs)
        return db.select_graph("EnterpriseBrain")
    except Exception as exc:
        raise RuntimeError(
            f"FalkorDB is not available at {host}:{port}. Start the FalkorDB/Redis service or set GRAPH_DB_HOST/GRAPH_DB_PORT/GRAPH_DB_USERNAME/GRAPH_DB_PASSWORD in the environment."
        ) from exc


def seed_demo_graph_data():
    try:
        graph = get_falkordb_connection()
    except RuntimeError as exc:
        print(f"Skipping demo graph seeding: {exc}")
        return

    demo_users = [
        {"id": "usr-super-001", "name": "Super Admin", "email": "superadmin@company.com", "password": "SuperAdmin@123", "role": "SuperAdmin"},
        {"id": "usr-admin-001", "name": "Operations Admin", "email": "admin@company.com", "password": "Admin@123", "role": "Admin"},
        {"id": "usr-manager-001", "name": "Project Manager", "email": "manager@company.com", "password": "Manager@123", "role": "Manager"},
        {"id": "usr-emp-001", "name": "Employee User", "email": "employee@company.com", "password": "Employee@123", "role": "Employee"},
    ]

    for user in demo_users:
        existing = graph.query("MATCH (u:User {email: $email}) RETURN count(u) AS cnt", {"email": user["email"]})
        if len(existing.result_set) == 0 or existing.result_set[0][0] == 0:
            graph.query(
                """
                CREATE (u:User {
                    id: $id,
                    email: $email,
                    name: $name,
                    password: $password,
                    status: 'ACTIVE',
                    mobile: '',
                    address: '',
                    created_at: timestamp(),
                    updated_at: timestamp(),
                    is_deleted: false,
                    comments: 'Seeded from startup'
                })
                WITH u
                MERGE (r:Role {name: $role})
                SET r.permissions = $permissions
                CREATE (u)-[:HAS_ROLE]->(r)
                """,
                {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "password": hash_password(user["password"]),
                    "role": user["role"],
                    "permissions": [
                        "users.read", "users.write" if user["role"] in {"SuperAdmin", "Admin", "Manager"} else "users.read",
                        "projects.read", "projects.write" if user["role"] in {"SuperAdmin", "Admin", "Manager"} else "projects.read",
                        "tickets.read", "tickets.write" if user["role"] in {"SuperAdmin", "Admin", "Manager"} else "tickets.read",
                        "attendance.read",
                        "dashboard.read",
                    ],
                },
            )

    for role_name, permissions in {
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
            "dashboard.read",
        ],
        "Admin": [
            "users.read", "users.write",
            "roles.read",
            "permissions.read",
            "projects.read", "projects.write",
            "tickets.read", "tickets.write",
            "attendance.read", "attendance.write",
            "team.read",
            "dashboard.read",
        ],
        "Manager": [
            "users.read", "users.write",
            "projects.read", "projects.write",
            "tickets.read", "tickets.write",
            "attendance.read", "attendance.write",
            "team.read",
            "dashboard.read",
        ],
        "Employee": [
            "tickets.read", "tickets.write",
            "attendance.read", "attendance.write",
            "projects.read",
            "holidays.read",
            "dashboard.read",
        ],
    }.items():
        graph.query(
            "MERGE (r:Role {name: $role}) SET r.permissions = $permissions",
            {"role": role_name, "permissions": permissions},
        )

    project_query = "MATCH (p:Project) RETURN count(p) AS cnt"
    project_count = graph.query(project_query)
    if len(project_count.result_set) == 0 or project_count.result_set[0][0] == 0:
        graph.query(
            """
            CREATE (p:Project {
                id: 'prj-001',
                name: 'Enterprise Brain',
                client_name: 'Internal Platform',
                cost: 250000,
                start_date: '2025-01-01',
                end_date: '2025-06-30',
                status: 'ACTIVE',
                is_deleted: false,
                created_by: 'superadmin@company.com',
                updated_by: 'superadmin@company.com',
                comments: 'Core internal productivity platform'
            })
            """
        )


def init_super_admin():
    try:
        graph = get_falkordb_connection()
    except RuntimeError as exc:
        print(f"Skipping super admin initialization: {exc}")
        return

    super_email = os.getenv("SUPER_ADMIN_EMAIL", "superadmin@company.com")
    super_pass = normalize_bcrypt_password(os.getenv("SUPER_ADMIN_PASSWORD", "SuperAdmin@123"))

    # Check if Super Admin exists
    query = "MATCH (u:User {email: $email}) RETURN u"
    result = graph.query(query, {'email': super_email})

    if len(result.result_set) == 0:
        hashed_password = hash_password(super_pass)
        create_query = """
        CREATE (u:User {
            id: 'super_admin_01',
            email: $email,
            password: $password,
            name: 'Super Admin',
            status: 'ACTIVE'
        })
        MERGE (r:Role {name: 'SuperAdmin'})
        CREATE (u)-[:HAS_ROLE]->(r)
        """
        graph.query(create_query, {'email': super_email, 'password': hashed_password})
        print("Super Admin initialized successfully.")