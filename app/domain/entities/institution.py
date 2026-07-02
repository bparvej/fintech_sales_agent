"""Institution domain entity."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.value_objects.institution_type import InstitutionType


class Institution(BaseModel):
    """Represents a financial institution (brokerage, bank, fintech, etc.)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    exchange_id: uuid.UUID
    name: str
    institution_type: InstitutionType = InstitutionType.BROKERAGE
    website_url: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    digital_maturity_score: Optional[float] = None
    status: str = "pending"
    raw_data: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
