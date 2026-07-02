"""Analysis status value object for pipeline tracking."""

from __future__ import annotations

from enum import Enum


class AnalysisStatus(str, Enum):
    """Status of an analysis pipeline run."""

    PENDING = "pending"
    DISCOVERING_EXCHANGE = "discovering_exchange"
    FINDING_MEMBER_LIST = "finding_member_list"
    EXTRACTING_BROKERS = "extracting_brokers"
    DISCOVERING_WEBSITES = "discovering_websites"
    CRAWLING_WEBSITES = "crawling_websites"
    DETECTING_TECHNOLOGY = "detecting_technology"
    DISCOVERING_EXECUTIVES = "discovering_executives"
    RESOLVING_PROFILES = "resolving_profiles"
    ANALYZING_OPPORTUNITIES = "analyzing_opportunities"
    SCORING_LEADS = "scoring_leads"
    GENERATING_INSIGHTS = "generating_insights"
    GENERATING_EMAILS = "generating_emails"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in (self.COMPLETED, self.FAILED, self.CANCELLED)

    @property
    def step_number(self) -> int:
        """Return the pipeline step number (1-based) for progress tracking."""
        ordered = [
            self.PENDING,
            self.DISCOVERING_EXCHANGE,
            self.FINDING_MEMBER_LIST,
            self.EXTRACTING_BROKERS,
            self.DISCOVERING_WEBSITES,
            self.CRAWLING_WEBSITES,
            self.DETECTING_TECHNOLOGY,
            self.DISCOVERING_EXECUTIVES,
            self.RESOLVING_PROFILES,
            self.ANALYZING_OPPORTUNITIES,
            self.SCORING_LEADS,
            self.GENERATING_INSIGHTS,
            self.GENERATING_EMAILS,
            self.COMPLETED,
        ]
        try:
            return ordered.index(self)
        except ValueError:
            return -1

    @classmethod
    def total_steps(cls) -> int:
        return 13  # PENDING through COMPLETED
