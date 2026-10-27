# KidSafe AI - Phase 2 Backend Verification Test Suite
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from main import app
from database import Base, engine

client = TestClient(app)

def setup_module():
    # Fresh database tables for testing
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    print("[PASS] Backend health check")

def test_auth_workflow():
    # 1. Register parent
    reg_payload = {
        "email": "testparent@example.com",
        "password": "securepassword123",
        "full_name": "Test Parent"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 200
    data = reg_res.json()
    assert "access_token" in data
    token = data["access_token"]
    print("[PASS] Parent registration and automatic JWT issuance")

    # 2. Login
    login_res = client.post("/api/auth/login", json={
        "email": "testparent@example.com",
        "password": "securepassword123"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    print("[PASS] Parent login")

    # 3. Get /me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "testparent@example.com"
    print("[PASS] JWT authentication verification (/api/auth/me)")

def test_child_profiles_and_rules():
    # Login to get token
    login_res = client.post("/api/auth/login", json={
        "email": "testparent@example.com",
        "password": "securepassword123"
    })
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Create new profile
    prof_payload = {
        "name": "Aarav",
        "age": 9,
        "tier": "junior",
        "daily_time_limit_minutes": 90
    }
    prof_res = client.post("/api/profiles", json=prof_payload, headers=auth_headers)
    assert prof_res.status_code == 200
    prof = prof_res.json()
    profile_id = prof["id"]
    assert prof["name"] == "Aarav"
    assert prof["tier"] == "junior"
    print("[PASS] Child profile creation")

    # Add custom rule to profile
    rule_res = client.post(
        f"/api/profiles/{profile_id}/rules",
        json={"domain": "scratch.mit.edu", "rule_type": "allow"},
        headers=auth_headers
    )
    assert rule_res.status_code == 200
    assert rule_res.json()["domain"] == "scratch.mit.edu"
    print("[PASS] Custom domain rule creation")

def test_pairing_sync_and_approval_workflow():
    login_res = client.post("/api/auth/login", json={
        "email": "testparent@example.com",
        "password": "securepassword123"
    })
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Fetch profile
    profiles = client.get("/api/profiles", headers=auth_headers).json()
    aarav_profile = [p for p in profiles if p["name"] == "Aarav"][0]
    profile_id = aarav_profile["id"]

    # 1. Generate 6-digit pairing code
    code_res = client.post(f"/api/profiles/{profile_id}/generate-pairing-code", headers=auth_headers)
    assert code_res.status_code == 200
    code_data = code_res.json()
    pairing_code = code_data["code"]
    assert len(pairing_code) == 6
    print(f"[PASS] 6-digit pairing code generated: {pairing_code}")

    # 2. Extension connects with pairing code
    pair_res = client.post("/api/devices/pair", json={
        "pairing_code": pairing_code,
        "device_name": "Aarav's Chrome Book",
        "browser": "Chrome"
    })
    assert pair_res.status_code == 200
    pair_data = pair_res.json()
    device_token = pair_data["device_token"]
    assert pair_data["success"] is True
    print("[PASS] Extension device pairing using one-time code")

    # 3. Extension syncs policy
    sync_res = client.post("/api/sync", json={
        "device_token": device_token,
        "time_used_today_seconds": 1800
    })
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["tier"] == "junior"
    assert "scratch.mit.edu" in sync_data["custom_allowlist"]
    print("[PASS] Extension policy sync (/api/sync)")

    # 4. Extension submits approval request from block page
    req_res = client.post(
        "/api/requests",
        headers={"X-Device-Token": device_token},
        json={
            "url": "https://nationalgeographic.com/animals",
            "domain": "nationalgeographic.com",
            "reason": "Need photos for science project"
        }
    )
    assert req_res.status_code == 200
    req_id = req_res.json()["id"]
    print("[PASS] Child block page approval request submission")

    # 5. Parent approves request in dashboard
    approve_res = client.post(f"/api/requests/{req_id}/approve", headers=auth_headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"
    print("[PASS] Parent approval action from dashboard")

    # 6. Verify domain was automatically added to custom allowlist
    rules_res = client.get(f"/api/profiles/{profile_id}/rules", headers=auth_headers)
    domains = [r["domain"] for r in rules_res.json() if r["rule_type"] == "allow"]
    assert "nationalgeographic.com" in domains
    print("[PASS] Approved domain auto-migrated to child's allowlist")

    # 7. Extension logs activity
    log_res = client.post(
        "/api/logs",
        headers={"X-Device-Token": device_token},
        json={
            "url": "https://blocked-gambling-site.com",
            "domain": "blocked-gambling-site.com",
            "action": "blocked",
            "reason": "gambling_keyword",
            "category": "gambling"
        }
    )
    assert log_res.status_code == 200
    print("[PASS] Extension activity logging")

    # 8. Parent views activity logs
    logs_fetch = client.get(f"/api/profiles/{profile_id}/logs", headers=auth_headers)
    assert logs_fetch.status_code == 200
    assert len(logs_fetch.json()) >= 1
    assert logs_fetch.json()[0]["domain"] == "blocked-gambling-site.com"
    print("[PASS] Parent activity log viewing")

if __name__ == "__main__":
    setup_module()
    test_health()
    test_auth_workflow()
    test_child_profiles_and_rules()
    test_pairing_sync_and_approval_workflow()
    print("\n=== ALL PHASE 2 TESTS PASSED SUCCESSFULLY! ===")
