"""Sales opportunity domain entity."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.value_objects.opportunity_type import OpportunityType


class SalesOpportunity(BaseModel):
    """Represents an identified sales opportunity at an institution."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    institution_id: uuid.UUID
    opportunity_type: OpportunityType
    title: str
    description: str
    priority: str = "medium"  # low, medium, high, critical
    confidence_score: float = 0.0  # 0.0 to 1.0
    estimated_value: Optional[str] = None
    reasoning: Optional[str] = None
    recommended_approach: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
