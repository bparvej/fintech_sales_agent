"""
Agent 9: Opportunity Analysis.

Given tech profile and company data, identifies software modernization opportunities.
"""

from __future__ import annotations

import json
from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.domain.value_objects.opportunity_type import OpportunityType
from app.infrastructure.llm.llm_factory import LLMFactory


class TechProfileData(BaseModel):
    frontend: list[str]
    backend: list[str]
    has_mobile_app: bool
    has_api: bool
    score: float


class OpportunityAnalysisInput(BaseModel):
    institution_name: str
    description: str | None
    tech_profile: TechProfileData


class OpportunityData(BaseModel):
    opportunity_type: OpportunityType
    title: str
    description: str
    priority: str
    confidence_score: float
    reasoning: str
    recommended_approach: str


class OpportunityAnalysisOutput(BaseModel):
    opportunities: list[OpportunityData] = Field(default_factory=list)


class OpportunityAnalysisAgent(BaseAgent[OpportunityAnalysisInput, OpportunityAnalysisOutput]):
    def __init__(self, llm_provider: str | None = None) -> None:
        super().__init__("OpportunityAnalysisAgent")
        # We need the smart model for reasoning
        self.llm = LLMFactory.create_for_provider_name(llm_provider) if llm_provider else LLMFactory.create()
        
        # Valid types for prompt guidance
        valid_types = [t.value for t in OpportunityType]
        
        self.system_prompt = f"""
        You are an expert FinTech Sales Engineer and Solutions Architect.
        Your task is to analyze a financial institution's technology profile and identify sales opportunities for modernization.
        
        Look for gaps:
        - No mobile app -> Mobile App Development
        - Old frontend frameworks (e.g., jQuery, none) -> Website Redesign / Platform Modernization
        - No public APIs -> API Integration
        - Low digital maturity score -> Comprehensive Digital Transformation
        
        Valid opportunity types MUST be one of: {valid_types}
        
        Priority MUST be one of: "low", "medium", "high", "critical"
        
        Respond with valid JSON:
        {{
            "opportunities": [
                {{
                    "opportunity_type": "exact_type_from_list",
                    "title": "Short catchy title",
                    "description": "Detailed description of the opportunity",
                    "priority": "high",
                    "confidence_score": 0.0 to 1.0,
                    "reasoning": "Why you identified this",
                    "recommended_approach": "How to pitch this"
                }}
            ]
        }}
        """

    async def execute(self, input_data: OpportunityAnalysisInput) -> OpportunityAnalysisOutput:
        prompt = f"""
        Institution: {input_data.institution_name}
        Description: {input_data.description or 'None available'}
        
        Technology Profile:
        - Frontend: {', '.join(input_data.tech_profile.frontend) if input_data.tech_profile.frontend else 'None detected'}
        - Backend: {', '.join(input_data.tech_profile.backend) if input_data.tech_profile.backend else 'None detected'}
        - Has Mobile App: {input_data.tech_profile.has_mobile_app}
        - Has Public API: {input_data.tech_profile.has_api}
        - Maturity Score: {input_data.tech_profile.score}/10
        
        Identify at least 2 strong sales opportunities based on this profile.
        """
        
        llm_response = await self.llm.complete_json(
            prompt=prompt,
            system_prompt=self.system_prompt
        )
        
        try:
            data = json.loads(llm_response["content"])
            opportunities = []
            
            for opp in data.get("opportunities", []):
                # Ensure type is valid, fallback to OTHER if not
                try:
                    opp_type = OpportunityType(opp.get("opportunity_type"))
                except ValueError:
                    opp_type = OpportunityType.OTHER
                    
                opp["opportunity_type"] = opp_type
                opportunities.append(OpportunityData(**opp))
                
            return OpportunityAnalysisOutput(opportunities=opportunities)
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to parse opportunity analysis: {e}")
