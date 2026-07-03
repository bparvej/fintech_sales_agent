"""
REST API router for stock exchange operations and filtering.

Provides endpoints for listing, filtering, and searching stock exchanges.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ExchangeModel
from app.infrastructure.database.connection import db_manager
from app.shared.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


async def get_db_session() -> AsyncSession:
    """Dependency to get database session."""
    async with db_manager.get_session() as session:
        yield session


@router.get("/exchanges")
async def list_exchanges(
    country: str = Query(None, description="Filter by country"),
    search: str = Query(None, description="Search exchange name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, list[dict] | int]:
    """
    List stock exchanges with optional filtering and search.
    
    Query Parameters:
    - country: Filter exchanges by country (e.g., "United States")
    - search: Search by exchange name (case-insensitive)
    - skip: Pagination offset (default: 0)
    - limit: Number of results (default: 50, max: 200)
    
    Example:
    - GET /api/v1/exchanges?country=United%20States
    - GET /api/v1/exchanges?search=NYSE
    - GET /api/v1/exchanges?country=United%20States&search=stock
    """
    try:
        query = select(ExchangeModel)
        
        if country:
            query = query.where(ExchangeModel.country == country)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                ExchangeModel.name.ilike(search_term) |
                ExchangeModel.website_url.ilike(search_term)
            )
        
        # Get total count for this filter
        count_query = query.with_only_columns(db_manager._engine)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await session.execute(query)
        exchanges = result.scalars().all()
        
        exchanges_data = [
            {
                "id": exchange.id,
                "name": exchange.name,
                "country": exchange.country,
                "website_url": exchange.website_url,
                "member_list_url": exchange.member_list_url,
                "total_members": exchange.total_members,
                "status": exchange.status,
            }
            for exchange in exchanges
        ]
        
        logger.info(
            "Exchanges listed",
            country=country,
            search=search,
            count=len(exchanges_data),
        )
        
        return {
            "exchanges": exchanges_data,
            "count": len(exchanges_data),
            "skip": skip,
            "limit": limit,
        }
        
    except Exception as exc:
        logger.error("Failed to list exchanges", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve exchanges")


@router.get("/exchanges/{country}")
async def get_exchanges_by_country(
    country: str,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, list[dict] | str]:
    """
    Get all stock exchanges for a specific country.
    
    Example: GET /api/v1/exchanges/United%20States
    """
    try:
        query = select(ExchangeModel).where(ExchangeModel.country == country)
        result = await session.execute(query)
        exchanges = result.scalars().all()
        
        if not exchanges:
            raise HTTPException(
                status_code=404,
                detail=f"No exchanges found for country: {country}"
            )
        
        exchanges_data = [
            {
                "id": exchange.id,
                "name": exchange.name,
                "country": exchange.country,
                "website_url": exchange.website_url,
                "member_list_url": exchange.member_list_url,
                "total_members": exchange.total_members,
                "status": exchange.status,
            }
            for exchange in exchanges
        ]
        
        logger.info(f"Exchanges retrieved for country: {country}", count=len(exchanges_data))
        
        return {"country": country, "exchanges": exchanges_data}
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to get exchanges for country {country}", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve exchanges")


@router.get("/exchanges-search")
async def search_exchanges(
    query: str = Query(..., min_length=2, description="Search query (name, country, website)"),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, list[dict]]:
    """
    Full-text search for stock exchanges.
    
    Searches across name, country, and website URL.
    
    Example: GET /api/v1/exchanges-search?query=york
    """
    try:
        search_term = f"%{query}%"
        
        db_query = select(ExchangeModel).where(
            ExchangeModel.name.ilike(search_term) |
            ExchangeModel.country.ilike(search_term) |
            ExchangeModel.website_url.ilike(search_term)
        ).limit(20)  # Limit search results to 20
        
        result = await session.execute(db_query)
        exchanges = result.scalars().all()
        
        exchanges_data = [
            {
                "id": exchange.id,
                "name": exchange.name,
                "country": exchange.country,
                "website_url": exchange.website_url,
                "member_list_url": exchange.member_list_url,
                "total_members": exchange.total_members,
                "status": exchange.status,
            }
            for exchange in exchanges
        ]
        
        logger.info(f"Exchange search executed", query=query, results=len(exchanges_data))
        
        return {"query": query, "results": exchanges_data, "count": len(exchanges_data)}
        
    except Exception as exc:
        logger.error(f"Failed to search exchanges with query: {query}", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search exchanges")
