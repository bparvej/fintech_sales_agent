"""
Agent 4: Website Discovery.

Given a brokerage firm name, discovers its official website URL
using web search.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.search.search_provider import SearchProviderFactory


class WebsiteDiscoveryInput(BaseModel):
    broker_name: str
    country: Optional[str] = None


class WebsiteDiscoveryOutput(BaseModel):
    broker_name: str
    official_website_url: str
    confidence: float = Field(default=1.0)


class WebsiteDiscoveryAgent(BaseAgent[WebsiteDiscoveryInput, WebsiteDiscoveryOutput]):
    def __init__(self) -> None:
        super().__init__("WebsiteDiscoveryAgent")
        self.search_provider = SearchProviderFactory.create()

    async def execute(self, input_data: WebsiteDiscoveryInput) -> WebsiteDiscoveryOutput:
        query = f'"{input_data.broker_name}" official website brokerage'
        if input_data.country:
            query += f' {input_data.country}'
            
        results = await self.search_provider.search(query, num_results=5)
        
        if not results:
            raise ValueError(f"Could not find official website for broker {input_data.broker_name}")
            
        # The first result is highly likely to be the official website
        # In a robust implementation, we would use an LLM to verify the domain name
        official_url = results[0].url
        
        return WebsiteDiscoveryOutput(
            broker_name=input_data.broker_name,
            official_website_url=official_url,
            confidence=0.85
        )
