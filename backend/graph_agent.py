from backend.database import get_falkordb_connection
from backend.graph_queries import validate_query_access, get_query_template


class GraphExecutionAgent:
    @staticmethod
    def execute(entity_name, action_name, user_role, params=None):
        params = params or {}
        if not validate_query_access(user_role, entity_name, action_name):
            raise PermissionError(f"Role '{user_role}' is not allowed to execute '{entity_name}.{action_name}'.")

        query = get_query_template(entity_name, action_name)
        if not query:
            raise ValueError(f"No prebuilt query found for {entity_name}.{action_name}.")

        graph = get_falkordb_connection()
        result = graph.query(query, params)
        return list(result.result_set)

    @staticmethod
    def execute_list_employees(user_role, email=None):
        if user_role in {"SuperAdmin", "Admin"}:
            return GraphExecutionAgent.execute("User", "list_all", user_role)
        if user_role == "Manager":
            return GraphExecutionAgent.execute("User", "list_team", user_role, {"manager_email": email})
        return GraphExecutionAgent.execute("User", "get_by_email", user_role, {"email": email})

    @staticmethod
    def execute_ticket_approval(user_role, ticket_id, updated_by):
        from backend.enterprise_data import approve_ticket_record

        return approve_ticket_record(ticket_id, updated_by, user_role)
