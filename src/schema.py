"""
BudgetGuard ZAR - Data Schema Module.

This module defines the core data models for the BudgetGuard system.
All monetary fields use Decimal type to ensure financial precision.

South African Market Context:
    - Default VAT rate: 15%
    - Monthly_Budget represents Net Platform Spend (VAT exclusive)
    - Calculations exclude agency management fees
    - RDS values match what media buyers enter in Meta/Google Ads

Classes:
    RiskLevel: Enumeration of campaign risk classifications.
    Campaign: Represents a single advertising campaign with budget data.
    CampaignAnalysis: Complete analysis result for a campaign.
    AnalysisSnapshot: Complete analysis run with metadata for audit purposes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional


# South African VAT rate (15%)
ZAR_VAT_RATE = Decimal("0.15")


class RiskLevel(Enum):
    """
    Risk classification for campaign pacing.

    Attributes:
        HEALTHY: Spend pace is within acceptable range of time pace.
        WARNING: Spend pace exceeds time pace by 5-15 percentage points.
        CRITICAL: Spend pace exceeds time pace by more than 15 percentage points.
        OVER_BUDGET: Current spend has exceeded the monthly budget.
    """

    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    OVER_BUDGET = "OVER_BUDGET"


@dataclass
class Campaign:
    """
    Represents a single advertising campaign with budget data.

    All monetary values are stored as Decimal to ensure precision
    in financial calculations.

    Important Definitions:
        monthly_budget: Net Platform Spend in ZAR (VAT exclusive).
            This is the actual amount available for ad platform spend,
            excluding VAT and agency management fees.
        current_spend: ZAR amount spent to date on ad platforms.
        gross_budget: Optional VAT-inclusive budget for reference.
            If provided, monthly_budget should equal gross_budget / 1.15.

    Attributes:
        name: Campaign identifier or name.
        monthly_budget: Net Platform Spend in ZAR (VAT exclusive).
        current_spend: ZAR amount spent to date.
        gross_budget: Optional gross budget (VAT inclusive) for audit trail.
    """

    name: str
    monthly_budget: Decimal
    current_spend: Decimal
    gross_budget: Optional[Decimal] = None


@dataclass
class CampaignAnalysis:
    """
    Complete analysis result for a campaign.

    Contains all calculated metrics including Recommended Daily Spend,
    pacing percentages, and risk classification.

    Attributes:
        campaign: Source campaign data.
        rds: Recommended Daily Spend in ZAR.
        spend_percentage: Current spend as percentage of budget (0-100+).
        time_percentage: Days elapsed as percentage of month (0-100).
        risk_level: Calculated risk classification.
        days_remaining: Days left in current month (inclusive of today).
    """

    campaign: Campaign
    rds: Decimal
    spend_percentage: Decimal
    time_percentage: Decimal
    risk_level: RiskLevel
    days_remaining: int


@dataclass
class AnalysisSnapshot:
    """
    Complete analysis run with metadata for audit purposes.

    Captures the full state of an analysis run including all campaign
    results and aggregate metrics. Used for persistence and audit trails.

    Attributes:
        timestamp: When the analysis was performed (UTC).
        version: BudgetGuard version identifier.
        campaigns: List of analysed campaigns with results.
        total_budget: Sum of all campaign budgets in ZAR.
        total_spend: Sum of all campaign spend in ZAR.
        critical_count: Number of campaigns flagged as CRITICAL.
        warning_count: Number of campaigns flagged as WARNING.
    """

    timestamp: datetime
    version: str
    campaigns: List[CampaignAnalysis]
    total_budget: Decimal
    total_spend: Decimal
    critical_count: int
    warning_count: int


def calculate_net_from_gross(gross_amount: Decimal) -> Decimal:
    """
    Calculates Net Platform Spend from a VAT-inclusive gross amount.

    Uses the South African VAT rate of 15% to extract the net amount
    that can be spent on advertising platforms.

    Args:
        gross_amount: VAT-inclusive budget amount in ZAR.

    Returns:
        Net amount (VAT exclusive) in ZAR.

    Example:
        >>> calculate_net_from_gross(Decimal("11500"))
        Decimal('10000.00')
    """
    from decimal import ROUND_HALF_EVEN
    net = gross_amount / (Decimal("1") + ZAR_VAT_RATE)
    return net.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def calculate_gross_from_net(net_amount: Decimal) -> Decimal:
    """
    Calculates VAT-inclusive gross amount from Net Platform Spend.

    Uses the South African VAT rate of 15% to calculate the gross amount.

    Args:
        net_amount: Net Platform Spend in ZAR (VAT exclusive).

    Returns:
        Gross amount (VAT inclusive) in ZAR.

    Example:
        >>> calculate_gross_from_net(Decimal("10000"))
        Decimal('11500.00')
    """
    from decimal import ROUND_HALF_EVEN
    gross = net_amount * (Decimal("1") + ZAR_VAT_RATE)
    return gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
