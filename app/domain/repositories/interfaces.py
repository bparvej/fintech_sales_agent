"""
Abstract repository interfaces for the domain layer.

These define the contracts that infrastructure implementations must fulfill.
Domain layer never imports infrastructure — only these interfaces.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from app.domain.entities.audit_log import AuditLog
from app.domain.entities.exchange import Exchange
from app.domain.entities.executive import Executive
from app.domain.entities.institution import Institution
from app.domain.entities.lead_score import LeadScore
from app.domain.entities.sales_opportunity import SalesOpportunity
from app.domain.entities.sales_report import SalesReport
from app.domain.entities.technology_profile import TechnologyProfile

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Base repository interface with common CRUD operations."""

    @abstractmethod
    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[T]:
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        ...

    @abstractmethod
    async def delete(self, entity_id: uuid.UUID) -> bool:
        ...

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        ...


class IExchangeRepository(IRepository[Exchange]):
    """Repository interface for Exchange entities."""

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Exchange]:
        ...


class IInstitutionRepository(IRepository[Institution]):
    """Repository interface for Institution entities."""

    @abstractmethod
    async def find_by_exchange_id(self, exchange_id: uuid.UUID) -> list[Institution]:
        ...

    @abstractmethod
    async def find_by_name_and_exchange(
        self, name: str, exchange_id: uuid.UUID
    ) -> Optional[Institution]:
        ...


class IExecutiveRepository(IRepository[Executive]):
    """Repository interface for Executive entities."""

    @abstractmethod
    async def find_by_institution_id(self, institution_id: uuid.UUID) -> list[Executive]:
        ...


class ITechnologyProfileRepository(IRepository[TechnologyProfile]):
    """Repository interface for TechnologyProfile entities."""

    @abstractmethod
    async def find_by_institution_id(
        self, institution_id: uuid.UUID
    ) -> Optional[TechnologyProfile]:
        ...


class ISalesOpportunityRepository(IRepository[SalesOpportunity]):
    """Repository interface for SalesOpportunity entities."""

    @abstractmethod
    async def find_by_institution_id(
        self, institution_id: uuid.UUID
    ) -> list[SalesOpportunity]:
        ...


class ILeadScoreRepository(IRepository[LeadScore]):
    """Repository interface for LeadScore entities."""

    @abstractmethod
    async def find_by_institution_id(
        self, institution_id: uuid.UUID
    ) -> Optional[LeadScore]:
        ...

    @abstractmethod
    async def get_top_leads(self, limit: int = 20) -> list[LeadScore]:
        ...


class ISalesReportRepository(IRepository[SalesReport]):
    """Repository interface for SalesReport entities."""

    @abstractmethod
    async def find_by_exchange_id(self, exchange_id: uuid.UUID) -> Optional[SalesReport]:
        ...


class IAuditLogRepository(ABC):
    """Repository interface for AuditLog entries (append-only)."""

    @abstractmethod
    async def create(self, log: AuditLog) -> AuditLog:
        ...

    @abstractmethod
    async def find_by_entity(
        self, entity_type: str, entity_id: uuid.UUID
    ) -> list[AuditLog]:
        ...

    @abstractmethod
    async def list_recent(self, limit: int = 50) -> list[AuditLog]:
        ...
