"""
Agent 6: Technology Detection.

Given crawled HTML or text content, detects technologies (frameworks, platforms, APIs)
used by the institution.
"""

from __future__ import annotations

import json
from typing import Any
from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.llm.llm_factory import LLMFactory


class TechnologyDetectionInput(BaseModel):
    institution_name: str
    website_url: str
    pages_content: list[dict[str, str]]  # list of dicts with 'url', 'title', 'text'


class TechnologyDetectionOutput(BaseModel):
    detected_technologies: list[dict[str, Any]] = Field(default_factory=list)
    frontend_technologies: list[str] = Field(default_factory=list)
    backend_technologies: list[str] = Field(default_factory=list)
    cms_platform: str | None = None
    analytics_tools: list[str] = Field(default_factory=list)
    security_features: list[str] = Field(default_factory=list)
    has_mobile_app: bool = False
    has_api: bool = False
    analysis_summary: str | None = None
    digital_maturity_score: float = 0.0


class TechnologyDetectionAgent(BaseAgent[TechnologyDetectionInput, TechnologyDetectionOutput]):
    def __init__(self, llm_provider: str | None = None) -> None:
        super().__init__("TechnologyDetectionAgent")
        self.llm = LLMFactory.create_for_provider_name(llm_provider) if llm_provider else LLMFactory.create()
        
        self.system_prompt = """
        You are an expert technology analyst.
        Your task is to analyze the extracted text from a financial institution's website and identify the technology stack and digital maturity.
        
        Identify:
        - Frontend frameworks (React, Angular, Vue, etc.)
        - Backend technologies if mentioned or implied
        - CMS (WordPress, Drupal, Sitecore, etc.)
        - Analytics tools (Google Analytics, Mixpanel, etc.)
        - Security features (SSL, 2FA, ISO certifications mentioned, etc.)
        - Evidence of mobile apps (links to App Store / Google Play)
        - Evidence of public APIs or developer portals
        
        Score the digital maturity from 0.0 to 10.0 based on the evidence.
        
        Respond with valid JSON matching the exact structure required.
        """

    async def execute(self, input_data: TechnologyDetectionInput) -> TechnologyDetectionOutput:
        # Combine text from pages, limit to avoid token limits
        combined_text = ""
        for page in input_data.pages_content[:5]:  # Just first 5 pages for tech detection
            combined_text += f"\n--- Page: {page.get('url', 'Unknown')} ---\n"
            combined_text += page.get("text", "")[:2000]  # First 2000 chars per page is usually enough
            
        prompt = f"""
        Institution: {input_data.institution_name}
        URL: {input_data.website_url}
        
        Content for Analysis:
        {combined_text}
        
        Please provide the technology detection analysis as JSON.
        """
        
        llm_response = await self.llm.complete_json(
            prompt=prompt,
            system_prompt=self.system_prompt
        )
        
        try:
            data = json.loads(llm_response["content"])
            return TechnologyDetectionOutput(**data)
        except (json.JSONDecodeError, TypeError) as e:
            # Fallback output if parsing fails
            return TechnologyDetectionOutput(
                analysis_summary=f"Failed to parse detailed technology data: {str(e)}",
                digital_maturity_score=3.0
            )
