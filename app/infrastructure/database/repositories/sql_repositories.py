"""
Concrete repository implementations using SQLAlchemy.

These implement the abstract interfaces defined in the domain layer.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.audit_log import AuditLog
from app.domain.entities.exchange import Exchange
from app.domain.entities.executive import Executive
from app.domain.entities.institution import Institution
from app.domain.entities.lead_score import LeadScore
from app.domain.entities.sales_opportunity import SalesOpportunity
from app.domain.entities.sales_report import SalesReport
from app.domain.entities.technology_profile import TechnologyProfile
from app.domain.repositories.interfaces import (
    IAuditLogRepository,
    IExchangeRepository,
    IExecutiveRepository,
    IInstitutionRepository,
    ILeadScoreRepository,
    ISalesOpportunityRepository,
    ISalesReportRepository,
    ITechnologyProfileRepository,
)
from app.infrastructure.database.models import (
    AuditLogModel,
    ExchangeModel,
    ExecutiveModel,
    InstitutionModel,
    LeadScoreModel,
    SalesOpportunityModel,
    SalesReportModel,
    TechnologyProfileModel,
)


def _model_to_entity(model: ExchangeModel) -> Exchange:
    return Exchange.model_validate(model, from_attributes=True)


class ExchangeRepository(IExchangeRepository):
    """SQLAlchemy implementation of IExchangeRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Exchange]:
        result = await self._session.get(ExchangeModel, entity_id)
        return Exchange.model_validate(result, from_attributes=True) if result else None

    async def create(self, entity: Exchange) -> Exchange:
        model = ExchangeModel(**entity.model_dump())
        self._session.add(model)
        await self._session.flush()
        return Exchange.model_validate(model, from_attributes=True)

    async def update(self, entity: Exchange) -> Exchange:
        model = await self._session.get(ExchangeModel, entity.id)
        if model:
            for key, value in entity.model_dump(exclude={"id", "created_at"}).items():
                setattr(model, key, value)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        model = await self._session.get(ExchangeModel, entity_id)
        if model:
            await self._session.delete(model)
            return True
        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Exchange]:
        stmt = select(ExchangeModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [Exchange.model_validate(m, from_attributes=True) for m in result.scalars().all()]

    async def find_by_name(self, name: str) -> Optional[Exchange]:
        stmt = select(ExchangeModel).where(ExchangeModel.name.ilike(f"%{name}%"))
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return Exchange.model_validate(model, from_attributes=True) if model else None


class InstitutionRepository(IInstitutionRepository):
    """SQLAlchemy implementation of IInstitutionRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Institution]:
        result = await self._session.get(InstitutionModel, entity_id)
        return Institution.model_validate(result, from_attributes=True) if result else None

    async def create(self, entity: Institution) -> Institution:
        model = InstitutionModel(**entity.model_dump())
        self._session.add(model)
        await self._session.flush()
        return Institution.model_validate(model, from_attributes=True)

    async def update(self, entity: Institution) -> Institution:
        model = await self._session.get(InstitutionModel, entity.id)
        if model:
            for key, value in entity.model_dump(exclude={"id", "created_at"}).items():
                setattr(model, key, value)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        model = await self._session.get(InstitutionModel, entity_id)
        if model:
            await self._session.delete(model)
            return True
        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Institution]:
        stmt = select(InstitutionModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [Institution.model_validate(m, from_attributes=True) for m in result.scalars().all()]

    async def find_by_exchange_id(self, exchange_id: uuid.UUID) -> list[Institution]:
        stmt = select(InstitutionModel).where(InstitutionModel.exchange_id == exchange_id)
        result = await self._session.execute(stmt)
        return [Institution.model_validate(m, from_attributes=True) for m in result.scalars().all()]

    async def find_by_name_and_exchange(
        self, name: str, exchange_id: uuid.UUID
    ) -> Optional[Institution]:
        stmt = select(InstitutionModel).where(
            InstitutionModel.name.ilike(f"%{name}%"),
            InstitutionModel.exchange_id == exchange_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return Institution.model_validate(model, from_attributes=True) if model else None


class ExecutiveRepository(IExecutiveRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Executive]:
        result = await self._session.get(ExecutiveModel, entity_id)
        return Executive.model_validate(result, from_attributes=True) if result else None

    async def create(self, entity: Executive) -> Executive:
        model = ExecutiveModel(**entity.model_dump())
        self._session.add(model)
        await self._session.flush()
        return Executive.model_validate(model, from_attributes=True)

    async def update(self, entity: Executive) -> Executive:
        model = await self._session.get(ExecutiveModel, entity.id)
        if model:
            for key, value in entity.model_dump(exclude={"id", "created_at"}).items():
                setattr(model, key, value)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        model = await self._session.get(ExecutiveModel, entity_id)
        if model:
            await self._session.delete(model)
            return True
        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Executive]:
        stmt = select(ExecutiveModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [Executive.model_validate(m, from_attributes=True) for m in result.scalars().all()]

    async def find_by_institution_id(self, institution_id: uuid.UUID) -> list[Executive]:
        stmt = select(ExecutiveModel).where(ExecutiveModel.institution_id == institution_id)
        result = await self._session.execute(stmt)
        return [Executive.model_validate(m, from_attributes=True) for m in result.scalars().all()]


class TechnologyProfileRepository(ITechnologyProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[TechnologyProfile]:
        result = await self._session.get(TechnologyProfileModel, entity_id)
        return TechnologyProfile.model_validate(result, from_attributes=True) if result else None

    async def create(self, entity: TechnologyProfile) -> TechnologyProfile:
        model = TechnologyProfileModel(**entity.model_dump())
        self._session.add(model)
        await self._session.flush()
        return TechnologyProfile.model_validate(model, from_attributes=True)

    async def update(self, entity: TechnologyProfile) -> TechnologyProfile:
        model = await self._session.get(TechnologyProfileModel, entity.id)
        if model:
            for key, value in entity.model_dump(exclude={"id", "created_at"}).items():
                setattr(model, key, value)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        model = await self._session.get(TechnologyProfileModel, entity_id)
        if model:
            await self._session.delete(model)
            return True
        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[TechnologyProfile]:
        stmt = select(TechnologyProfileModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [TechnologyProfile.model_validate(m, from_attributes=True) for m in result.scalars().all()]

    async def find_by_institution_id(self, institution_id: uuid.UUID) -> Optional[TechnologyProfile]:
        stmt = select(TechnologyProfileModel).where(TechnologyProfileModel.institution_id == institution_id)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return TechnologyProfile.model_validate(model, from_attributes=True) if model else None


class SalesOpportunityRepository(ISalesOpportunityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[SalesOpportunity]:
        result = await self._session.get(SalesOpportunityModel, entity_id)
        return SalesOpportunity.model_validate(result, from_attributes=True) if result else None

    async def create(self, entity: SalesOpportunity) -> SalesOpportunity:
        model = SalesOpportunityModel(**entity.model_dump())
        self._session.add(model)
        await self._session.flush()
        return SalesOpportunity.model_validate(model, from_attributes=True)

    async def update(self, entity: SalesOpportunity) -> SalesOpportunity:
        model = await self._session.get(SalesOpportunityModel, entity.id)
        if model:
            for key, value in entity.model_dump(exclude={"id", "created_at"}).items():
                setattr(model, key, value)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        model = await self._session.get(SalesOpportunityModel, entity_id)
        if model:
            await self._session.delete(model)
            return True
        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[SalesOpportunity]:
        stmt = select(SalesOpportunityModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [SalesOpportunity.model_validate(m, from_attributes=True) for m in result.scalars().all()]

    async def find_by_institution_id(self, institution_id: uuid.UUID) -> list[SalesOpportunity]:
        stmt = select(SalesOpportunityModel).where(SalesOpportunityModel.institution_id == institution_id)
        result = await self._session.execute(stmt)
        return [SalesOpportunity.model_validate(m, from_attributes=True) for m in result.scalars().all()]


class LeadScoreRepository(ILeadScoreRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[LeadScore]:
        result = await self._session.get(LeadScoreModel, entity_id)
        return LeadScore.model_validate(result, from_attributes=True) if result else None

    async def create(self, entity: LeadScore) -> LeadScore:
        model = LeadScoreModel(**entity.model_dump())
        self._session.add(model)
        await self._session.flush()
        return LeadScore.model_validate(model, from_attributes=True)

    async def update(self, entity: LeadScore) -> LeadScore:
        model = await self._session.get(LeadScoreModel, entity.id)
        if model:
            for key, value in entity.model_dump(exclude={"id", "created_at"}).items():
                setattr(model, key, value)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        model = await self._session.get(LeadScoreModel, entity_id)
        if model:
            await self._session.delete(model)
            return True
        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[LeadScore]:
        stmt = select(LeadScoreModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [LeadScore.model_validate(m, from_attributes=True) for m in result.scalars().all()]

    async def find_by_institution_id(self, institution_id: uuid.UUID) -> Optional[LeadScore]:
        stmt = select(LeadScoreModel).where(LeadScoreModel.institution_id == institution_id)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return LeadScore.model_validate(model, from_attributes=True) if model else None

    async def get_top_leads(self, limit: int = 20) -> list[LeadScore]:
        stmt = select(LeadScoreModel).order_by(LeadScoreModel.overall_score.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [LeadScore.model_validate(m, from_attributes=True) for m in result.scalars().all()]


class SalesReportRepository(ISalesReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[SalesReport]:
        result = await self._session.get(SalesReportModel, entity_id)
        return SalesReport.model_validate(result, from_attributes=True) if result else None

    async def create(self, entity: SalesReport) -> SalesReport:
        model = SalesReportModel(**entity.model_dump())
        self._session.add(model)
        await self._session.flush()
        return SalesReport.model_validate(model, from_attributes=True)

    async def update(self, entity: SalesReport) -> SalesReport:
        model = await self._session.get(SalesReportModel, entity.id)
        if model:
            for key, value in entity.model_dump(exclude={"id"}).items():
                setattr(model, key, value)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        model = await self._session.get(SalesReportModel, entity_id)
        if model:
            await self._session.delete(model)
            return True
        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[SalesReport]:
        stmt = select(SalesReportModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [SalesReport.model_validate(m, from_attributes=True) for m in result.scalars().all()]

    async def find_by_exchange_id(self, exchange_id: uuid.UUID) -> Optional[SalesReport]:
        stmt = select(SalesReportModel).where(SalesReportModel.exchange_id == exchange_id)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return SalesReport.model_validate(model, from_attributes=True) if model else None


class AuditLogRepository(IAuditLogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, log: AuditLog) -> AuditLog:
        model = AuditLogModel(**log.model_dump())
        self._session.add(model)
        await self._session.flush()
        return AuditLog.model_validate(model, from_attributes=True)

    async def find_by_entity(self, entity_type: str, entity_id: uuid.UUID) -> list[AuditLog]:
        stmt = select(AuditLogModel).where(
            AuditLogModel.entity_type == entity_type,
            AuditLogModel.entity_id == entity_id,
        ).order_by(AuditLogModel.timestamp.desc())
        result = await self._session.execute(stmt)
        return [AuditLog.model_validate(m, from_attributes=True) for m in result.scalars().all()]

    async def list_recent(self, limit: int = 50) -> list[AuditLog]:
        stmt = select(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [AuditLog.model_validate(m, from_attributes=True) for m in result.scalars().all()]
