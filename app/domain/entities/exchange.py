"""Exchange domain entity."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Exchange(BaseModel):
    """Represents a stock exchange or securities exchange."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    country: Optional[str] = None
    website_url: Optional[str] = None
    member_list_url: Optional[str] = None
    total_members: int = 0
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
