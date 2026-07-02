"""
Agent 1: Exchange Discovery.

Given a stock exchange name (and optional country), discovers its official website URL
using web search.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.search.search_provider import SearchProviderFactory


class ExchangeDiscoveryInput(BaseModel):
    exchange_name: str
    country: Optional[str] = None


class ExchangeDiscoveryOutput(BaseModel):
    exchange_name: str
    official_website_url: str
    confidence: float = Field(default=1.0)


class ExchangeDiscoveryAgent(BaseAgent[ExchangeDiscoveryInput, ExchangeDiscoveryOutput]):
    def __init__(self) -> None:
        super().__init__("ExchangeDiscoveryAgent")
        self.search_provider = SearchProviderFactory.create()

    async def execute(self, input_data: ExchangeDiscoveryInput) -> ExchangeDiscoveryOutput:
        query = f'"{input_data.exchange_name}" official website'
        if input_data.country:
            query += f' {input_data.country}'
            
        results = await self.search_provider.search(query, num_results=5)
        
        if not results:
            raise ValueError(f"Could not find official website for {input_data.exchange_name}")
            
        # The first result is highly likely to be the official website
        # In a more robust implementation, we could use an LLM to evaluate the best match
        official_url = results[0].url
        
        return ExchangeDiscoveryOutput(
            exchange_name=input_data.exchange_name,
            official_website_url=official_url,
            confidence=0.9
        )
