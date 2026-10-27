# KidSafe AI Backend - Device Pairing Router
import random
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter(tags=["Device Pairing"])

@router.post("/api/profiles/{profile_id}/generate-pairing-code", response_model=schemas.GenerateCodeResponse)
def generate_pairing_code(
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

    # Invalidate previous unused codes for this profile
    db.query(models.PairingCode).filter(
        models.PairingCode.profile_id == profile_id,
        models.PairingCode.is_used == False
    ).update({"is_used": True})

    # Generate 6-digit numeric pairing code
    code = "".join(random.choices("0123456789", k=6))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    pairing_code = models.PairingCode(
        profile_id=profile_id,
        code=code,
        expires_at=expires_at
    )
    db.add(pairing_code)
    db.commit()
    db.refresh(pairing_code)

    return schemas.GenerateCodeResponse(
        code=pairing_code.code,
        profile_id=profile_id,
        expires_at=pairing_code.expires_at
    )

@router.post("/api/devices/pair", response_model=schemas.PairDeviceResponse)
def pair_device(
    payload: schemas.PairDeviceRequest,
    db: Session = Depends(get_db)
):
    clean_code = payload.pairing_code.strip()
    now = datetime.now(timezone.utc)

    pairing_code = db.query(models.PairingCode).filter(
        models.PairingCode.code == clean_code,
        models.PairingCode.is_used == False,
        models.PairingCode.expires_at > now
    ).first()

    if not pairing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired pairing code. Please generate a new code from Parent Dashboard."
        )

    profile = db.query(models.ChildProfile).filter(models.ChildProfile.id == pairing_code.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile associated with pairing code not found.")

    # Mark code used
    pairing_code.is_used = True

    # Generate device token
    device_token = secrets.token_hex(32)
    device = models.PairedDevice(
        profile_id=profile.id,
        device_token=device_token,
        device_name=payload.device_name or "Child Browser",
        browser=payload.browser or "Chrome",
        last_sync_at=now
    )
    db.add(device)
    db.commit()

    return schemas.PairDeviceResponse(
        success=True,
        device_token=device_token,
        profile_id=profile.id,
        profile_name=profile.name,
        tier=profile.tier,
        daily_time_limit_minutes=profile.daily_time_limit_minutes
    )
