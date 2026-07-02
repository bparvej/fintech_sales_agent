"""Opportunity type value object."""

from __future__ import annotations

from enum import Enum


class OpportunityType(str, Enum):
    """Types of sales opportunities identified by the analysis."""

    PLATFORM_MODERNIZATION = "platform_modernization"
    MOBILE_APP_DEVELOPMENT = "mobile_app_development"
    CLOUD_MIGRATION = "cloud_migration"
    CYBERSECURITY_UPGRADE = "cybersecurity_upgrade"
    API_INTEGRATION = "api_integration"
    DATA_ANALYTICS = "data_analytics"
    COMPLIANCE_AUTOMATION = "compliance_automation"
    DIGITAL_ONBOARDING = "digital_onboarding"
    TRADING_SYSTEM_UPGRADE = "trading_system_upgrade"
    CRM_IMPLEMENTATION = "crm_implementation"
    WEBSITE_REDESIGN = "website_redesign"
    OTHER = "other"
