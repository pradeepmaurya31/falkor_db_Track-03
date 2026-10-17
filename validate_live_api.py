import json
import urllib.parse
import urllib.request

base = "http://localhost:8000"

with urllib.request.urlopen(base + "/api/health", timeout=20) as r:
    health = json.loads(r.read().decode())
    print("HEALTH", r.status, json.dumps(health, separators=(",", ":")))

form = urllib.parse.urlencode({
    "username": "employee@company.com",
    "password": "Employee@123",
}).encode()
req = urllib.request.Request(
    base + "/api/auth/login",
    data=form,
    method="POST",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
with urllib.request.urlopen(req, timeout=20) as r:
    login = json.loads(r.read().decode())
    print("LOGIN", r.status, json.dumps(login, separators=(",", ":")))

req2 = urllib.request.Request(
    base + "/api/dashboard",
    headers={"Authorization": "Bearer " + login["access_token"]},
)
with urllib.request.urlopen(req2, timeout=20) as r:
    dashboard = json.loads(r.read().decode())
    print("DASHBOARD", r.status, "keys=", sorted(dashboard.keys()))
    print("ROLE", dashboard.get("role"))
    print("SUMMARY", json.dumps(dashboard.get("summary", {}), separators=(",", ":")))
