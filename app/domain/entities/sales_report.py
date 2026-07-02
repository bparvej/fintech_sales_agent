"""Sales report domain entity."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class SalesReport(BaseModel):
    """Represents a generated sales intelligence report for an exchange analysis."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    exchange_id: uuid.UUID
    title: str
    summary: Optional[str] = None
    total_institutions: int = 0
    total_executives: int = 0
    total_opportunities: int = 0
    hot_leads: int = 0
    warm_leads: int = 0
    cold_leads: int = 0
    report_data: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
