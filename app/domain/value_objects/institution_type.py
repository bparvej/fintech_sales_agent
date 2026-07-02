"""
Value object enums for institution types, opportunity types, and analysis status.
"""

from __future__ import annotations

from enum import Enum


class InstitutionType(str, Enum):
    """Types of financial institutions the system can analyze."""

    BROKERAGE = "brokerage"
    COMMERCIAL_BANK = "commercial_bank"
    MERCHANT_BANK = "merchant_bank"
    INVESTMENT_BANK = "investment_bank"
    ASSET_MANAGEMENT = "asset_management"
    INSURANCE = "insurance"
    FINTECH = "fintech"
    CRYPTO_EXCHANGE = "crypto_exchange"
    DIGITAL_BANK = "digital_bank"
    PAYMENT_PROVIDER = "payment_provider"
    STOCK_EXCHANGE = "stock_exchange"
    OTHER = "other"
