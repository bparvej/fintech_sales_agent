"""
Database seeders for initial data population.

Provides functions to seed stock exchanges, countries, and other reference data.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ExchangeModel


STOCK_EXCHANGES_SEED_DATA = [
    # North America
    {
        "name": "New York Stock Exchange (NYSE)",
        "country": "United States",
        "website_url": "https://www.nyse.com",
        "member_list_url": "https://www.nyse.com/about/memberships",
        "total_members": 2400,
    },
    {
        "name": "NASDAQ",
        "country": "United States",
        "website_url": "https://www.nasdaq.com",
        "member_list_url": "https://www.nasdaq.com/market-activity/market-participants",
        "total_members": 3500,
    },
    {
        "name": "Toronto Stock Exchange (TSX)",
        "country": "Canada",
        "website_url": "https://www.tsx.com",
        "member_list_url": "https://www.tsx.com/trading/membership",
        "total_members": 1300,
    },
    # Europe
    {
        "name": "London Stock Exchange (LSE)",
        "country": "United Kingdom",
        "website_url": "https://www.londonstockexchange.com",
        "member_list_url": "https://www.londonstockexchange.com/news-and-events/market-news",
        "total_members": 2800,
    },
    {
        "name": "Euronext Paris",
        "country": "France",
        "website_url": "https://www.euronext.com",
        "member_list_url": "https://www.euronext.com/en/about/members",
        "total_members": 1100,
    },
    {
        "name": "Deutsche Börse (Frankfurt)",
        "country": "Germany",
        "website_url": "https://www.deutsche-boerse.com",
        "member_list_url": "https://www.deutsche-boerse.com/dbg-en/about-us/members",
        "total_members": 1600,
    },
    {
        "name": "SIX Swiss Exchange",
        "country": "Switzerland",
        "website_url": "https://www.six-group.com/en/products-services/trading/trading-post-trade/securities-trading.html",
        "member_list_url": "https://www.six-group.com/en/about-us/structure/participants.html",
        "total_members": 300,
    },
    {
        "name": "Borsa Italiana (Milan)",
        "country": "Italy",
        "website_url": "https://www.borsaitaliana.it",
        "member_list_url": "https://www.borsaitaliana.it/borsaitaliana/emi/intermediari.html",
        "total_members": 350,
    },
    {
        "name": "BME - Bolsas y Mercados Españoles",
        "country": "Spain",
        "website_url": "https://www.bolsasymercados.es",
        "member_list_url": "https://www.bolsasymercados.es/ing/Empresas-cotizadas",
        "total_members": 420,
    },
    # Asia-Pacific
    {
        "name": "Tokyo Stock Exchange (TSE)",
        "country": "Japan",
        "website_url": "https://www.jpx.co.jp",
        "member_list_url": "https://www.jpx.co.jp/english/",
        "total_members": 2100,
    },
    {
        "name": "Hong Kong Exchanges and Clearing (HKEX)",
        "country": "Hong Kong",
        "website_url": "https://www.hkex.com.hk",
        "member_list_url": "https://www.hkex.com.hk/eng/Market/Participants/",
        "total_members": 500,
    },
    {
        "name": "Shanghai Stock Exchange (SSE)",
        "country": "China",
        "website_url": "https://www.sse.com.cn",
        "member_list_url": "https://www.sse.com.cn/",
        "total_members": 1900,
    },
    {
        "name": "Singapore Exchange (SGX)",
        "country": "Singapore",
        "website_url": "https://www.sgx.com",
        "member_list_url": "https://www.sgx.com/",
        "total_members": 420,
    },
    {
        "name": "National Stock Exchange of India (NSE)",
        "country": "India",
        "website_url": "https://www.nseindia.com",
        "member_list_url": "https://www.nseindia.com/",
        "total_members": 2300,
    },
    {
        "name": "Australian Securities Exchange (ASX)",
        "country": "Australia",
        "website_url": "https://www.asx.com.au",
        "member_list_url": "https://www.asx.com.au/",
        "total_members": 800,
    },
    # Latin America
    {
        "name": "B3 - Brasil Bolsa Balcão",
        "country": "Brazil",
        "website_url": "https://www.b3.com.br",
        "member_list_url": "https://www.b3.com.br/",
        "total_members": 180,
    },
    {
        "name": "Bolsa de Valores de Colombia",
        "country": "Colombia",
        "website_url": "https://www.bvc.com.co",
        "member_list_url": "https://www.bvc.com.co/",
        "total_members": 90,
    },
    # Middle East
    {
        "name": "Saudi Arabia Stock Exchange (TADAWUL)",
        "country": "Saudi Arabia",
        "website_url": "https://www.tadawul.com.sa",
        "member_list_url": "https://www.tadawul.com.sa/",
        "total_members": 200,
    },
    {
        "name": "Nasdaq Dubai",
        "country": "United Arab Emirates",
        "website_url": "https://www.nasdaqdubai.com",
        "member_list_url": "https://www.nasdaqdubai.com/",
        "total_members": 120,
    },
]


async def seed_stock_exchanges(session: AsyncSession) -> None:
    """
    Seed the database with initial stock exchange data.
    
    Only inserts if exchanges table is empty.
    """
    try:
        # Check if data already exists
        result = await session.execute("SELECT COUNT(*) as count FROM exchanges")
        count = result.scalar()
        
        if count > 0:
            print(f"✓ Stock exchanges already seeded ({count} records)")
            return
        
        # Prepare seed data with IDs
        exchanges_to_insert = [
            {
                "id": str(uuid.uuid4()),
                "name": data["name"],
                "country": data["country"],
                "website_url": data["website_url"],
                "member_list_url": data["member_list_url"],
                "total_members": data["total_members"],
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            for data in STOCK_EXCHANGES_SEED_DATA
        ]
        
        # Insert all exchanges
        stmt = insert(ExchangeModel).values(exchanges_to_insert)
        result = await session.execute(stmt)
        await session.commit()
        
        print(f"✓ Successfully seeded {len(exchanges_to_insert)} stock exchanges")
        
    except Exception as exc:
        await session.rollback()
        print(f"✗ Error seeding stock exchanges: {exc}")
        raise


def get_countries_list() -> list[str]:
    """Get unique list of countries from seed data."""
    countries = sorted(set(data["country"] for data in STOCK_EXCHANGES_SEED_DATA))
    return countries


def get_llm_models_for_provider(provider: str) -> list[str]:
    """Get available models for a given LLM provider."""
    models_map = {
        "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "deepseek": ["deepseek-chat", "deepseek-coder"],
        "qwen": ["qwen-plus", "qwen-turbo", "qwen-long"],
        "ollama": ["llama3", "llama2", "mistral"],
        "gemini": ["gemini-2.5-flash", "gemini-2.0-pro"],
    }
    return models_map.get(provider.lower(), [])
