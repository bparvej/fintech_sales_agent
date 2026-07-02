"""
DTOs for the application layer.
"""

from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    exchange_name: str
    country: str | None = None
    llm_provider: str | None = None
    search_provider: str | None = None


class AnalysisResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    message: str


class AnalysisStatusResponse(BaseModel):
    job_id: uuid.UUID
    exchange_name: str
    status: str
    step_number: int
    total_steps: int
    error: str | None = None
    completed_at: str | None = None


class AnalysisResultResponse(BaseModel):
    job_id: uuid.UUID
    exchange_id: uuid.UUID | None
    status: str
    report_data: dict[str, Any] | None = None
