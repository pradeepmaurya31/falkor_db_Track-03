import os
from falkordb import FalkorDB

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