# KidSafe AI Backend - Approval Requests Router
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter(tags=["Approval Requests"])

@router.post("/api/requests", response_model=schemas.ApprovalRequestResponse)
def submit_request(
    request_in: schemas.ApprovalRequestCreate,
    x_device_token: str = Header(None, alias="X-Device-Token"),
    db: Session = Depends(get_db)
):
    if not x_device_token:
        raise HTTPException(status_code=401, detail="X-Device-Token header missing.")

    device = db.query(models.PairedDevice).filter(models.PairedDevice.device_token == x_device_token).first()
    if not device:
        raise HTTPException(status_code=401, detail="Invalid device token.")

    clean_domain = request_in.domain.strip().lower()

    # Check if a pending request for this domain already exists
    existing = db.query(models.ApprovalRequest).filter(
        models.ApprovalRequest.profile_id == device.profile_id,
        models.ApprovalRequest.domain == clean_domain,
        models.ApprovalRequest.status == "pending"
    ).first()

    if existing:
        return existing

    new_request = models.ApprovalRequest(
        profile_id=device.profile_id,
        url=request_in.url,
        domain=clean_domain,
        reason=request_in.reason or "Child requested access from block page.",
        status="pending"
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/api/profiles/{profile_id}/requests", response_model=List[schemas.ApprovalRequestResponse])
def get_profile_requests(
    profile_id: str,
    parent: models.Parent = Depends(auth.get_current_parent),
    db: Session = Depends(get_db)
):
    profile = db.query(models.ChildProfile).filter(
        models.ChildProfile.id == profile_id,
        models.ChildProfile.parent_id == parent.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    return db.query(models.ApprovalRequest).filter(
        models.ApprovalRequest.profile_id == profile_id
    ).order_by(models.ApprovalRequest.requested_at.desc()).all()

@router.post("/api/requests/{request_id}/approve")
def approve_request(
    request_id: str,
    parent: models.Parent = Depends(auth.get_current_parent),
    db: Session = Depends(get_db)
):
    req = db.query(models.ApprovalRequest).join(models.ChildProfile).filter(
        models.ApprovalRequest.id == request_id,
        models.ChildProfile.parent_id == parent.id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found.")

    req.status = "approved"
    req.resolved_at = datetime.now(timezone.utc)

    # Automatically add to custom allowlist for this profile
    existing_rule = db.query(models.CustomRule).filter(
        models.CustomRule.profile_id == req.profile_id,
        models.CustomRule.domain == req.domain
    ).first()

    if not existing_rule:
        allow_rule = models.CustomRule(
            profile_id=req.profile_id,
            domain=req.domain,
            rule_type="allow"
        )
        db.add(allow_rule)
    else:
        existing_rule.rule_type = "allow"

    db.commit()
    return {"success": True, "status": "approved", "domain": req.domain}

@router.post("/api/requests/{request_id}/deny")
def deny_request(
    request_id: str,
    parent: models.Parent = Depends(auth.get_current_parent),
    db: Session = Depends(get_db)
):
    req = db.query(models.ApprovalRequest).join(models.ChildProfile).filter(
        models.ApprovalRequest.id == request_id,
        models.ChildProfile.parent_id == parent.id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found.")

    req.status = "denied"
    req.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "status": "denied"}
