# KidSafe AI Backend - Pydantic Request & Response Schemas
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

# Auth Schemas
class ParentRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = "Parent"

class ParentLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    parent_id: str
    email: str
    full_name: str

class ParentResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True

# Child Profile Schemas
class ChildProfileCreate(BaseModel):
    name: str
    age: int
    tier: Optional[str] = "junior" # little_explorer, junior, teen
    daily_time_limit_minutes: Optional[int] = 120

class ChildProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    tier: Optional[str] = None
    daily_time_limit_minutes: Optional[int] = None
    is_protection_active: Optional[bool] = None

class ChildProfileResponse(BaseModel):
    id: str
    name: str
    age: int
    tier: str
    daily_time_limit_minutes: int
    time_used_today_seconds: int
    is_protection_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Pairing Schemas
class GenerateCodeResponse(BaseModel):
    code: str
    profile_id: str
    expires_at: datetime

class PairDeviceRequest(BaseModel):
    pairing_code: str
    device_name: Optional[str] = "Child Chrome Browser"
    browser: Optional[str] = "Chrome"

class PairDeviceResponse(BaseModel):
    success: bool
    device_token: str
    profile_id: str
    profile_name: str
    tier: str
    daily_time_limit_minutes: int

# Custom Rule Schemas
class CustomRuleCreate(BaseModel):
    domain: str
    rule_type: str # 'allow' or 'block'

class CustomRuleResponse(BaseModel):
    id: str
    profile_id: str
    domain: str
    rule_type: str
    created_at: datetime

    class Config:
        from_attributes = True

# Approval Request Schemas
class ApprovalRequestCreate(BaseModel):
    url: str
    domain: str
    reason: Optional[str] = ""

class ApprovalRequestResponse(BaseModel):
    id: str
    profile_id: str
    url: str
    domain: str
    reason: str
    status: str
    requested_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Sync Schemas
class SyncPayload(BaseModel):
    device_token: str
    time_used_today_seconds: Optional[int] = 0

class SyncResponse(BaseModel):
    success: bool
    profile_id: str
    profile_name: str
    tier: str
    daily_time_limit_minutes: int
    is_protection_active: bool
    custom_allowlist: List[str]
    custom_blocklist: List[str]
    pending_request_updates: List[ApprovalRequestResponse]

# Activity Log Schemas
class ActivityLogCreate(BaseModel):
    url: str
    domain: str
    action: str # 'blocked', 'allowed'
    reason: Optional[str] = ""
    category: Optional[str] = ""

class ActivityLogResponse(BaseModel):
    id: str
    profile_id: str
    url: str
    domain: str
    action: str
    reason: str
    category: str
    timestamp: datetime

    class Config:
        from_attributes = True
