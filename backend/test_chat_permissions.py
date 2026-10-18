import uuid

from backend.agent import guardrail_check, ticket_slot_filler_node
from backend.database import get_falkordb_connection
from backend.enterprise_data import ROLE_PERMISSIONS, get_role_permissions


def test_manager_has_employee_add_permission():
    assert "users.write" in ROLE_PERMISSIONS["Manager"]
    assert "users.read" in ROLE_PERMISSIONS["Manager"]


def test_permissions_are_loaded_from_graph_storage():
    graph = get_falkordb_connection()
    graph.query("MERGE (r:Role {name: 'Employee'}) SET r.permissions = ['custom.read', 'custom.write']")
    permissions = get_role_permissions("Employee")
    assert "custom.read" in permissions
    assert "custom.write" in permissions


def test_manager_can_add_employee_via_chat():
    state = {
        "user_email": "manager@company.com",
        "user_role": "Manager",
        "message": "Add employee John Doe email john@example.com role Employee",
        "intent": "",
        "extracted_data": {},
        "chat_history": [],
        "response": "",
        "requires_approval": False,
    }
    result = guardrail_check(state)
    assert "response" not in result or result["response"] == ""


def test_admin_and_superadmin_can_create_employee_from_natural_language_request():
    for role in ["Admin", "SuperAdmin"]:
        state = {
            "user_email": "admin@company.com" if role == "Admin" else "superadmin@company.com",
            "user_role": role,
            "message": "can you add Mohan Singh, email mohan@gmail.com and location Pune, salary 25000",
            "intent": "",
            "extracted_data": {},
            "chat_history": [],
            "response": "",
            "requires_approval": False,
        }
        result = guardrail_check(state)
        assert "response" not in result or result["response"] == ""


def test_manager_can_approve_pending_ticket_in_chat():
    state = {
        "user_email": "manager@company.com",
        "user_role": "Manager",
        "message": "approve INCIDENT001",
        "intent": "CREATE_TICKET",
        "extracted_data": {},
        "chat_history": [],
        "response": "",
        "requires_approval": False,
    }
    result = ticket_slot_filler_node(state)
    assert "approved" in result["response"].lower()


def test_employee_can_ask_for_own_attendance_and_manager_name():
    for message in [
        "show my attendance",
        "who is my manager",
        "show my pending tickets",
    ]:
        state = {
            "user_email": "employee@company.com",
            "user_role": "Employee",
            "message": message,
            "intent": "GENERAL_QUERY",
            "extracted_data": {},
            "chat_history": [],
            "response": "",
            "requires_approval": False,
        }
        result = ticket_slot_filler_node(state)
        assert result["response"]
        assert "retry aftersome time" not in result["response"].lower()


def test_chat_employee_add_uses_unique_email_and_succeeds_for_new_user():
    unique_email = f"chat-user-{uuid.uuid4().hex[:8]}@company.com"
    state = {
        "user_email": "manager@company.com",
        "user_role": "Manager",
        "message": f"Add employee Test User email {unique_email} role Employee",
        "intent": "CREATE_EMPLOYEE",
        "extracted_data": {},
        "chat_history": [],
        "response": "",
        "requires_approval": False,
    }
    result = ticket_slot_filler_node(state)
    assert "Login details" in result["response"]
    assert "already in use" not in result["response"].lower()


def test_employee_can_create_ticket_and_see_own_ticket_details():
    create_state = {
        "user_email": "employee@company.com",
        "user_role": "Employee",
        "message": "create a ticket for laptop request",
        "intent": "CREATE_TICKET",
        "extracted_data": {},
        "chat_history": [],
        "response": "",
        "requires_approval": False,
    }
    create_result = ticket_slot_filler_node(create_state)
    assert "Ticket" in create_result["response"]
    assert "created successfully" in create_result["response"].lower()

    query_state = {
        "user_email": "employee@company.com",
        "user_role": "Employee",
        "message": "show my tickets",
        "intent": "GENERAL_QUERY",
        "extracted_data": {},
        "chat_history": [],
        "response": "",
        "requires_approval": False,
    }
    query_result = ticket_slot_filler_node(query_state)
    assert "ticket summary" in query_result["response"].lower() or "Ticket" in query_result["response"]


def test_holiday_responses_include_the_actual_date():
    state = {
        "user_email": "employee@company.com",
        "user_role": "Employee",
        "message": "show holidays",
        "intent": "CHECK_ATTENDANCE",
        "extracted_data": {},
        "chat_history": [],
        "response": "",
        "requires_approval": False,
    }
    result = ticket_slot_filler_node(state)
    assert "2026-10-21" in result["response"]
    assert "Dussehra" in result["response"]


def test_employee_last_ticket_query_is_not_treated_as_ticket_creation():
    state = {
        "user_email": "employee@company.com",
        "user_role": "Employee",
        "message": "my last ticket",
        "intent": "CREATE_TICKET",
        "extracted_data": {},
        "chat_history": [],
        "response": "",
        "requires_approval": False,
    }
    result = ticket_slot_filler_node(state)
    assert "no matching tickets" not in result["response"].lower()
    assert "latest ticket" in result["response"].lower() or "ticket summary" in result["response"].lower() or "INCIDENT" in result["response"]
