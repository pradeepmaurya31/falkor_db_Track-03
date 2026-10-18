import logging
import os
import re
from typing import List, TypedDict

from google import genai
from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

from backend.database import get_falkordb_connection
from backend.enterprise_data import (
    ATTENDANCE,
    HOLIDAYS,
    TICKETS,
    USER_CATALOG,
    create_ticket_record,
    create_user_record,
    find_user_by_email,
    list_holidays_for_role,
    list_tickets_for_role,
    update_user_record,
)
from backend.graph_agent import GraphExecutionAgent

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

ROLE_ACCESS = {
    "SuperAdmin": {"users", "roles", "permissions", "attendance", "tickets", "projects", "salary", "assets", "travel", "holidays"},
    "Admin": {"attendance", "tickets", "projects", "roles", "users", "permissions", "holidays"},
    "Manager": {"attendance", "tickets", "projects", "team", "users", "holidays"},
    "Employee": {"attendance", "tickets", "holidays", "projects"},
}


def is_employee_creation_request(message: str) -> bool:
    msg = (message or "").lower()
    direct_patterns = [
        "add employee",
        "create employee",
        "hire employee",
        "new employee",
        "add user",
        "create user",
        "hire user",
        "add staff",
        "create staff",
        "hire staff",
    ]
    if any(pattern in msg for pattern in direct_patterns):
        return True
    if re.search(r"\b(?:add|create|hire|new)\b.*\b(?:employee|user|staff)\b", msg):
        return True
    if re.search(r"\b(?:can you|please)\s*(?:add|create|hire|new)\s+[a-z][a-z .'-]+\s*(?:,|and)?\s*(?:email|e-mail)\s*[:=]?", msg):
        return True
    return False


class AgentState(TypedDict):
    user_email: str
    user_role: str
    message: str
    intent: str
    extracted_data: dict
    chat_history: List[dict]
    response: str
    requires_approval: bool


def _get_manager_for_employee(email: str):
    for user in USER_CATALOG:
        if not user.get("is_deleted", False) and user.get("role") == "Manager":
            return user
    return {"name": "Project Manager", "email": "manager@company.com"}


def _build_employee_self_service_response(state: AgentState):
    msg = (state["message"] or "").lower()
    email = state["user_email"]

    if "manager" in msg:
        manager = _get_manager_for_employee(email)
        state["response"] = f"Your manager is {manager['name']} ({manager['email']})."
        return state

    if "holiday" in msg:
        holidays = list_holidays_for_role(state["user_role"])
        if not holidays:
            state["response"] = "There are no holiday entries available right now."
            return state
        holiday_list = "; ".join(
            f"{h['holiday_name']} ({h.get('holiday_date') or h.get('year')})" for h in holidays[:5]
        )
        state["response"] = f"Upcoming company holidays: {holiday_list}."
        return state

    if "ticket" in msg:
        create_verbs = ["create", "raise", "new", "submit", "open"]
        view_verbs = ["show", "list", "view", "check", "details", "last", "latest", "my", "recent"]
        if any(token in msg for token in create_verbs) and not any(token in msg for token in view_verbs):
            return None

        relevant = [
            t for t in list_tickets_for_role(state["user_role"])
            if not t.get("is_deleted", False) and (t.get("user_email") == email or t.get("created_by") == email)
        ]
        if "pending" in msg:
            relevant = [t for t in relevant if t.get("status") == "PENDING_MANAGER_APPROVAL"]
        if not relevant:
            state["response"] = "You do not have any matching tickets in your current scope."
            return state
        if any(token in msg for token in ["last", "latest", "recent"]):
            last_ticket = max(relevant, key=lambda t: t.get("updated_at") or t.get("created_at") or "")
            state["response"] = (
                f"Your latest ticket is {last_ticket['id']} with status {last_ticket.get('status', 'PENDING_MANAGER_APPROVAL')} "
                f"and type {last_ticket.get('type', 'GENERAL')}."
            )
            return state
        summary = "; ".join(f"{t['id']} ({t['status']})" for t in relevant[:10])
        state["response"] = f"Your ticket summary: {summary}."
        return state

    if "attendance" in msg:
        relevant = [a for a in ATTENDANCE if not a.get("is_deleted", False) and a.get("user_email") == email]
        if not relevant:
            state["response"] = "No attendance record has been found for your current period."
            return state
        latest = sorted(relevant, key=lambda item: item.get("date", ""), reverse=True)[0]
        state["response"] = (
            f"Your most recent attendance is {latest.get('date')} from {latest.get('in_time', '--')} to {latest.get('out_time', '--')} "
            f"({latest.get('type', 'FULL_DAY')})."
        )
        return state

    return None


