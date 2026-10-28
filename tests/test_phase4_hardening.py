# KidSafe AI - Phase 4 Verification Test Suite
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from fastapi.testclient import TestClient
from main import app
from database import Base, engine

client = TestClient(app)

def test_hardening_registry_files():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    chrome_reg = os.path.join(root, "hardening", "chrome_hardening.reg")
    edge_reg = os.path.join(root, "hardening", "edge_hardening.reg")
    guide_md = os.path.join(root, "hardening", "HARDENING_GUIDE.md")

    assert os.path.exists(chrome_reg), "Chrome registry hardening file exists"
    assert os.path.exists(edge_reg), "Edge registry hardening file exists"
    assert os.path.exists(guide_md), "Hardening guide exists"

    with open(chrome_reg, "r") as f:
        content = f.read()
        assert "ExtensionInstallForcelist" in content
        assert "IncognitoModeAvailability" in content

    print("[PASS] Hardening registry policies & bypass guide verified")

def test_evaluation_benchmark_files():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dataset_file = os.path.join(root, "evaluation", "dataset.json")
    report_file = os.path.join(root, "evaluation", "EVALUATION_REPORT.md")

    assert os.path.exists(dataset_file), "Evaluation dataset exists"
    assert os.path.exists(report_file), "Evaluation report exists"

    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Performance Metrics Table" in content
        assert "Confusion Matrix Breakdown" in content

    print("[PASS] Evaluation dataset and benchmark report verified")

def test_csv_export_endpoint():
    # Register & get auth token
    reg = client.post("/api/auth/register", json={
        "email": "csvparent@example.com",
        "password": "securepassword123",
        "full_name": "CSV Parent"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get child profile
    profiles = client.get("/api/profiles", headers=headers).json()
    profile_id = profiles[0]["id"]

    # Export CSV
    csv_res = client.get(f"/api/profiles/{profile_id}/logs/export.csv", headers=headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert "Timestamp (UTC),Domain,Action,Reason,Category,Full URL" in csv_res.text
    print("[PASS] Activity logs CSV report export endpoint verified")

if __name__ == "__main__":
    test_hardening_registry_files()
    test_evaluation_benchmark_files()
    test_csv_export_endpoint()
    print("\n=== ALL PHASE 4 TESTS PASSED! ===")
