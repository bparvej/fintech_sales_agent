"""Lead score domain entity."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class LeadScore(BaseModel):
    """Represents the overall lead score for an institution."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    institution_id: uuid.UUID
    overall_score: float = 0.0  # 0 to 100
    technology_score: float = 0.0
    digital_presence_score: float = 0.0
    opportunity_score: float = 0.0
    accessibility_score: float = 0.0
    scoring_factors: dict[str, Any] = Field(default_factory=dict)
    tier: str = "cold"  # hot, warm, cold
    recommendation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
