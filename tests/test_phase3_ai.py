# KidSafe AI - Phase 3 AI Verification Test Suite
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from main import app
from database import Base, engine, SessionLocal
import models
from ai.classifier import classifier_agent
from ai.parent_agent import parent_agent

client = TestClient(app)

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_page_classifier_direct():
    print("\n--- Testing Page Classifier Agent ---")

    # 1. High-risk gambling site
    res_gambling = classifier_agent.classify(
        url="https://online-casino-slots.com/play-real-money",
        title="Best Casino Slots",
        meta_description="Play real money roulette and slots",
        age_profile="junior"
    )
    assert res_gambling["verdict"] == "block"
    assert "gambling" in res_gambling["risk_flags"]
    assert res_gambling["age_rating"] == "18+"
    assert len(res_gambling["reason_child"]) > 5
    print("[PASS] High-risk content classified as block with risk flags")

    # 2. Educational learning site for Little Explorer
    res_edu = classifier_agent.classify(
        url="https://scratch.mit.edu/explore/projects",
        title="Scratch - Imagine, Program, Share",
        meta_description="Create stories, games, and animations with coding",
        age_profile="little_explorer"
    )
    assert res_edu["verdict"] == "allow"
    assert res_edu["age_rating"] == "5+"
    assert "education" in res_edu["categories"]
    print("[PASS] Educational content allowed for Little Explorer")

    # 3. Social media site for Little Explorer -> requires Ask Parent
    res_social = classifier_agent.classify(
        url="https://reddit.com/r/all",
        title="Reddit - Dive into anything",
        meta_description="Discussion forum and community posts",
        age_profile="little_explorer"
    )
    assert res_social["verdict"] in ["ask_parent", "block"]
    print("[PASS] Unmoderated forum flagged for Little Explorer")

    # 4. Verify PRD 7.1 Schema Keys
    required_keys = {"verdict", "confidence", "categories", "age_rating", "reason_parent", "reason_child", "risk_flags"}
    assert required_keys.issubset(set(res_edu.keys()))
    print("[PASS] Schema matches PRD Section 7.1 specification")

def test_parent_nl_agent_direct():
    print("\n--- Testing Parent Natural Language Agent ---")
    db = SessionLocal()
    try:
        # Create dummy parent and profile
        dummy_parent = models.Parent(email="nlp@example.com", password_hash="hash")
        db.add(dummy_parent)
        db.commit()

        dummy_child = models.ChildProfile(
            parent_id=dummy_parent.id,
            name="Zoya",
            age=10,
            tier="junior",
            daily_time_limit_minutes=120
        )
        db.add(dummy_child)
        db.commit()

        # 1. Preview multi-action command
        cmd = "Allow scratch.mit.edu and set daily screen time to 90 minutes"
        preview = parent_agent.preview_instruction(cmd, dummy_child)
        assert preview["success"] is True
        assert preview["actions_count"] == 2
        assert preview["requires_confirmation"] is True
        print(f"[PASS] NL Command successfully parsed into {preview['actions_count']} structured actions")

        # 2. Apply confirmed actions
        apply_res = parent_agent.apply_actions(preview["actions"], dummy_child.id, db)
        assert apply_res["success"] is True
        assert apply_res["updated_profile"]["daily_time_limit_minutes"] == 90

        # Verify DB custom rule was created
        rule = db.query(models.CustomRule).filter(
            models.CustomRule.profile_id == dummy_child.id,
            models.CustomRule.domain == "scratch.mit.edu"
        ).first()
        assert rule is not None
        assert rule.rule_type == "allow"
        print("[PASS] Confirmed NL actions applied to database and profile")

        # 3. Test tier change instruction
        cmd2 = "Switch to Little Explorer mode"
        preview2 = parent_agent.preview_instruction(cmd2, dummy_child)
        assert preview2["success"] is True
        assert preview2["actions"][0]["action_type"] == "CHANGE_TIER"
        assert preview2["actions"][0]["params"]["tier"] == "little_explorer"
        print("[PASS] Safety tier change parsed from natural language")

    finally:
        db.close()

def test_ai_api_endpoints():
    print("\n--- Testing AI HTTP Endpoints ---")
    # 1. /api/ai/classify
    classify_payload = {
        "url": "https://pbskids.org/arthur",
        "title": "PBS Kids Games",
        "meta_description": "Educational games for children",
        "age_profile": "little_explorer"
    }
    res = client.post("/api/ai/classify", json=classify_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] == "allow"
    print("[PASS] POST /api/ai/classify endpoint working")

    # 2. Auth for parent endpoints
    reg_res = client.post("/api/auth/register", json={
        "email": "aiparent@example.com",
        "password": "mypassword123",
        "full_name": "AI Parent"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch child profile
    profiles = client.get("/api/profiles", headers=headers).json()
    profile_id = profiles[0]["id"]

    # 3. /api/ai/nl-rule/preview
    prev_res = client.post("/api/ai/nl-rule/preview", headers=headers, json={
        "profile_id": profile_id,
        "instruction": "Block twitch.tv and discord.com"
    })
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["success"] is True
    assert prev_data["actions_count"] == 2
    print("[PASS] POST /api/ai/nl-rule/preview endpoint working")

    # 4. /api/ai/nl-rule/confirm
    conf_res = client.post("/api/ai/nl-rule/confirm", headers=headers, json={
        "profile_id": profile_id,
        "actions": prev_data["actions"]
    })
    assert conf_res.status_code == 200
    conf_data = conf_res.json()
    assert conf_data["success"] is True
    print("[PASS] POST /api/ai/nl-rule/confirm endpoint working")

if __name__ == "__main__":
    setup_module()
    test_page_classifier_direct()
    test_parent_nl_agent_direct()
    test_ai_api_endpoints()
    print("\n=== ALL PHASE 3 AI TESTS PASSED! ===")
