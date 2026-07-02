"""
Agent 2: Member List Discovery.

Given a stock exchange website URL, finds the specific page containing the 
member/broker/TREC holder list.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import urljoin
from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.crawler.web_crawler import WebCrawler
from app.infrastructure.llm.llm_factory import LLMFactory


class MemberListDiscoveryInput(BaseModel):
    exchange_name: str
    exchange_url: str


class MemberListDiscoveryOutput(BaseModel):
    member_list_url: str
    confidence: float = Field(default=1.0)
    reasoning: Optional[str] = None


class MemberListDiscoveryAgent(BaseAgent[MemberListDiscoveryInput, MemberListDiscoveryOutput]):
    def __init__(self) -> None:
        super().__init__("MemberListDiscoveryAgent")
        self.crawler = WebCrawler()
        self.llm = LLMFactory.create()
        
        self.system_prompt = """
        You are an expert at analyzing stock exchange websites.
        Your task is to identify the URL of the page that contains the list of brokers / members / TREC holders.
        
        Look for links containing words like:
        - Members
        - Brokers
        - TREC Holders
        - Member Directory
        - Market Participants
        
        Analyze the provided list of links from the exchange homepage and determine the most likely URL for the member list.
        
        Respond with valid JSON:
        {
            "member_list_url": "the absolute URL",
            "confidence": 0.0 to 1.0,
            "reasoning": "Why you chose this URL"
        }
        """

    async def execute(self, input_data: MemberListDiscoveryInput) -> MemberListDiscoveryOutput:
        # Crawl the homepage to get links
        result = await self.crawler.crawl_page(input_data.exchange_url)
        
        if not result.is_success:
            raise ValueError(f"Failed to crawl exchange homepage: {input_data.exchange_url}")
            
        links = result.links
        
        if not links:
            raise ValueError(f"No links found on exchange homepage: {input_data.exchange_url}")
            
        # Format links for the LLM
        links_text = "\n".join(links)
        
        prompt = f"""
        Exchange: {input_data.exchange_name}
        Homepage URL: {input_data.exchange_url}
        
        Available Links:
        {links_text}
        """
        
        llm_response = await self.llm.complete_json(
            prompt=prompt,
            system_prompt=self.system_prompt
        )
        
        import json
        try:
            data = json.loads(llm_response["content"])
            
            # Ensure the URL is absolute
            member_url = data.get("member_list_url", "")
            if member_url and not member_url.startswith("http"):
                member_url = urljoin(input_data.exchange_url, member_url)
                
            return MemberListDiscoveryOutput(
                member_list_url=member_url,
                confidence=float(data.get("confidence", 0.0)),
                reasoning=data.get("reasoning")
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse LLM response: {e}")
