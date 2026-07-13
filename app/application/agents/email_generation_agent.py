"""
Agent 12: Email Generation.

Given sales insights and executive profiles, generates personalized outreach emails.
"""

from __future__ import annotations

import json
from pydantic import BaseModel, Field

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.llm.llm_factory import LLMFactory
from app.application.agents.sales_insight_agent import SalesInsightOutput
from app.application.agents.executive_discovery_agent import ExecutiveInfo


class EmailGenerationInput(BaseModel):
    institution_name: str
    executives: list[ExecutiveInfo]
    sales_insight: SalesInsightOutput


class EmailDraft(BaseModel):
    recipient_name: str
    recipient_title: str
    subject_line: str
    email_body: str


class EmailGenerationOutput(BaseModel):
    emails: list[EmailDraft] = Field(default_factory=list)


class EmailGenerationAgent(BaseAgent[EmailGenerationInput, EmailGenerationOutput]):
    def __init__(self, llm_provider: str | None = None) -> None:
        super().__init__("EmailGenerationAgent")
        self.llm = LLMFactory.create_for_provider_name(llm_provider) if llm_provider else LLMFactory.create()
        
        self.system_prompt = """
        You are an expert enterprise software sales executive.
        Your task is to write highly personalized, consultative cold outreach emails to C-level executives.
        
        Rules:
        - Be concise, direct, and professional.
        - NEVER sound like a generic marketing template.
        - Reference the specific pain points / opportunities identified.
        - Ask for a brief 15-minute introductory call.
        - Keep it under 150 words.
        
        Respond with valid JSON:
        {
            "emails": [
                {
                    "recipient_name": "Name",
                    "recipient_title": "Title",
                    "subject_line": "Compelling subject line",
                    "email_body": "The full text of the email"
                }
            ]
        }
        """

    async def execute(self, input_data: EmailGenerationInput) -> EmailGenerationOutput:
        if not input_data.executives:
            return EmailGenerationOutput()
            
        execs_text = ""
        for i, ex in enumerate(input_data.executives[:3]): # Max 3 emails
            execs_text += f"- {ex.name}, {ex.title}\n"
            
        points_text = "\n".join([f"- {p}" for p in input_data.sales_insight.key_selling_points])
            
        prompt = f"""
        Institution: {input_data.institution_name}
        
        Executives to email:
        {execs_text}
        
        Pitch Strategy: {input_data.sales_insight.pitch_strategy}
        
        Key Points to Highlight:
        {points_text}
        
        Generate one highly personalized email for each executive in JSON format.
        """
        
        llm_response = await self.llm.complete_json(
            prompt=prompt,
            system_prompt=self.system_prompt
        )
        
        try:
            data = json.loads(llm_response["content"])
            emails = []
            
            for draft in data.get("emails", []):
                if draft.get("recipient_name") and draft.get("email_body"):
                    emails.append(EmailDraft(**draft))
                    
            return EmailGenerationOutput(emails=emails)
            
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse email drafts: {e}")
