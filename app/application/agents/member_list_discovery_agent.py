"""
Agent 2: Member List Discovery.

Given a stock exchange website URL, finds the specific page containing the 
member/broker/TREC holder list.
Uses crawling + LLM analysis, falls back to web search if needed.
"""

from __future__ import annotations

import json
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.crawler.web_crawler import WebCrawler
from app.infrastructure.llm.llm_factory import LLMFactory
from app.infrastructure.search.search_provider import SearchProviderFactory
from app.shared.logging.logger import get_logger

logger = get_logger(__name__)


class MemberListDiscoveryInput(BaseModel):
    exchange_name: str
    exchange_url: str


class MemberListDiscoveryOutput(BaseModel):
    member_list_url: str
    confidence: float = Field(default=1.0)
    reasoning: Optional[str] = None


class MemberListDiscoveryAgent(BaseAgent[MemberListDiscoveryInput, MemberListDiscoveryOutput]):
    def __init__(self, llm_provider: str | None = None) -> None:
        super().__init__("MemberListDiscoveryAgent")
        self.crawler = WebCrawler()
        self.search_provider = SearchProviderFactory.create()
        self.llm = LLMFactory.create_for_provider_name(llm_provider) if llm_provider else LLMFactory.create()
        
        self.system_prompt = """
        You are an expert at analyzing stock exchange websites.
        Your task is to identify the URL of the page that contains the list of brokers / members / TREC holders.
        
        Look for links containing words like:
        - Members / Member Directory / Member List
        - Brokers / Broker List
        - TREC Holders / T.R.E.C. Holders
        - Market Participants
        - Participants
        - Member Firms
        - Trading Members
        - Stockbrokers
        
        The link text is provided in format: URL | LINK TEXT
        
        Respond with valid JSON:
        {
            "member_list_url": "the absolute URL (must be a specific page, NOT the homepage)",
            "confidence": 0.0 to 1.0 (lower if not confident),
            "reasoning": "Why you chose this URL based on link text"
        }
        
        IMPORTANT: If none of the links clearly point to a member/broker list, set confidence to 0.
        """

    async def _search_member_list(self, exchange_name: str) -> str | None:
        """Use web search to find the member list page as fallback."""
        queries = [
            f'"{exchange_name}" "TREC holders" directory',
            f'"{exchange_name}" "member list" brokers',
            f'"{exchange_name}" "member directory"',
            f'"{exchange_name}" brokers list',
        ]
        for query in queries:
            results = await self.search_provider.search(query, num_results=5)
            for r in results:
                url = r.url
                if any(kw in r.title.lower() or kw in r.snippet.lower()
                       for kw in ["trec", "member", "broker", "participant"]):
                    return url
        return None

    async def execute(self, input_data: MemberListDiscoveryInput) -> MemberListDiscoveryOutput:
        # Crawl the homepage to get links + text
        result = await self.crawler.crawl_page(input_data.exchange_url)
        
        if not result.is_success:
            raise ValueError(f"Failed to crawl exchange homepage: {input_data.exchange_url}")
            
        # Build links with anchor text from raw HTML
        soup = BeautifulSoup(result.html, "html.parser")
        link_entries = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(input_data.exchange_url, href)
            if not full_url.startswith("http"):
                continue
            text = a_tag.get_text(strip=True)[:60]
            if text:
                link_entries.append(f"{full_url} | {text}")
            else:
                link_entries.append(full_url)
        
        if not link_entries:
            raise ValueError(f"No links found on exchange homepage: {input_data.exchange_url}")
            
        links_text = "\n".join(link_entries[:80])  # Limit to 80 links
        
        prompt = f"""
        Exchange: {input_data.exchange_name}
        Homepage URL: {input_data.exchange_url}
        
        Available Links (URL | Link Text):
        {links_text}
        """
        
        llm_response = await self.llm.complete_json(
            prompt=prompt,
            system_prompt=self.system_prompt
        )
        
        try:
            data = json.loads(llm_response["content"])
            member_url = data.get("member_list_url", "")
            confidence = float(data.get("confidence", 0.0))
            
            if member_url and not member_url.startswith("http"):
                member_url = urljoin(input_data.exchange_url, member_url)
            
            # If LLM returned homepage or low confidence, try search fallback
            exchange_domain = urlparse(input_data.exchange_url).netloc
            member_domain = urlparse(member_url).netloc if member_url else ""
            
            if (not member_url or
                member_url.rstrip("/") == input_data.exchange_url.rstrip("/") or
                confidence < 0.3 or
                member_domain != exchange_domain):
                
                logger.info("LLM could not find member list, trying search fallback", exchange=input_data.exchange_name)
                search_url = await self._search_member_list(input_data.exchange_name)
                if search_url:
                    return MemberListDiscoveryOutput(
                        member_list_url=search_url,
                        confidence=0.7,
                        reasoning=f"Found via web search: {search_url}"
                    )
                raise ValueError(
                    f"Could not find member list page for {input_data.exchange_name}. "
                    f"The exchange website may use JavaScript navigation that requires manual inspection. "
                    f"Try visiting {input_data.exchange_url} and finding the member/broker/TREC holder directory."
                )
                
            return MemberListDiscoveryOutput(
                member_list_url=member_url,
                confidence=confidence,
                reasoning=data.get("reasoning")
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse LLM response: {e}")
