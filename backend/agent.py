import os
import re
from typing import List, TypedDict

from google import genai
from langgraph.graph import END, StateGraph

from backend.database import get_falkordb_connection
from backend.enterprise_data import create_user_record, find_user_by_email

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

ROLE_ACCESS = {
    "SuperAdmin": {"users", "roles", "permissions", "attendance", "tickets", "projects", "salary", "assets", "travel", "holidays"},
    "Admin": {"attendance", "tickets", "projects", "roles", "users", "permissions", "holidays"},
    "Manager": {"attendance", "tickets", "projects", "team", "users", "holidays"},
    "Employee": {"attendance", "tickets", "holidays", "projects"},
}


class AgentState(TypedDict):
    user_email: str
    user_role: str
    message: str
    intent: str
    extracted_data: dict
    chat_history: List[dict]
    response: str
    requires_approval: bool


def intent_classifier_node(state: AgentState):
    msg = state["message"].lower()
    employee_create_keywords = [
        "add employee",
        "create employee",
        "hire employee",
        "new employee",
        "add user",
        "create user",
        "hire user",
    ]
    if any(k in msg for k in employee_create_keywords):
        state["intent"] = "CREATE_EMPLOYEE"
        state["requires_approval"] = False
    elif any(k in msg for k in ["ticket", "flight", "laptop", "cab", "leave", "asset", "travel"]):
        state["intent"] = "CREATE_TICKET"
        state["requires_approval"] = True
    elif "attendance" in msg or "holiday" in msg:
        state["intent"] = "CHECK_ATTENDANCE"
        state["requires_approval"] = False
    else:
        state["intent"] = "GENERAL_QUERY"
        state["requires_approval"] = False
    return state


def parse_employee_creation_message(message: str):
    name_match = re.search(r"(?:add|create|hire|new)\s+(?:employee|user)\s+([A-Za-z][A-Za-z .'-]+?)(?:\s+(?:with|and)?\s*(?:email|e-mail)|\s*$)", message, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).strip()
    else:
        name_match = re.search(r"(?:name|employee name)\s*[:=]\s*([A-Za-z][A-Za-z .'-]+)", message, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else ""

    email_match = re.search(r"(?:email|e-mail)\s*[:=]?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", message, re.IGNORECASE)
    email = email_match.group(1).strip() if email_match else ""

    role_match = re.search(r"(?:role)\s*[:=]?\s*([A-Za-z]+)", message, re.IGNORECASE)
    role = role_match.group(1).strip().title() if role_match else "Employee"

    return {"name": name, "email": email, "role": role}


def guardrail_check(state: AgentState):
    msg = state["message"].lower()
    role = state["user_role"]
    allowed_topics = ROLE_ACCESS.get(role, {"attendance", "tickets", "holidays"})
    restricted_topics = [
        "salary",
        "permissions",
        "roles",
        "manager",
        "admin",
        "user management",
        "team",
        "project cost",
        "employee attendance",
    ]

    if role == "Employee":
        if any(topic in msg for topic in restricted_topics):
            state["response"] = "You can only access your own attendance, tickets, holidays and project-related information."
            return state

    employee_create_keywords = [
        "add employee",
        "create employee",
        "hire employee",
        "new employee",
        "add user",
        "create user",
        "hire user",
    ]
    if any(keyword in msg for keyword in employee_create_keywords):
        if role not in {"SuperAdmin", "Admin", "Manager"}:
            state["response"] = "Only managers, admins, and super admins can add employees through chat."
            return state
        return state

    if role == "Manager":
        if any(topic in msg for topic in ["salary", "permissions", "roles", "user management"]) or "all employee attendance" in msg:
            state["response"] = "As a manager, you can view team attendance and project data, but not the full salary or permission matrix."
            return state

    if role == "Admin" and any(topic in msg for topic in ["salary", "permissions", "roles"]):
        if not {"permissions", "roles", "users"}.intersection(allowed_topics):
            state["response"] = "Your current access does not include permission or role administration."
            return state

    if role == "SuperAdmin":
        return state

    if not any(topic in msg for topic in [
        "attendance", "ticket", "holiday", "project", "leave", "travel", "asset", "cab", "laptop"
    ]):
        if "salary" in msg or "permission" in msg or "role" in msg or "admin" in msg:
            state["response"] = "This information is restricted by your role and is not available in your current chat access scope."
            return state

    return state


def ticket_slot_filler_node(state: AgentState):
    model_name = os.getenv("GENAI_MODEL_NAME", "gemini-3.8-flash")
    state = guardrail_check(state)
    if "response" in state and state["response"]:
        return state

    if state["intent"] == "CREATE_EMPLOYEE":
        payload = parse_employee_creation_message(state["message"])
        if not payload["name"] or not payload["email"]:
            state["response"] = "Please provide an employee name and email, for example: 'Add employee John Doe email john.doe@company.com role Employee'."
            return state

        if find_user_by_email(payload["email"]):
            state["response"] = f"An employee with email {payload['email']} already exists."
            return state

        created = create_user_record(payload, state["user_email"])
        state["response"] = (
            f"Employee {created['name']} has been added successfully with email {created['email']} "
            f"and role {created['role']}."
        )
        return state

    if state["intent"] == "CREATE_TICKET":
        prompt = f"Extract ticket details (type, description, date) from this message: '{state['message']}'"
        if client is None:
            state["response"] = "I have noted the request. Please confirm the ticket type and details, and it will be sent for manager approval."
            return state
        response = client.models.generate_content(model=model_name, contents=prompt)
        state["extracted_data"] = {"details": response.text}
        state["response"] = f"I have gathered your request details: {response.text}. Escalating to your Manager for approval."
    else:
        if client is None:
            state["response"] = "I can help with attendance, tickets, projects, and employee additions. Please share the exact request and I will process it."
            return state
        response = client.models.generate_content(model=model_name, contents=state['message'])
        state["response"] = response.text
    return state


def log_interaction_node(state: AgentState):
    try:
        graph = get_falkordb_connection()
        query = """
        MATCH (u:User {email: $email})
        CREATE (u)-[:LOGGED_CHAT {timestamp: timestamp(), message: $msg, response: $resp}]->(u)
        """
        graph.query(query, {"email": state["user_email"], "msg": state["message"], "resp": state["response"]})
    except Exception:
        pass
    return state


workflow = StateGraph(AgentState)
workflow.add_node("classifier", intent_classifier_node)
workflow.add_node("slot_filler", ticket_slot_filler_node)
workflow.add_node("logger", log_interaction_node)

workflow.set_entry_point("classifier")
workflow.add_edge("classifier", "slot_filler")
workflow.add_edge("slot_filler", "logger")
workflow.add_edge("logger", END)

compiled_agent = workflow.compile()