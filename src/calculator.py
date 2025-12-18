"""
BudgetGuard ZAR - Pacing Engine Module.

This module provides the core financial calculation engine for budget pacing.
All calculations use Decimal arithmetic with Banker's Rounding to ensure
financial precision.

Classes:
    PacingEngine: Core calculation engine for RDS and risk assessment.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Optional

from src.date_logic import DateManager
from src.schema import Campaign, CampaignAnalysis, RiskLevel


class PacingEngine:
    """
    Core financial calculation engine for budget pacing.

    All calculations use Decimal arithmetic with Banker's Rounding
    (ROUND_HALF_EVEN) to ensure financial precision and eliminate
    floating-point errors.

    Attributes:
        date_manager: DateManager instance for time calculations.

    Example:
        >>> from decimal import Decimal
        >>> dm = DateManager()
        >>> engine = PacingEngine(dm)
        >>> campaign = Campaign("Test", Decimal("10000"), Decimal("3000"))
        >>> analysis = engine.analyse_campaign(campaign)
    """

    # Risk threshold constants (percentage points)
    CRITICAL_THRESHOLD = Decimal("15")
    WARNING_THRESHOLD = Decimal("5")

    def __init__(self, date_manager: DateManager):
        """
        Initialises the PacingEngine with a DateManager.

        Args:
            date_manager: DateManager instance for date calculations.
        """
        self._date_manager = date_manager

    def calculate_rds(
        self,
        campaign: Campaign,
        reference_date: Optional[date] = None
    ) -> Decimal:
        """
        Calculates the Recommended Daily Spend for a campaign.

        Formula: (Monthly_Budget - Current_Spend) / Days_Remaining

        If the campaign is over budget, returns Decimal('0.00').

        Args:
            campaign: Campaign with budget and spend data.
            reference_date: Date for calculation. Defaults to today.

        Returns:
            RDS value in ZAR, rounded to 2 decimal places using
            Banker's Rounding. Returns Decimal('0.00') if over budget.
        """
        remaining_budget = campaign.monthly_budget - campaign.current_spend

        if remaining_budget <= Decimal("0"):
            return Decimal("0.00")

        days_remaining = Decimal(str(
            self._date_manager.get_days_remaining(reference_date)
        ))

        rds = remaining_budget / days_remaining
        return rds.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

    def calculate_spend_percentage(self, campaign: Campaign) -> Decimal:
        """
        Calculates current spend as a percentage of monthly budget.

        Args:
            campaign: Campaign with budget and spend data.

        Returns:
            Spend percentage as Decimal (0-100+). Can exceed 100 if
            over budget.

        Raises:
            ValueError: If monthly_budget is zero or negative.
        """
        if campaign.monthly_budget <= Decimal("0"):
            raise ValueError("Monthly budget must be positive")

        percentage = (campaign.current_spend / campaign.monthly_budget) * Decimal("100")
        return percentage

    def determine_risk_level(
        self,
        spend_percentage: Decimal,
        time_percentage: Decimal
    ) -> RiskLevel:
        """
        Determines risk classification based on pacing variance.

        Risk Thresholds:
        - OVER_BUDGET: Spend % exceeds 100%
        - CRITICAL: Spend % exceeds Time % by >15 points
        - WARNING: Spend % exceeds Time % by 5-15 points
        - HEALTHY: Spend % within 5 points of Time %

        Args:
            spend_percentage: Current spend percentage (0-100+).
            time_percentage: Current time percentage (0-100).

        Returns:
            RiskLevel enum value based on pacing variance.
        """
        if spend_percentage > Decimal("100"):
            return RiskLevel.OVER_BUDGET

        variance = spend_percentage - time_percentage

        if variance > self.CRITICAL_THRESHOLD:
            return RiskLevel.CRITICAL
        elif variance > self.WARNING_THRESHOLD:
            return RiskLevel.WARNING
        else:
            return RiskLevel.HEALTHY

    def analyse_campaign(
        self,
        campaign: Campaign,
        reference_date: Optional[date] = None
    ) -> CampaignAnalysis:
        """
        Performs complete analysis on a single campaign.

        Calculates RDS, spend percentage, time percentage, and
        determines risk level based on pacing variance.

        Args:
            campaign: Campaign to analyse.
            reference_date: Date for calculation. Defaults to today.

        Returns:
            CampaignAnalysis with all calculated metrics.
        """
        rds = self.calculate_rds(campaign, reference_date)
        spend_percentage = self.calculate_spend_percentage(campaign)
        time_percentage = self._date_manager.get_time_percentage(reference_date)
        risk_level = self.determine_risk_level(spend_percentage, time_percentage)
        days_remaining = self._date_manager.get_days_remaining(reference_date)

        return CampaignAnalysis(
            campaign=campaign,
            rds=rds,
            spend_percentage=spend_percentage,
            time_percentage=time_percentage,
            risk_level=risk_level,
            days_remaining=days_remaining
        )
