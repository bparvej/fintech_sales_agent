"""
Agent 11: Sales Insight.

Given opportunities + scores, generates personalized sales insights and pitch strategy.
"""

from __future__ import annotations

import json
from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.llm.llm_factory import LLMFactory
from app.application.agents.opportunity_analysis_agent import OpportunityData


class SalesInsightInput(BaseModel):
    institution_name: str
    opportunities: list[OpportunityData]
    lead_tier: str
    overall_score: float


class SalesInsightOutput(BaseModel):
    executive_summary: str
    pitch_strategy: str
    key_selling_points: list[str] = Field(default_factory=list)
    potential_objections: list[str] = Field(default_factory=list)


class SalesInsightAgent(BaseAgent[SalesInsightInput, SalesInsightOutput]):
    def __init__(self) -> None:
        super().__init__("SalesInsightAgent")
        self.llm = LLMFactory.create()
        
        self.system_prompt = """
        You are an expert FinTech Sales Director.
        Your task is to review the identified sales opportunities for a financial institution and formulate a winning sales strategy.
        
        Respond with valid JSON:
        {
            "executive_summary": "A 2-sentence summary of why this account matters and their current state.",
            "pitch_strategy": "A paragraph explaining how to approach them, what angle to take, and which pain points to highlight.",
            "key_selling_points": ["Point 1", "Point 2", "Point 3"],
            "potential_objections": ["Objection 1 with rebuttal", "Objection 2 with rebuttal"]
        }
        """

    async def execute(self, input_data: SalesInsightInput) -> SalesInsightOutput:
        if not input_data.opportunities:
            return SalesInsightOutput(
                executive_summary="No modernization opportunities identified.",
                pitch_strategy="Monitor account for future changes.",
                key_selling_points=[],
                potential_objections=[]
            )
            
        opps_text = ""
        for i, opp in enumerate(input_data.opportunities):
            opps_text += f"\n{i+1}. {opp.title} ({opp.priority} priority)\n   {opp.description}\n"
            
        prompt = f"""
        Institution: {input_data.institution_name}
        Lead Tier: {input_data.lead_tier.upper()} (Score: {input_data.overall_score}/100)
        
        Identified Opportunities:
        {opps_text}
        
        Provide the sales insight strategy as JSON.
        """
        
        llm_response = await self.llm.complete_json(
            prompt=prompt,
            system_prompt=self.system_prompt
        )
        
        try:
            data = json.loads(llm_response["content"])
            return SalesInsightOutput(**data)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Failed to parse sales insight data: {e}")
