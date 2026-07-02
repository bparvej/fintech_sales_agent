"""
Analysis Service.

High-level application service that exposes the core use cases to the API layer.
Handles starting analysis jobs and querying their status/results.
"""

from __future__ import annotations

import asyncio
import uuid

from app.application.dto.analysis_dtos import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatusResponse,
    AnalysisResultResponse,
)
from app.application.workflows.pipeline_orchestrator import PipelineOrchestrator
from app.domain.value_objects.analysis_status import AnalysisStatus
from app.infrastructure.database.connection import db_manager
from app.infrastructure.database.repositories.sql_repositories import (
    ExchangeRepository,
    SalesReportRepository,
)


class AnalysisService:
    """Service for managing the analysis pipeline lifecycle."""

    async def start_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """Starts a new background analysis job."""
        job_id = uuid.uuid4()
        
        # Initialize the orchestrator (it registers itself in the global dict)
        orchestrator = PipelineOrchestrator(
            job_id=job_id,
            exchange_name=request.exchange_name,
            country=request.country,
            llm_provider=request.llm_provider,
            search_provider=request.search_provider
        )
        
        # Start the pipeline in the background
        asyncio.create_task(orchestrator.run_pipeline())
        
        return AnalysisResponse(
            job_id=job_id,
            status=AnalysisStatus.PENDING.value,
            message=f"Analysis started for {request.exchange_name}"
        )

    async def get_status(self, job_id: uuid.UUID) -> AnalysisStatusResponse:
        """Get the real-time status of an analysis job."""
        job_id_str = str(job_id)
        job = PipelineOrchestrator.get_job(job_id_str)
        
        if job:
            # Job is currently in memory (running or recently finished/failed)
            return AnalysisStatusResponse(
                job_id=job_id,
                exchange_name=job.exchange_name,
                status=job.status.value,
                step_number=job.status.step_number,
                total_steps=AnalysisStatus.total_steps(),
                error=job.error,
                completed_at=None if not job.status.is_terminal else "Now" # Simplification
            )
            
        # If not in memory, we could check DB. For this implementation, we just return error.
        raise ValueError(f"Job not found or expired: {job_id}")

    async def get_results(self, job_id: uuid.UUID) -> AnalysisResultResponse:
        """Get the final results of a completed analysis job."""
        job = PipelineOrchestrator.get_job(str(job_id))
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
            
        if not job.status.is_terminal:
            return AnalysisResultResponse(
                job_id=job_id,
                exchange_id=job.exchange_id,
                status=job.status.value,
                report_data=None
            )
            
        if job.status == AnalysisStatus.FAILED:
            return AnalysisResultResponse(
                job_id=job_id,
                exchange_id=job.exchange_id,
                status=job.status.value,
                report_data={"error": job.error}
            )
            
        # Job completed successfully, fetch report from DB
        if not job.exchange_id:
            raise ValueError("Exchange ID not set despite completed status")
            
        async with db_manager.get_session() as session:
            repo = SalesReportRepository(session)
            report = await repo.find_by_exchange_id(job.exchange_id)
            
            return AnalysisResultResponse(
                job_id=job_id,
                exchange_id=job.exchange_id,
                status=job.status.value,
                report_data=report.model_dump() if report else None
            )
