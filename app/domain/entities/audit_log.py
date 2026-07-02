"""Audit log domain entity."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    """Tracks all significant system actions for auditing."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    action: str
    entity_type: str
    entity_id: Optional[uuid.UUID] = None
    agent_name: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    status: str = "success"
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
