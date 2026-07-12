"""
Pipeline Orchestrator.

Chains all 12 AI agents into a single workflow.
Manages database persistence between steps and broadcasts progress via WebSockets.
"""

from __future__ import annotations

import asyncio
import uuid
import traceback
from typing import Any

from app.domain.entities.exchange import Exchange
from app.domain.entities.institution import Institution
from app.domain.entities.technology_profile import TechnologyProfile
from app.domain.entities.sales_opportunity import SalesOpportunity
from app.domain.entities.lead_score import LeadScore
from app.domain.entities.executive import Executive
from app.domain.entities.sales_report import SalesReport
from app.domain.entities.audit_log import AuditLog
from app.domain.value_objects.analysis_status import AnalysisStatus
from app.domain.value_objects.institution_type import InstitutionType
from app.infrastructure.database.connection import db_manager
from app.infrastructure.database.repositories.sql_repositories import (
    ExchangeRepository,
    InstitutionRepository,
    TechnologyProfileRepository,
    SalesOpportunityRepository,
    LeadScoreRepository,
    ExecutiveRepository,
    SalesReportRepository,
    AuditLogRepository,
)
from app.application.agents.exchange_discovery_agent import ExchangeDiscoveryAgent, ExchangeDiscoveryInput
from app.application.agents.member_list_discovery_agent import MemberListDiscoveryAgent, MemberListDiscoveryInput
from app.application.agents.broker_extraction_agent import BrokerExtractionAgent, BrokerExtractionInput
from app.application.agents.website_discovery_agent import WebsiteDiscoveryAgent, WebsiteDiscoveryInput
from app.application.agents.website_crawler_agent import WebsiteCrawlerAgent, WebsiteCrawlerInput
from app.application.agents.technology_detection_agent import TechnologyDetectionAgent, TechnologyDetectionInput
from app.application.agents.executive_discovery_agent import ExecutiveDiscoveryAgent, ExecutiveDiscoveryInput
from app.application.agents.profile_resolver_agent import ProfileResolverAgent, ProfileResolverInput, ExecutiveQuery
from app.application.agents.opportunity_analysis_agent import OpportunityAnalysisAgent, OpportunityAnalysisInput, TechProfileData
from app.application.agents.lead_scoring_agent import LeadScoringAgent, LeadScoringInput
from app.application.agents.sales_insight_agent import SalesInsightAgent, SalesInsightInput
from app.application.agents.email_generation_agent import EmailGenerationAgent, EmailGenerationInput

from app.shared.logging.logger import get_logger

logger = get_logger(__name__)


