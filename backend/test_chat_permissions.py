from backend.agent import guardrail_check
from backend.enterprise_data import ROLE_PERMISSIONS


def test_manager_has_employee_add_permission():
    assert "users.write" in ROLE_PERMISSIONS["Manager"]
    assert "users.read" in ROLE_PERMISSIONS["Manager"]


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