def intent_classifier_node(state: AgentState):
    msg = state["message"].lower()
    logger.info("Classifying intent for user=%s role=%s message=%s", state.get("user_email"), state.get("user_role"), state.get("message"))
    if is_employee_creation_request(state["message"]):
        state["intent"] = "CREATE_EMPLOYEE"
        state["requires_approval"] = False
    elif any(k in msg for k in ["ticket", "flight", "laptop", "cab", "leave", "asset", "travel"]):
        ticket_query_patterns = [
            "my ticket",
            "my tickets",
            "last ticket",
            "latest ticket",
            "recent ticket",
            "show my ticket",
            "show my tickets",
            "view my ticket",
            "check my ticket",
            "details of my ticket",
            "pending ticket",
            "pending tickets",
        ]
        if any(pattern in msg for pattern in ticket_query_patterns):
            state["intent"] = "GENERAL_QUERY"
            state["requires_approval"] = False
        else:
            state["intent"] = "CREATE_TICKET"
            state["requires_approval"] = True
    elif "attendance" in msg or "holiday" in msg:
        state["intent"] = "CHECK_ATTENDANCE"
        state["requires_approval"] = False
    else:
        state["intent"] = "GENERAL_QUERY"
        state["requires_approval"] = False
    logger.info("Intent classified as %s for user=%s", state["intent"], state.get("user_email"))
    return state