class PipelineOrchestrator:
    """Master orchestrator for the FinTech Sales Intelligence pipeline."""

    def __init__(self, job_id: uuid.UUID, exchange_name: str, country: str | None = None, llm_provider: str | None = None, search_provider: str | None = None) -> None:
        self.job_id = job_id
        self.exchange_name = exchange_name
        self.country = country
        self.llm_provider = llm_provider
        self.search_provider = search_provider
        
        # Agents
        self.agent_exchange = ExchangeDiscoveryAgent()
        self.agent_members = MemberListDiscoveryAgent()
        self.agent_brokers = BrokerExtractionAgent()
        self.agent_web_discover = WebsiteDiscoveryAgent()
        self.agent_crawler = WebsiteCrawlerAgent()
        self.agent_tech = TechnologyDetectionAgent()
        self.agent_execs = ExecutiveDiscoveryAgent()
        self.agent_profiles = ProfileResolverAgent()
        self.agent_opportunities = OpportunityAnalysisAgent()
        self.agent_scoring = LeadScoringAgent()
        self.agent_insights = SalesInsightAgent()
        self.agent_email = EmailGenerationAgent()
        
        # State
        self.status = AnalysisStatus.PENDING
        self.error: str | None = None
        self.exchange_id: uuid.UUID | None = None
        
        # Global active jobs registry for websocket access
        # In a real app, use Redis pub/sub
        self.__class__._active_jobs[str(job_id)] = self

    # Class-level registry
    _active_jobs: dict[str, "PipelineOrchestrator"] = {}
    
    @classmethod
    def get_job(cls, job_id: str) -> "PipelineOrchestrator" | None:
        return cls._active_jobs.get(job_id)

    async def update_status(self, new_status: AnalysisStatus, db_session) -> None:
        """Update pipeline status and persist to exchange."""
        self.status = new_status
        logger.info("Pipeline status updated", job_id=str(self.job_id), status=new_status.value)
        
        if self.exchange_id and db_session:
            repo = ExchangeRepository(db_session)
            exchange = await repo.get_by_id(self.exchange_id)
            if exchange:
                exchange.status = new_status.value
                await repo.update(exchange)
                
    async def log_audit(self, session, action: str, agent_name: str, result, entity_id: uuid.UUID, entity_type: str) -> None:
        """Record an audit log for an agent execution."""
        audit_repo = AuditLogRepository(session)
        await audit_repo.create(AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            agent_name=agent_name,
            duration_ms=result.duration_ms,
            tokens_used=result.tokens_used,
            status="success" if result.success else "error",
            error_message=result.error
        ))

    async def run_pipeline(self) -> None:
        """Execute the full 12-agent pipeline."""
        try:
            async with db_manager.get_session() as session:
                await self._execute_pipeline(session)
        except Exception as e:
            self.error = str(e)
            self.status = AnalysisStatus.FAILED
            logger.error("Pipeline failed", job_id=str(self.job_id), error=str(e), trace=traceback.format_exc())
            
            # Try to update DB status on failure
            if self.exchange_id:
                try:
                    async with db_manager.get_session() as fail_session:
                        await self.update_status(AnalysisStatus.FAILED, fail_session)
                except Exception:
                    pass

    async def _execute_pipeline(self, session) -> None:
        """Internal pipeline execution with a DB session."""
        
        ex_repo = ExchangeRepository(session)
        inst_repo = InstitutionRepository(session)
        tech_repo = TechnologyProfileRepository(session)
        exec_repo = ExecutiveRepository(session)
        opp_repo = SalesOpportunityRepository(session)
        score_repo = LeadScoreRepository(session)
        report_repo = SalesReportRepository(session)
        
        # ---------------------------------------------------------
        # 1. Exchange Discovery
        # ---------------------------------------------------------
        await self.update_status(AnalysisStatus.DISCOVERING_EXCHANGE, session)
        
        res1 = await self.agent_exchange.run(ExchangeDiscoveryInput(
            exchange_name=self.exchange_name,
            country=self.country
        ))
        
        if not res1.success:
            raise RuntimeError(f"Agent 1 Failed: {res1.error}")
            
        exchange = Exchange(
            name=self.exchange_name,
            country=self.country,
            website_url=res1.data["official_website_url"],
            status=self.status.value
        )
        exchange = await ex_repo.create(exchange)
        self.exchange_id = exchange.id
        await self.log_audit(session, "discovery", self.agent_exchange.name, res1, exchange.id, "Exchange")
        
        # ---------------------------------------------------------
        # 2. Member List Discovery
        # ---------------------------------------------------------
        await self.update_status(AnalysisStatus.FINDING_MEMBER_LIST, session)
        
        res2 = await self.agent_members.run(MemberListDiscoveryInput(
            exchange_name=exchange.name,
            exchange_url=exchange.website_url  # type: ignore
        ))
        
        if not res2.success:
            raise RuntimeError(f"Agent 2 Failed: {res2.error}")
            
        exchange.member_list_url = res2.data["member_list_url"]
        await ex_repo.update(exchange)
        await self.log_audit(session, "member_list", self.agent_members.name, res2, exchange.id, "Exchange")
        
        # ---------------------------------------------------------
        # 3. Broker Extraction
        # ---------------------------------------------------------
        await self.update_status(AnalysisStatus.EXTRACTING_BROKERS, session)
        
        res3 = await self.agent_brokers.run(BrokerExtractionInput(
            exchange_name=exchange.name,
            member_list_url=exchange.member_list_url  # type: ignore
        ))
        
        if not res3.success:
            raise RuntimeError(f"Agent 3 Failed: {res3.error}")
            
        brokers_data = res3.data.get("brokers", [])
        exchange.total_members = len(brokers_data)
        await ex_repo.update(exchange)
        await self.log_audit(session, "extraction", self.agent_brokers.name, res3, exchange.id, "Exchange")
        
        # Save institutions
        institutions = []
        for b_data in brokers_data[:20]:  # Limit to 20 for this implementation to save time/tokens
            inst = Institution(
                exchange_id=exchange.id,
                name=b_data["name"],
                institution_type=InstitutionType.BROKERAGE,
                description=b_data.get("description"),
                address=b_data.get("address"),
                phone=b_data.get("phone"),
                email=b_data.get("email"),
                website_url=b_data.get("website_url"),
                raw_data=b_data
            )
            inst = await inst_repo.create(inst)
            institutions.append(inst)
            
        # ---------------------------------------------------------
        # Institution Loop (Agents 4-12 run per institution)
        # ---------------------------------------------------------
        # For a production system, we'd use a queue (RabbitMQ/Celery) 
        # For this PoC, we process concurrently with asyncio.gather
        
        for inst in institutions:
            try:
                await self._process_institution(
                    inst, session, inst_repo, tech_repo, exec_repo, opp_repo, score_repo
                )
            except Exception as e:
                logger.error(f"Failed to process institution {inst.name}", error=str(e))
                # Continue with next institution
                
        # ---------------------------------------------------------
        # Final Report Generation
        # ---------------------------------------------------------
        await self.update_status(AnalysisStatus.COMPLETED, session)
        
        # Generate summary
        all_insts = await inst_repo.find_by_exchange_id(exchange.id)
        
        report = SalesReport(
            exchange_id=exchange.id,
            title=f"Sales Intelligence: {exchange.name}",
            total_institutions=len(all_insts)
        )
        await report_repo.create(report)

    async def _process_institution(
        self, inst: Institution, session, inst_repo, tech_repo, exec_repo, opp_repo, score_repo
    ) -> None:
        """Run agents 4-12 on a single institution."""
        
        # ---------------------------------------------------------
        # 4. Website Discovery
        # ---------------------------------------------------------
        if not inst.website_url:
            await self.update_status(AnalysisStatus.DISCOVERING_WEBSITES, session)
            res4 = await self.agent_web_discover.run(WebsiteDiscoveryInput(
                broker_name=inst.name,
                country=self.country
            ))
            if res4.success:
                inst.website_url = res4.data["official_website_url"]
                await inst_repo.update(inst)
                
        if not inst.website_url:
            return # Cannot proceed without a website
            
        # ---------------------------------------------------------
        # 5. Website Crawler
        # ---------------------------------------------------------
        await self.update_status(AnalysisStatus.CRAWLING_WEBSITES, session)
        res5 = await self.agent_crawler.run(WebsiteCrawlerInput(
            website_url=inst.website_url
        ))
        
        if not res5.success:
            return # Cannot proceed without content
            
        pages_content = res5.data.get("pages", [])
        
        # ---------------------------------------------------------
        # 6. Technology Detection
        # ---------------------------------------------------------
        await self.update_status(AnalysisStatus.DETECTING_TECHNOLOGY, session)
        res6 = await self.agent_tech.run(TechnologyDetectionInput(
            institution_name=inst.name,
            website_url=inst.website_url,
            pages_content=pages_content
        ))
        
        tech_profile_data = res6.data if res6.success else {}
        if tech_profile_data:
            tp = TechnologyProfile(
                institution_id=inst.id,
                **{k:v for k,v in tech_profile_data.items() if k in TechnologyProfile.model_fields}
            )
            await tech_repo.create(tp)
            
            inst.digital_maturity_score = tp.digital_maturity_score
            await inst_repo.update(inst)
            
        # ---------------------------------------------------------
        # 7. Executive Discovery
        # ---------------------------------------------------------
        await self.update_status(AnalysisStatus.DISCOVERING_EXECUTIVES, session)
        res7 = await self.agent_execs.run(ExecutiveDiscoveryInput(
            institution_name=inst.name,
            website_url=inst.website_url,
            pages_content=pages_content
        ))
        
        executives = []
        if res7.success:
            for ex_data in res7.data.get("executives", []):
                exec = Executive(
                    institution_id=inst.id,
                    name=ex_data["name"],
                    title=ex_data["title"],
                    source=ex_data["source"],
                    confidence=ex_data.get("confidence", 1.0)
                )
                exec = await exec_repo.create(exec)
                executives.append(exec)
                
        # ---------------------------------------------------------
        # 8. Profile Resolver
        # ---------------------------------------------------------
        if executives:
            await self.update_status(AnalysisStatus.RESOLVING_PROFILES, session)
            exec_queries = [ExecutiveQuery(name=e.name, title=e.title or "") for e in executives]
            
            res8 = await self.agent_profiles.run(ProfileResolverInput(
                institution_name=inst.name,
                executives=exec_queries
            ))
            
            if res8.success:
                # Update executives with resolved URLs
                resolved_map = {r["name"]: r for r in res8.data.get("resolved_profiles", [])}
                for exec in executives:
                    if exec.name in resolved_map:
                        resolved = resolved_map[exec.name]
                        exec.linkedin_url = resolved.get("linkedin_url")
                        exec.facebook_url = resolved.get("facebook_url")
                        await exec_repo.update(exec)
                        
        # ---------------------------------------------------------
        # 9. Opportunity Analysis
        # ---------------------------------------------------------
        await self.update_status(AnalysisStatus.ANALYZING_OPPORTUNITIES, session)
        
        tp_data = TechProfileData(
            frontend=tech_profile_data.get("frontend_technologies", []),
            backend=tech_profile_data.get("backend_technologies", []),
            has_mobile_app=tech_profile_data.get("has_mobile_app", False),
            has_api=tech_profile_data.get("has_api", False),
            score=tech_profile_data.get("digital_maturity_score", 0.0)
        )
        
        res9 = await self.agent_opportunities.run(OpportunityAnalysisInput(
            institution_name=inst.name,
            description=inst.description,
            tech_profile=tp_data
        ))
        
        opps = []
        if res9.success:
            for opp_data in res9.data.get("opportunities", []):
                opp = SalesOpportunity(
                    institution_id=inst.id,
                    opportunity_type=opp_data["opportunity_type"],
                    title=opp_data["title"],
                    description=opp_data["description"],
                    priority=opp_data["priority"],
                    confidence_score=opp_data["confidence_score"],
                    reasoning=opp_data["reasoning"],
                    recommended_approach=opp_data["recommended_approach"]
                )
                opp = await opp_repo.create(opp)
                opps.append(opp)
                
        # ---------------------------------------------------------
        # 10. Lead Scoring
        # ---------------------------------------------------------
        await self.update_status(AnalysisStatus.SCORING_LEADS, session)
        
        res10 = await self.agent_scoring.run(LeadScoringInput(
            has_website=bool(inst.website_url),
            executives_found=len(executives),
            tech_score=tech_profile_data.get("digital_maturity_score", 0.0),
            opportunities=res9.data.get("opportunities", []) if res9.success else []
        ))
        
        score = None
        if res10.success:
            score = LeadScore(
                institution_id=inst.id,
                **{k:v for k,v in res10.data.items() if k in LeadScore.model_fields}
            )
            await score_repo.create(score)
            
        # ---------------------------------------------------------
        # 11 & 12. Sales Insight & Email Generation
        # ---------------------------------------------------------
        if score and score.tier in ["hot", "warm"]:
            await self.update_status(AnalysisStatus.GENERATING_INSIGHTS, session)
            
            res11 = await self.agent_insights.run(SalesInsightInput(
                institution_name=inst.name,
                opportunities=res9.data.get("opportunities", []) if res9.success else [],
                lead_tier=score.tier,
                overall_score=score.overall_score
            ))
            
            if res11.success and executives:
                await self.update_status(AnalysisStatus.GENERATING_EMAILS, session)
                
                exec_infos = []
                for e in executives:
                    from app.application.agents.executive_discovery_agent import ExecutiveInfo
                    exec_infos.append(ExecutiveInfo(
                        name=e.name,
                        title=e.title or "",
                        source=e.source or "",
                        confidence=e.confidence
                    ))
                    
                from app.application.agents.sales_insight_agent import SalesInsightOutput
                insight_out = SalesInsightOutput(**res11.data)
                
                # Run Email Gen
                await self.agent_email.run(EmailGenerationInput(
                    institution_name=inst.name,
                    executives=exec_infos,
                    sales_insight=insight_out
                ))
                # Emails would be saved or sent here
