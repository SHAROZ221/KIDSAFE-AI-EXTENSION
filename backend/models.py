# KidSafe AI Backend - SQLAlchemy ORM Models
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Parent(Base):
    __tablename__ = "parents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), default="Parent")
    created_at = Column(DateTime, default=utc_now)

    profiles = relationship("ChildProfile", back_populates="parent", cascade="all, delete-orphan")


class ChildProfile(Base):
    __tablename__ = "child_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String(36), ForeignKey("parents.id"), nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, default=10)
    tier = Column(String(50), default="junior") # little_explorer, junior, teen
    daily_time_limit_minutes = Column(Integer, default=120)
    time_used_today_seconds = Column(Integer, default=0)
    last_active_date = Column(String(10), default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    is_protection_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    parent = relationship("Parent", back_populates="profiles")
    pairing_codes = relationship("PairingCode", back_populates="profile", cascade="all, delete-orphan")
    devices = relationship("PairedDevice", back_populates="profile", cascade="all, delete-orphan")
    rules = relationship("CustomRule", back_populates="profile", cascade="all, delete-orphan")
    requests = relationship("ApprovalRequest", back_populates="profile", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="profile", cascade="all, delete-orphan")


class PairingCode(Base):
    __tablename__ = "pairing_codes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("child_profiles.id"), nullable=False)
    code = Column(String(6), index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("ChildProfile", back_populates="pairing_codes")


class PairedDevice(Base):
    __tablename__ = "paired_devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("child_profiles.id"), nullable=False)
    device_token = Column(String(64), unique=True, index=True, nullable=False)
    device_name = Column(String(100), default="Child Browser")
    browser = Column(String(50), default="Chrome")
    paired_at = Column(DateTime, default=utc_now)
    last_sync_at = Column(DateTime, default=utc_now)

    profile = relationship("ChildProfile", back_populates="devices")


class CustomRule(Base):
    __tablename__ = "custom_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("child_profiles.id"), nullable=False)
    domain = Column(String(255), nullable=False)
    rule_type = Column(String(20), nullable=False) # 'allow' or 'block'
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("ChildProfile", back_populates="rules")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("child_profiles.id"), nullable=False)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False)
    reason = Column(Text, default="")
    status = Column(String(20), default="pending") # 'pending', 'approved', 'denied'
    requested_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)

    profile = relationship("ChildProfile", back_populates="requests")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("child_profiles.id"), nullable=False)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False)
    action = Column(String(20), nullable=False) # 'blocked', 'allowed'
    reason = Column(String(100), default="")
    category = Column(String(50), default="")
    timestamp = Column(DateTime, default=utc_now)

    profile = relationship("ChildProfile", back_populates="activity_logs")
