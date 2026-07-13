"""
Agent 7: Executive Discovery.

Given company information and crawled content, discovers C-level executives 
and tech leaders (CEO, CTO, CIO, IT Head, etc.).
"""

from __future__ import annotations

import json
from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.llm.llm_factory import LLMFactory
from app.infrastructure.search.search_provider import SearchProviderFactory


class ExecutiveDiscoveryInput(BaseModel):
    institution_name: str
    website_url: str
    pages_content: list[dict[str, str]]


class ExecutiveInfo(BaseModel):
    name: str
    title: str
    source: str
    confidence: float = 1.0


class ExecutiveDiscoveryOutput(BaseModel):
    executives: list[ExecutiveInfo] = Field(default_factory=list)


class ExecutiveDiscoveryAgent(BaseAgent[ExecutiveDiscoveryInput, ExecutiveDiscoveryOutput]):
    def __init__(self, llm_provider: str | None = None) -> None:
        super().__init__("ExecutiveDiscoveryAgent")
        self.llm = LLMFactory.create_for_provider_name(llm_provider) if llm_provider else LLMFactory.create()
        self.search_provider = SearchProviderFactory.create()
        
        self.system_prompt = """
        You are an expert at identifying key decision-makers in financial institutions.
        Your task is to identify C-level executives and technology leaders.
        
        Look for:
        - Chief Executive Officer (CEO)
        - Managing Director (MD)
        - Chief Technology Officer (CTO)
        - Chief Information Officer (CIO)
        - Head of IT / Head of Technology
        
        Analyze the provided text to find names and titles.
        If you find none in the text, return an empty list.
        
        Respond with valid JSON:
        {
            "executives": [
                {
                    "name": "Full Name",
                    "title": "Exact Title",
                    "source": "Where you found it (e.g., website page title)",
                    "confidence": 0.0 to 1.0
                }
            ]
        }
        """

    async def execute(self, input_data: ExecutiveDiscoveryInput) -> ExecutiveDiscoveryOutput:
        # Step 1: Try to find from website content
        combined_text = ""
        # Prioritize about-us, team, management pages if possible, else just first few pages
        about_pages = [p for p in input_data.pages_content if "about" in p.get("url", "").lower() or "team" in p.get("url", "").lower() or "management" in p.get("url", "").lower()]
        
        pages_to_analyze = about_pages if about_pages else input_data.pages_content[:3]
        
        for page in pages_to_analyze:
            combined_text += f"\n--- Page: {page.get('url', 'Unknown')} ---\n"
            combined_text += page.get("text", "")[:3000]
            
        prompt = f"""
        Institution: {input_data.institution_name}
        
        Content for Analysis:
        {combined_text}
        """
        
        llm_response = await self.llm.complete_json(
            prompt=prompt,
            system_prompt=self.system_prompt
        )
        
        try:
            data = json.loads(llm_response["content"])
            executives = []
            
            for ex in data.get("executives", []):
                if ex.get("name") and ex.get("title"):
                    executives.append(ExecutiveInfo(**ex))
                    
            # If we didn't find enough, we could use SearchProvider here to supplement
            # e.g., search('"{institution_name}" CEO OR CTO OR CIO site:linkedin.com')
            # But we'll keep it simple for now and rely on website text.
                    
            return ExecutiveDiscoveryOutput(executives=executives)
            
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse executive data: {e}")
