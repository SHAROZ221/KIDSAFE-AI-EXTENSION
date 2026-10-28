# KidSafe AI Backend - AI Agent Router (Phase 3)
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth
from ai.classifier import classifier_agent
from ai.parent_agent import parent_agent

router = APIRouter(prefix="/api/ai", tags=["AI Agents"])

@router.post("/classify", response_model=schemas.ClassifyResponse)
def classify_webpage(payload: schemas.ClassifyRequest):
    """
    Evaluates webpage URL, metadata, and extracted text using LLM / semantic agent.
    Returns age rating, structured verdict, and kid-friendly reasons.
    """
    if not payload.url:
        raise HTTPException(status_code=400, detail="URL is required for classification.")

    verdict_data = classifier_agent.classify(
        url=payload.url,
        title=payload.title or "",
        meta_description=payload.meta_description or "",
        page_text_sample=payload.page_text_sample or "",
        age_profile=payload.age_profile or "junior"
    )
    return schemas.ClassifyResponse(**verdict_data)

@router.post("/nl-rule/preview")
def preview_natural_language_rule(
    payload: schemas.NLPreviewRequest,
    parent: models.Parent = Depends(auth.get_current_parent),
    db: Session = Depends(get_db)
):
    """
    Interprets natural-language parent instructions (e.g. 'allow scratch.mit.edu and block twitch for Aarav')
    and returns a structured preview of actions for confirmation.
    """
    profile = db.query(models.ChildProfile).filter(
        models.ChildProfile.id == payload.profile_id,
        models.ChildProfile.parent_id == parent.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    preview_res = parent_agent.preview_instruction(
        instruction=payload.instruction,
        profile=profile
    )
    return preview_res

@router.post("/nl-rule/confirm")
def confirm_natural_language_rule(
    payload: schemas.NLConfirmRequest,
    parent: models.Parent = Depends(auth.get_current_parent),
    db: Session = Depends(get_db)
):
    """
    Applies confirmed actions to the child profile.
    """
    profile = db.query(models.ChildProfile).filter(
        models.ChildProfile.id == payload.profile_id,
        models.ChildProfile.parent_id == parent.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    result = parent_agent.apply_actions(
        actions=payload.actions,
        profile_id=profile.id,
        db=db
    )
    return result
