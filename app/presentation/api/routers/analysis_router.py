"""
REST API router for analysis operations.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.application.dto.analysis_dtos import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatusResponse,
    AnalysisResultResponse,
)
from app.application.services.analysis_service import AnalysisService
from app.infrastructure.llm.llm_factory import LLMFactory

router = APIRouter()
analysis_service = AnalysisService()


@router.post("", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """Start a new financial exchange analysis job."""
    return await analysis_service.start_analysis(request)


@router.get("/{job_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(job_id: uuid.UUID) -> AnalysisStatusResponse:
    """Get the current progress status of an analysis job."""
    try:
        return await analysis_service.get_status(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{job_id}/results", response_model=AnalysisResultResponse)
async def get_analysis_results(job_id: uuid.UUID) -> AnalysisResultResponse:
    """Get the final sales intelligence report for a completed job."""
    try:
        return await analysis_service.get_results(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
        
@router.get("/llm-providers", response_model=list[dict[str, str]])
async def get_llm_providers() -> list[dict[str, str]]:
    """Get available LLM providers for the UI."""
    return LLMFactory.available_providers()
