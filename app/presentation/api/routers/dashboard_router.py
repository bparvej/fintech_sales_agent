"""
Dashboard and WebSocket router.

Serves the main HTML application and provides real-time progress updates via WebSocket.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

from app.application.workflows.pipeline_orchestrator import PipelineOrchestrator
from app.domain.value_objects.analysis_status import AnalysisStatus
from app.shared.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def serve_dashboard() -> Any:
    """Serve the main SPA dashboard."""
    static_dir = Path(__file__).resolve().parent.parent.parent / "static"
    index_file = static_dir / "index.html"
    
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>FinTech Sales Intelligence</h1><p>Dashboard UI not built yet.</p>")


@router.websocket("/ws/progress/{job_id}")
async def progress_websocket(websocket: WebSocket, job_id: str) -> None:
    """WebSocket endpoint for real-time analysis progress updates."""
    await websocket.accept()
    
    try:
        # Loop to push updates
        last_status = None
        
        while True:
            job = PipelineOrchestrator.get_job(job_id)
            
            if not job:
                await websocket.send_json({
                    "status": "error",
                    "message": "Job not found or expired"
                })
                break
                
            current_status = job.status
            
            # Send update if status changed or every 2 seconds as heartbeat
            if current_status != last_status:
                await websocket.send_json({
                    "job_id": job_id,
                    "exchange_name": job.exchange_name,
                    "status": current_status.value,
                    "step_number": current_status.step_number,
                    "total_steps": AnalysisStatus.total_steps(),
                    "error": job.error
                })
                last_status = current_status
                
            if current_status.is_terminal:
                break
                
            await asyncio.sleep(2.0)
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", job_id=job_id)
    except Exception as e:
        logger.error("WebSocket error", job_id=job_id, error=str(e))
        try:
            await websocket.send_json({"status": "error", "message": str(e)})
        except Exception:
            pass
