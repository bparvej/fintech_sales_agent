"""
Agent 8: Profile Resolver.

Given executive names, resolves their LinkedIn/Facebook professional profile URLs
via web search.
"""

from __future__ import annotations

import asyncio
from typing import Optional
from pydantic import BaseModel

from app.application.agents.base_agent import BaseAgent
from app.infrastructure.search.search_provider import SearchProviderFactory


class ExecutiveQuery(BaseModel):
    name: str
    title: str


class ProfileResolverInput(BaseModel):
    institution_name: str
    executives: list[ExecutiveQuery]


class ResolvedProfile(BaseModel):
    name: str
    title: str
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None


class ProfileResolverOutput(BaseModel):
    resolved_profiles: list[ResolvedProfile]


class ProfileResolverAgent(BaseAgent[ProfileResolverInput, ProfileResolverOutput]):
    def __init__(self) -> None:
        super().__init__("ProfileResolverAgent")
        self.search_provider = SearchProviderFactory.create()

    async def _resolve_single_profile(self, inst_name: str, exec_query: ExecutiveQuery) -> ResolvedProfile:
        # Search for LinkedIn
        li_query = f'"{exec_query.name}" "{exec_query.title}" "{inst_name}" site:linkedin.com/in'
        li_results = await self.search_provider.search(li_query, num_results=3)
        
        linkedin_url = None
        if li_results:
            linkedin_url = li_results[0].url
            
        # FB search is often less reliable for professional attribution, but requested
        fb_query = f'"{exec_query.name}" "{exec_query.title}" "{inst_name}" site:facebook.com'
        fb_results = await self.search_provider.search(fb_query, num_results=3)
        
        facebook_url = None
        if fb_results:
            facebook_url = fb_results[0].url
            
        return ResolvedProfile(
            name=exec_query.name,
            title=exec_query.title,
            linkedin_url=linkedin_url,
            facebook_url=facebook_url
        )

    async def execute(self, input_data: ProfileResolverInput) -> ProfileResolverOutput:
        tasks = []
        for exec_q in input_data.executives:
            tasks.append(self._resolve_single_profile(input_data.institution_name, exec_q))
            
        # Run searches concurrently
        resolved = await asyncio.gather(*tasks)
        
        return ProfileResolverOutput(resolved_profiles=list(resolved))
