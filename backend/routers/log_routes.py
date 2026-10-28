# KidSafe AI Backend - Activity Logs Router
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

from io import StringIO
import csv
from fastapi.responses import Response

router = APIRouter(tags=["Activity Logs"])

@router.post("/api/logs", response_model=schemas.ActivityLogResponse)
def create_log(
    log_in: schemas.ActivityLogCreate,
    x_device_token: str = Header(None, alias="X-Device-Token"),
    db: Session = Depends(get_db)
):
    if not x_device_token:
        raise HTTPException(status_code=401, detail="X-Device-Token header missing.")

    device = db.query(models.PairedDevice).filter(models.PairedDevice.device_token == x_device_token).first()
    if not device:
        raise HTTPException(status_code=401, detail="Invalid device token.")

    new_log = models.ActivityLog(
        profile_id=device.profile_id,
        url=log_in.url,
        domain=log_in.domain.strip().lower(),
        action=log_in.action,
        reason=log_in.reason or "",
        category=log_in.category or "general"
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

@router.get("/api/profiles/{profile_id}/logs", response_model=List[schemas.ActivityLogResponse])
def get_profile_logs(
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

    return db.query(models.ActivityLog).filter(
        models.ActivityLog.profile_id == profile_id
    ).order_by(models.ActivityLog.timestamp.desc()).limit(100).all()

@router.get("/api/profiles/{profile_id}/logs/export.csv")
def export_profile_logs_csv(
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

    logs = db.query(models.ActivityLog).filter(
        models.ActivityLog.profile_id == profile_id
    ).order_by(models.ActivityLog.timestamp.desc()).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp (UTC)", "Domain", "Action", "Reason", "Category", "Full URL"])

    for log in logs:
        writer.writerow([
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
            log.domain,
            log.action,
            log.reason,
            log.category,
            log.url
        ])

    csv_data = output.getvalue()
    filename = f"kidsafe_{profile.name.lower()}_activity_report.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
