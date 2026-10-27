# KidSafe AI Backend - Child Profiles & Rules Router
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/api/profiles", tags=["Child Profiles"])

@router.get("", response_model=List[schemas.ChildProfileResponse])
def get_profiles(
    parent: models.Parent = Depends(auth.get_current_parent),
    db: Session = Depends(get_db)
):
    return db.query(models.ChildProfile).filter(models.ChildProfile.parent_id == parent.id).all()

@router.post("", response_model=schemas.ChildProfileResponse)
def create_profile(
    profile_in: schemas.ChildProfileCreate,
    parent: models.Parent = Depends(auth.get_current_parent),
    db: Session = Depends(get_db)
):
    new_profile = models.ChildProfile(
        parent_id=parent.id,
        name=profile_in.name,
        age=profile_in.age,
        tier=profile_in.tier or "junior",
        daily_time_limit_minutes=profile_in.daily_time_limit_minutes or 120
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile

@router.get("/{profile_id}", response_model=schemas.ChildProfileResponse)
def get_profile(
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
    return profile

@router.put("/{profile_id}", response_model=schemas.ChildProfileResponse)
def update_profile(
    profile_id: str,
    updates: schemas.ChildProfileUpdate,
    parent: models.Parent = Depends(auth.get_current_parent),
    db: Session = Depends(get_db)
):
    profile = db.query(models.ChildProfile).filter(
        models.ChildProfile.id == profile_id,
        models.ChildProfile.parent_id == parent.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    if updates.name is not None:
        profile.name = updates.name
    if updates.age is not None:
        profile.age = updates.age
    if updates.tier is not None:
        profile.tier = updates.tier
    if updates.daily_time_limit_minutes is not None:
        profile.daily_time_limit_minutes = updates.daily_time_limit_minutes
    if updates.is_protection_active is not None:
        profile.is_protection_active = updates.is_protection_active

    db.commit()
    db.refresh(profile)
    return profile

@router.delete("/{profile_id}")
def delete_profile(
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
    db.delete(profile)
    db.commit()
    return {"success": True, "message": "Profile deleted."}

# Rules sub-routes
@router.get("/{profile_id}/rules", response_model=List[schemas.CustomRuleResponse])
def get_profile_rules(
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
    return db.query(models.CustomRule).filter(models.CustomRule.profile_id == profile_id).all()

@router.post("/{profile_id}/rules", response_model=schemas.CustomRuleResponse)
def add_profile_rule(
    profile_id: str,
    rule_in: schemas.CustomRuleCreate,
    parent: models.Parent = Depends(auth.get_current_parent),
    db: Session = Depends(get_db)
):
    profile = db.query(models.ChildProfile).filter(
        models.ChildProfile.id == profile_id,
        models.ChildProfile.parent_id == parent.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    clean_domain = rule_in.domain.strip().lower()
    # Check if rule exists
    existing = db.query(models.CustomRule).filter(
        models.CustomRule.profile_id == profile_id,
        models.CustomRule.domain == clean_domain
    ).first()

    if existing:
        existing.rule_type = rule_in.rule_type
        db.commit()
        db.refresh(existing)
        return existing

    new_rule = models.CustomRule(
        profile_id=profile_id,
        domain=clean_domain,
        rule_type=rule_in.rule_type
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@router.delete("/{profile_id}/rules/{rule_id}")
def delete_profile_rule(
    profile_id: str,
    rule_id: str,
    parent: models.Parent = Depends(auth.get_current_parent),
    db: Session = Depends(get_db)
):
    rule = db.query(models.CustomRule).join(models.ChildProfile).filter(
        models.CustomRule.id == rule_id,
        models.CustomRule.profile_id == profile_id,
        models.ChildProfile.parent_id == parent.id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")

    db.delete(rule)
    db.commit()
    return {"success": True, "message": "Rule removed."}
