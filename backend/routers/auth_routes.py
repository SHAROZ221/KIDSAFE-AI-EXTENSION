# KidSafe AI Backend - Auth Router
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.TokenResponse)
def register(parent_in: schemas.ParentRegister, db: Session = Depends(get_db)):
    existing = db.query(models.Parent).filter(models.Parent.email == parent_in.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    hashed_pw = auth.hash_password(parent_in.password)
    new_parent = models.Parent(
        email=parent_in.email.lower(),
        password_hash=hashed_pw,
        full_name=parent_in.full_name or "Parent"
    )
    db.add(new_parent)
    db.commit()
    db.refresh(new_parent)

    # Automatically create a default child profile for easy onboarding
    default_child = models.ChildProfile(
        parent_id=new_parent.id,
        name="Child",
        age=10,
        tier="junior",
        daily_time_limit_minutes=120
    )
    db.add(default_child)
    db.commit()

    token = auth.create_access_token({"sub": new_parent.id})
    return schemas.TokenResponse(
        access_token=token,
        parent_id=new_parent.id,
        email=new_parent.email,
        full_name=new_parent.full_name
    )

@router.post("/login", response_model=schemas.TokenResponse)
def login(login_in: schemas.ParentLogin, db: Session = Depends(get_db)):
    parent = db.query(models.Parent).filter(models.Parent.email == login_in.email.lower()).first()
    if not parent or not auth.verify_password(login_in.password, parent.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    token = auth.create_access_token({"sub": parent.id})
    return schemas.TokenResponse(
        access_token=token,
        parent_id=parent.id,
        email=parent.email,
        full_name=parent.full_name
    )

@router.get("/me", response_model=schemas.ParentResponse)
def get_current_user_profile(parent: models.Parent = Depends(auth.get_current_parent)):
    return parent