def parse_employee_creation_message(message: str):
    logger.info("Parsing employee creation request: %s", message)
    name_match = re.search(
        r"(?:add|create|hire|new|can you\s*(?:add|create|hire|new))\s+(?:employee|user|staff)?\s*([A-Za-z][A-Za-z .'-]+?)(?:\s*(?:,|and)?\s*(?:email|e-mail)|\s+(?:with|and|role)|\s*$)",
        message,
        re.IGNORECASE,
    )
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
    logger.info("Running guardrail check for role=%s message=%s", role, state.get("message"))
    allowed_topics = ROLE_ACCESS.get(role, {"attendance", "tickets", "holidays"})
    restricted_topics = [
        "salary",
        "permissions",
        "roles",
        "admin",
        "user management",
        "team",
        "project cost",
        "employee attendance",
    ]

    if role == "Employee":
        if any(topic in msg for topic in restricted_topics):
            logger.warning("Employee role blocked due to restricted access: user=%s message=%s", state.get("user_email"), state.get("message"))
            state["response"] = "You can only access your own attendance, tickets, holidays and project-related information."
            return state

    if is_employee_creation_request(state["message"]):
        if role not in {"SuperAdmin", "Admin", "Manager"}:
            logger.warning("Employee creation blocked for non-authorized role: role=%s user=%s", role, state.get("user_email"))
            state["response"] = "Only managers, admins, and super admins can add employees through chat."
            return state
        logger.info("Employee creation request allowed for role=%s user=%s", role, state.get("user_email"))
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
    logger.info("Executing slot filler for intent=%s user=%s", state.get("intent"), state.get("user_email"))
    state = guardrail_check(state)
    if "response" in state and state["response"]:
        return state

    approval_match = re.search(r"\bapprove\b\s*(?:ticket\s*)?(INCIDENT\d+)", state["message"], re.IGNORECASE)
    if approval_match:
        ticket_id = approval_match.group(1).upper()
        if state["user_role"] not in {"SuperAdmin", "Admin", "Manager"}:
            state["response"] = "Only supervisors can approve tickets."
            return state
        try:
            GraphExecutionAgent.execute_ticket_approval(state["user_role"], ticket_id, state["user_email"])
        except Exception:
            logger.warning("Ticket approval graph call failed; using in-memory fallback for user=%s ticket=%s", state.get("user_email"), ticket_id)
        for ticket in TICKETS:
            if ticket.get("id") == ticket_id:
                ticket["status"] = "APPROVED"
                ticket["updated_by"] = state["user_email"]
                break
        state["response"] = f"Ticket {ticket_id} has been approved successfully."
        return state

    pending_match = re.search(r"\b(pending|open)\s+(?:ticket|tickets)\b|\bshow\s+me\s+(?:pending|open)\s+(?:ticket|tickets)\b", state["message"], re.IGNORECASE)
    if pending_match:
        tickets = list_tickets_for_role(state["user_role"])
        if state["user_role"] == "Manager":
            subordinate_emails = {
                u["email"] for u in USER_CATALOG
                if u.get("role") == "Employee" and (u.get("reporting_manager") or u.get("created_by") or "").lower() == state["user_email"].lower()
            }
            relevant = [
                t for t in tickets
                if not t.get("is_deleted", False)
                and t.get("user_email") in subordinate_emails
                and t.get("status") == "PENDING_MANAGER_APPROVAL"
            ]
        else:
            relevant = [
                t for t in tickets
                if not t.get("is_deleted", False)
                and (
                    state["user_role"] in {"SuperAdmin", "Admin"}
                    or t.get("user_email") == state["user_email"]
                )
                and t.get("status") == "PENDING_MANAGER_APPROVAL"
            ]
        if not relevant:
            state["response"] = "There are no pending tickets in your current access scope."
            return state
        summary = "; ".join(f"{t['id']} ({t['type']})" for t in relevant)
        state["response"] = f"Pending tickets: {summary}."
        return state

    if state["user_role"] == "Employee":
        employee_response = _build_employee_self_service_response(state)
        if employee_response is not None:
            return employee_response

    if state["intent"] == "CREATE_EMPLOYEE":
        payload = parse_employee_creation_message(state["message"])
        if not payload["name"] or not payload["email"]:
            state["response"] = "Please provide an employee name and email, for example: 'Add employee John Doe email john.doe@company.com role Employee'."
            return state

        if find_user_by_email(payload["email"]):
            state["response"] = "This email is already in use. Please provide a unique email address."
            return state

        default_password = "Welcome@123"
        payload["password"] = payload.get("password", default_password)
        try:
            created = create_user_record(payload, state["user_email"])
        except PermissionError:
            logger.warning("Permission denied while creating employee for user=%s role=%s", state.get("user_email"), state.get("user_role"))
            state["response"] = "You do not have permission to add employees in the current role context."
            return state
        except ValueError as exc:
            state["response"] = str(exc)
            return state
        except Exception:
            logger.exception("User creation failed while creating employee for user=%s", state.get("user_email"))
            state["response"] = "retry aftersome time, facing some technical issue"
            return state

        state["response"] = (
            f"Employee {created['name']} has been added successfully. "
            f"Login details: Email = {created['email']}, Password = {created['password']}."
        )
        return state

    if state["intent"] == "CREATE_TICKET":
        ticket_text = state["message"]
        type_match = re.search(r"(?:ticket|incident)\s+(?:for|about)?\s*([A-Za-z\s]+?)(?:\s+to\s+|\s+for\s+|$)", ticket_text, re.IGNORECASE)
        ticket_type = (type_match.group(1).strip() if type_match else "GENERAL").upper().replace(" ", "_")
        if "laptop" in ticket_text.lower():
            ticket_type = "LAPTOP_ALLOCATION"
        elif "travel" in ticket_text.lower():
            ticket_type = "TRAVEL"
        elif "leave" in ticket_text.lower():
            ticket_type = "LEAVE"
        elif "asset" in ticket_text.lower():
            ticket_type = "ASSET"
        elif "attendance" in ticket_text.lower():
            ticket_type = "ATTENDANCE"

        try:
            ticket = create_ticket_record({"type": ticket_type, "comments": ticket_text, "user_email": state["user_email"]}, state["user_email"])
            state["response"] = f"Ticket {ticket['id']} created successfully for your request."
            return state
        except Exception:
            logger.exception("Ticket creation failed for user=%s", state.get("user_email"))
            state["response"] = "retry aftersome time, facing some technical issue"
            return state

    elif "list employee" in state["message"].lower() or "list employees" in state["message"].lower() or "show employees" in state["message"].lower():
        try:
            rows = GraphExecutionAgent.execute_list_employees(state["user_role"], state["user_email"])
            if not rows:
                state["response"] = "No employees found in your current scope."
            else:
                employee_summary = "; ".join(f"{row[0]} ({row[2]})" for row in rows[:10])
                state["response"] = f"Employees in scope: {employee_summary}."
        except PermissionError:
            logger.warning("Permission denied for employee listing user=%s role=%s", state.get("user_email"), state.get("user_role"))
            state["response"] = "You do not have permission to list employees in this data scope."
    elif "change password" in state["message"].lower() or "reset password" in state["message"].lower():
        match = re.search(r"(?:change|reset)\s+(?:my\s+)?password\s+(?:to|=|:)?\s*([A-Za-z0-9@#$%^&*!_\-]{8,})", state["message"], re.IGNORECASE)
        if not match:
            state["response"] = "Please provide the new password in the format: 'Change my password to NewPassword@123'."
            return state
        new_password = match.group(1).strip()
        user = find_user_by_email(state["user_email"])
        if not user:
            state["response"] = "User profile not found."
            return state
        updated = update_user_record(user["id"], {"password": new_password}, state["user_email"])
        if updated is None:
            state["response"] = "Unable to update your password. Please try again."
            return state
        state["response"] = "Your password has been updated successfully."
        return state
    else:
        if client is None:
            logger.warning("Gemini client unavailable for general query user=%s", state.get("user_email"))
            state["response"] = "I can help with attendance, tickets, projects, and employee additions. Please share the exact request and I will process it."
            return state
        try:
            response = client.models.generate_content(model=model_name, contents=state['message'])
            state["response"] = response.text
        except Exception as exc:
            logger.exception("LLM general query failed for user=%s", state.get("user_email"))
            state["response"] = "retry aftersome time, facing some technical issue"
    return state


def log_interaction_node(state: AgentState):
    logger.info("Logging interaction for user=%s response=%s", state.get("user_email"), state.get("response"))
    try:
        graph = get_falkordb_connection()
        query = """
        MATCH (u:User {email: $email})
        CREATE (u)-[:LOGGED_CHAT {timestamp: timestamp(), message: $msg, response: $resp}]->(u)
        """
        graph.query(query, {"email": state["user_email"], "msg": state["message"], "resp": state["response"]})
    except Exception as exc:
        logger.exception("Failed to log interaction for user=%s", state.get("user_email"))
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