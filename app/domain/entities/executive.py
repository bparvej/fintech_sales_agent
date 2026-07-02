"""Executive domain entity."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Executive(BaseModel):
    """Represents a key decision-maker at a financial institution."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    institution_id: uuid.UUID
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    source: Optional[str] = None  # Where the info was found
    confidence: float = 0.0  # 0.0 to 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
