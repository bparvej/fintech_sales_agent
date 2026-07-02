"""
Agent 10: Lead Scoring.

Given all data, scores the institution as a sales lead using deterministic logic.
No LLM required.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.application.agents.opportunity_analysis_agent import OpportunityData


class LeadScoringInput(BaseModel):
    has_website: bool
    executives_found: int
    tech_score: float  # from technology detection
    opportunities: list[OpportunityData]


class LeadScoringOutput(BaseModel):
    overall_score: float
    technology_score: float
    digital_presence_score: float
    opportunity_score: float
    accessibility_score: float
    scoring_factors: dict[str, float] = Field(default_factory=dict)
    tier: str
    recommendation: str


class LeadScoringAgent(BaseAgent[LeadScoringInput, LeadScoringOutput]):
    def __init__(self) -> None:
        super().__init__("LeadScoringAgent")

    async def execute(self, input_data: LeadScoringInput) -> LeadScoringOutput:
        # Deterministic scoring algorithm
        
        # 1. Digital Presence (0-20)
        dp_score = 20.0 if input_data.has_website else 0.0
        
        # 2. Technology (0-20)
        # We invert the tech maturity score: lower maturity = higher need/lead score
        # Assume input tech_score is 0-10
        tech_need = max(0.0, 10.0 - input_data.tech_score)
        tech_score = tech_need * 2.0  # Scale to 20
        
        # 3. Opportunities (0-40)
        opp_score = 0.0
        for opp in input_data.opportunities:
            weight = {
                "critical": 15.0,
                "high": 10.0,
                "medium": 5.0,
                "low": 2.0
            }.get(opp.priority, 5.0)
            opp_score += weight
        opp_score = min(40.0, opp_score)  # Cap at 40
        
        # 4. Accessibility / Decision Makers (0-20)
        # Found executives means we have someone to pitch to
        acc_score = min(20.0, input_data.executives_found * 5.0)
        
        # Calculate Total
        total_score = dp_score + tech_score + opp_score + acc_score
        
        # Determine Tier & Recommendation
        if total_score >= 80:
            tier = "hot"
            recommendation = "Immediate outreach highly recommended. High number of modernization opportunities and accessible decision makers."
        elif total_score >= 50:
            tier = "warm"
            recommendation = "Good prospect. Personalize outreach based on the identified opportunities."
        else:
            tier = "cold"
            recommendation = "Low priority. Add to nurture sequence or re-evaluate in 6 months."
            
        factors = {
            "has_website": 1.0 if input_data.has_website else 0.0,
            "executives_count": float(input_data.executives_found),
            "opportunity_count": float(len(input_data.opportunities)),
            "tech_maturity": float(input_data.tech_score)
        }
            
        return LeadScoringOutput(
            overall_score=total_score,
            technology_score=tech_score,
            digital_presence_score=dp_score,
            opportunity_score=opp_score,
            accessibility_score=acc_score,
            scoring_factors=factors,
            tier=tier,
            recommendation=recommendation
        )
