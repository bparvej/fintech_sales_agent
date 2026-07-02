"""
Agent 3: Broker Extraction.

Given a member list URL, extracts the names and any other available 
information about the brokerage firms.
"""

from __future__ import annotations

import json
from typing import Optional
from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.crawler.web_crawler import WebCrawler
from app.infrastructure.llm.llm_factory import LLMFactory


class BrokerExtractionInput(BaseModel):
    exchange_name: str
    member_list_url: str


class BrokerInfo(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = None


class BrokerExtractionOutput(BaseModel):
    brokers: list[BrokerInfo] = Field(default_factory=list)
    extraction_confidence: float = Field(default=1.0)


class BrokerExtractionAgent(BaseAgent[BrokerExtractionInput, BrokerExtractionOutput]):
    def __init__(self) -> None:
        super().__init__("BrokerExtractionAgent")
        self.crawler = WebCrawler()
        
        # We use a cheaper model for extraction tasks
        settings = __import__("app.shared.config.settings").shared.config.settings.get_settings()
        # In a real implementation, we'd use the configured 'mini' model, 
        # but for simplicity we'll just use the factory default.
        self.llm = LLMFactory.create()
        
        self.system_prompt = """
        You are an expert at extracting structured data from HTML content.
        Your task is to extract a list of brokerage firms (members/TREC holders) from the provided text.
        
        Extract as much information as possible for each firm, including:
        - Name (Required)
        - Address
        - Phone
        - Email
        - Website URL
        - Description
        
        Respond with valid JSON:
        {
            "brokers": [
                {
                    "name": "Firm Name",
                    "address": "...",
                    "phone": "...",
                    "email": "...",
                    "website_url": "...",
                    "description": "..."
                }
            ],
            "extraction_confidence": 0.0 to 1.0
        }
        """

    async def execute(self, input_data: BrokerExtractionInput) -> BrokerExtractionOutput:
        # Crawl the member list page
        result = await self.crawler.crawl_page(input_data.member_list_url)
        
        if not result.is_success:
            raise ValueError(f"Failed to crawl member list page: {input_data.member_list_url}")
            
        text = result.text
        
        if not text:
            raise ValueError(f"No text extracted from member list page: {input_data.member_list_url}")
            
        prompt = f"""
        Exchange: {input_data.exchange_name}
        URL: {input_data.member_list_url}
        
        Content:
        {text}
        """
        
        llm_response = await self.llm.complete_json(
            prompt=prompt,
            system_prompt=self.system_prompt,
            # Extraction tasks can be longer
            max_tokens=8192
        )
        
        try:
            data = json.loads(llm_response["content"])
            brokers_data = data.get("brokers", [])
            
            brokers = []
            for b in brokers_data:
                if b.get("name"):
                    brokers.append(BrokerInfo(**b))
                    
            return BrokerExtractionOutput(
                brokers=brokers,
                extraction_confidence=float(data.get("extraction_confidence", 0.0))
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse LLM response: {e}")
