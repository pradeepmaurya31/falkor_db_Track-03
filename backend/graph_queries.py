from copy import deepcopy

GRAPH_QUERY_LIBRARY = {
    "User": {
        "list_all": """
            MATCH (u:User)
            OPTIONAL MATCH (u)-[:HAS_ROLE]->(r:Role)
            RETURN u.email AS email, u.name AS name, u.status AS status, coalesce(r.name, 'Employee') AS role
        """,
        "get_by_email": """
            MATCH (u:User {email: $email})
            OPTIONAL MATCH (u)-[:HAS_ROLE]->(r:Role)
            RETURN u.email AS email, u.name AS name, u.status AS status, coalesce(r.name, 'Employee') AS role
        """,
        "list_team": """
            MATCH (manager:User {email: $manager_email})<-[:REPORTS_TO*0..5]-(u:User)
            OPTIONAL MATCH (u)-[:HAS_ROLE]->(r:Role)
            RETURN DISTINCT u.email AS email, u.name AS name, u.status AS status, coalesce(r.name, 'Employee') AS role
        """,
        "create": """
            CREATE (u:User {
                id: $id,
                email: $email,
                name: $name,
                password: $password,
                status: $status
            })
            WITH u
            MERGE (r:Role {name: $role})
            CREATE (u)-[:HAS_ROLE]->(r)
            RETURN u.email AS email, u.name AS name, u.status AS status, $role AS role
        """,
        "update": """
            MATCH (u:User {email: $email})
            SET u.name = COALESCE($name, u.name),
                u.status = COALESCE($status, u.status)
            RETURN u.email AS email, u.name AS name, u.status AS status
        """,
        "delete": """
            MATCH (u:User {email: $email})
            SET u.status = 'INACTIVE'
            RETURN u.email AS email, u.name AS name, u.status AS status
        """,
    },
    "Project": {
        "list_all": """
            MATCH (p:Project)
            RETURN p.id AS id, p.name AS name, p.client_name AS client_name, p.status AS status
        """,
        "list_my_projects": """
            MATCH (u:User {email: $email})<-[:ASSIGNED_TO]-(p:Project)
            RETURN p.id AS id, p.name AS name, p.status AS status
        """,
    },
    "Attendance": {
        "list_for_employee": """
            MATCH (a:Attendance {user_email: $email})
            RETURN a.date AS date, a.in_time AS in_time, a.out_time AS out_time, a.type AS type, a.is_approved AS is_approved
        """,
        "list_team": """
            MATCH (manager:User {email: $manager_email})<-[:REPORTS_TO*0..5]-(u:User)
            MATCH (a:Attendance {user_email: u.email})
            RETURN a.user_email AS user_email, a.date AS date, a.type AS type, a.is_approved AS is_approved
        """,
    },
}

ROLE_QUERY_POLICY = {
    "SuperAdmin": {
        "User": {"list_all", "get_by_email", "create", "update", "delete"},
        "Project": {"list_all", "list_my_projects"},
        "Attendance": {"list_for_employee", "list_team"},
    },
    "Admin": {
        "User": {"list_all", "get_by_email", "create", "update", "delete"},
        "Project": {"list_all", "list_my_projects"},
        "Attendance": {"list_for_employee", "list_team"},
    },
    "Manager": {
        "User": {"list_team", "get_by_email", "create"},
        "Project": {"list_all", "list_my_projects"},
        "Attendance": {"list_for_employee", "list_team"},
    },
    "Employee": {
        "User": {"get_by_email"},
        "Project": {"list_my_projects"},
        "Attendance": {"list_for_employee"},
    },
}


def get_query_template(entity_name, action_name):
    return GRAPH_QUERY_LIBRARY.get(entity_name, {}).get(action_name)


def validate_query_access(role, entity_name, action_name):
    allowed = ROLE_QUERY_POLICY.get(role, {})
    return action_name in allowed.get(entity_name, set())
