"""
REST API router for configuration and filter options.

Provides endpoints for UI dropdowns: LLM providers, countries, models, exchanges.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.infrastructure.llm.llm_factory import LLMFactory
from app.infrastructure.database.seeders import get_countries_list, get_llm_models_for_provider
from app.shared.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/llm-providers")
async def get_llm_providers() -> list[dict[str, str]]:
    """
    Get available LLM providers for the UI dropdown.
    
    Returns list of providers with status (configured/not_configured) and available models.
    """
    try:
        providers = LLMFactory.available_providers()
        
        # Enhance with model lists
        for provider in providers:
            provider["available_models"] = get_llm_models_for_provider(provider["value"])
            if not provider["configured"]:
                provider["warning"] = f"API key not configured. Set {provider['value'].upper()}_API_KEY in .env"
        
        logger.info("LLM providers retrieved", count=len(providers))
        return providers
    except Exception as exc:
        logger.error("Failed to get LLM providers", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve LLM providers")


@router.get("/llm-models/{provider}")
async def get_llm_models(provider: str) -> dict[str, list[str]]:
    """
    Get available models for a specific LLM provider.
    
    Example: GET /api/v1/config/llm-models/openai
    """
    try:
        if provider.lower() not in ["openai", "deepseek", "qwen", "ollama", "gemini"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown provider: {provider}. Options: openai, deepseek, qwen, ollama, gemini"
            )
        
        models = get_llm_models_for_provider(provider)
        return {"provider": provider, "models": models}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to get models for provider {provider}", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve models")


@router.get("/countries")
async def get_countries() -> dict[str, list[str]]:
    """
    Get list of all countries with stock exchanges.
    
    Used for UI country filter dropdown.
    """
    try:
        countries = get_countries_list()
        logger.info("Countries list retrieved", count=len(countries))
        return {"countries": countries}
    except Exception as exc:
        logger.error("Failed to get countries", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve countries")


@router.get("/llm-status")
async def check_llm_status(provider: str = Query(..., description="Provider name (e.g., openai, deepseek)")) -> dict[str, str | bool]:
    """
    Check if a specific LLM provider is properly configured.
    
    Returns configuration status and any warnings/errors.
    Example: GET /api/v1/config/llm-status?provider=openai
    """
    try:
        providers = LLMFactory.available_providers()
        provider_info = next((p for p in providers if p["value"] == provider.lower()), None)
        
        if not provider_info:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown provider: {provider}"
            )
        
        return {
            "provider": provider,
            "configured": provider_info["configured"],
            "model": provider_info.get("model", ""),
            "status": "ready" if provider_info["configured"] else "missing_api_key",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to check LLM status for {provider}", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to check LLM status")
