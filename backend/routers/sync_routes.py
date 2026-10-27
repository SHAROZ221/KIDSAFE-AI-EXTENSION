# KidSafe AI Backend - Policy Sync Router
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(tags=["Policy Sync"])

@router.post("/api/sync", response_model=schemas.SyncResponse)
def sync_device(
    payload: schemas.SyncPayload,
    db: Session = Depends(get_db)
):
    device = db.query(models.PairedDevice).filter(models.PairedDevice.device_token == payload.device_token).first()
    if not device:
        raise HTTPException(status_code=401, detail="Invalid device token.")

    profile = db.query(models.ChildProfile).filter(models.ChildProfile.id == device.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    # Update sync timestamp and usage time
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    device.last_sync_at = now

    if profile.last_active_date != today:
        profile.time_used_today_seconds = 0
        profile.last_active_date = today
    elif payload.time_used_today_seconds and payload.time_used_today_seconds > profile.time_used_today_seconds:
        profile.time_used_today_seconds = payload.time_used_today_seconds

    db.commit()

    # Fetch custom rules
    rules = db.query(models.CustomRule).filter(models.CustomRule.profile_id == profile.id).all()
    allowlist = [r.domain for r in rules if r.rule_type == "allow"]
    blocklist = [r.domain for r in rules if r.rule_type == "block"]

    # Fetch requests
    requests = db.query(models.ApprovalRequest).filter(
        models.ApprovalRequest.profile_id == profile.id
    ).order_by(models.ApprovalRequest.requested_at.desc()).limit(20).all()

    return schemas.SyncResponse(
        success=True,
        profile_id=profile.id,
        profile_name=profile.name,
        tier=profile.tier,
        daily_time_limit_minutes=profile.daily_time_limit_minutes,
        is_protection_active=profile.is_protection_active,
        custom_allowlist=allowlist,
        custom_blocklist=blocklist,
        pending_request_updates=requests
    )
