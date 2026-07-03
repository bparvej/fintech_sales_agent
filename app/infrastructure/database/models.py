"""
SQLAlchemy ORM models mapped from domain entities.

These models define the database schema. Domain entities are pure Pydantic models;
these ORM models handle persistence only.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.domain.value_objects.institution_type import InstitutionType
from app.domain.value_objects.opportunity_type import OpportunityType
from app.infrastructure.database.connection import Base


class ExchangeModel(Base):
    __tablename__ = "exchanges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(500), nullable=False, index=True)
    country = Column(String(200), nullable=True)
    website_url = Column(Text, nullable=True)
    member_list_url = Column(Text, nullable=True)
    total_members = Column(Integer, default=0)
    status = Column(String(50), default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    institutions = relationship("InstitutionModel", back_populates="exchange", lazy="selectin")
    reports = relationship("SalesReportModel", back_populates="exchange", lazy="selectin")


class InstitutionModel(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exchange_id = Column(String(36), ForeignKey("exchanges.id"), nullable=False, index=True)
    name = Column(String(500), nullable=False, index=True)
    institution_type = Column(
        Enum(InstitutionType, name="institution_type_enum"),
        default=InstitutionType.BROKERAGE,
    )
    website_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(100), nullable=True)
    email = Column(String(300), nullable=True)
    digital_maturity_score = Column(Float, nullable=True)
    status = Column(String(50), default="pending", index=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    exchange = relationship("ExchangeModel", back_populates="institutions")
    executives = relationship("ExecutiveModel", back_populates="institution", lazy="selectin")
    technology_profile = relationship("TechnologyProfileModel", back_populates="institution", uselist=False, lazy="selectin")
    opportunities = relationship("SalesOpportunityModel", back_populates="institution", lazy="selectin")
    lead_score = relationship("LeadScoreModel", back_populates="institution", uselist=False, lazy="selectin")


class ExecutiveModel(Base):
    __tablename__ = "executives"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    title = Column(String(300), nullable=True)
    email = Column(String(300), nullable=True)
    phone = Column(String(100), nullable=True)
    linkedin_url = Column(Text, nullable=True)
    facebook_url = Column(Text, nullable=True)
    profile_image_url = Column(Text, nullable=True)
    source = Column(String(200), nullable=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    institution = relationship("InstitutionModel", back_populates="executives")


class TechnologyProfileModel(Base):
    __tablename__ = "technology_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, unique=True, index=True)
    detected_technologies = Column(JSON, default=list)
    frontend_technologies = Column(JSON, default=list)
    backend_technologies = Column(JSON, default=list)
    cms_platform = Column(String(200), nullable=True)
    hosting_provider = Column(String(200), nullable=True)
    cdn_provider = Column(String(200), nullable=True)
    analytics_tools = Column(JSON, default=list)
    security_features = Column(JSON, default=list)
    has_mobile_app = Column(Boolean, default=False)
    has_api = Column(Boolean, default=False)
    ssl_grade = Column(String(10), nullable=True)
    analysis_summary = Column(Text, nullable=True)
    digital_maturity_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    institution = relationship("InstitutionModel", back_populates="technology_profile")


class SalesOpportunityModel(Base):
    __tablename__ = "sales_opportunities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    opportunity_type = Column(
        Enum(OpportunityType, name="opportunity_type_enum"),
        nullable=False,
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), default="medium")
    confidence_score = Column(Float, default=0.0)
    estimated_value = Column(String(100), nullable=True)
    reasoning = Column(Text, nullable=True)
    recommended_approach = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    institution = relationship("InstitutionModel", back_populates="opportunities")


class LeadScoreModel(Base):
    __tablename__ = "lead_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, unique=True, index=True)
    overall_score = Column(Float, default=0.0)
    technology_score = Column(Float, default=0.0)
    digital_presence_score = Column(Float, default=0.0)
    opportunity_score = Column(Float, default=0.0)
    accessibility_score = Column(Float, default=0.0)
    scoring_factors = Column(JSON, default=dict)
    tier = Column(String(20), default="cold")
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    institution = relationship("InstitutionModel", back_populates="lead_score")


class SalesReportModel(Base):
    __tablename__ = "sales_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exchange_id = Column(String(36), ForeignKey("exchanges.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    total_institutions = Column(Integer, default=0)
    total_executives = Column(Integer, default=0)
    total_opportunities = Column(Integer, default=0)
    hot_leads = Column(Integer, default=0)
    warm_leads = Column(Integer, default=0)
    cold_leads = Column(Integer, default=0)
    report_data = Column(JSON, default=dict)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    exchange = relationship("ExchangeModel", back_populates="reports")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(String(200), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(36), nullable=True)
    agent_name = Column(String(200), nullable=True)
    details = Column(JSON, default=dict)
    duration_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    status = Column(String(50), default="success")
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
