"""Technology profile domain entity."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TechnologyProfile(BaseModel):
    """Represents the technology stack detected for an institution."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    institution_id: uuid.UUID
    detected_technologies: list[dict[str, Any]] = Field(default_factory=list)
    frontend_technologies: list[str] = Field(default_factory=list)
    backend_technologies: list[str] = Field(default_factory=list)
    cms_platform: Optional[str] = None
    hosting_provider: Optional[str] = None
    cdn_provider: Optional[str] = None
    analytics_tools: list[str] = Field(default_factory=list)
    security_features: list[str] = Field(default_factory=list)
    has_mobile_app: bool = False
    has_api: bool = False
    ssl_grade: Optional[str] = None
    analysis_summary: Optional[str] = None
    digital_maturity_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
