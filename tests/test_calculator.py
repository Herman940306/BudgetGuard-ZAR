"""
BudgetGuard ZAR - Pacing Engine Tests.

Property-based and unit tests for PacingEngine class.
Tests ensure correct RDS calculation, risk classification,
and Decimal arithmetic precision.

**Feature: budgetguard-zar, Property 4: RDS Formula Correctness**
**Feature: budgetguard-zar, Property 5: Risk Classification Correctness**
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN

import pytest
from hypothesis import given, settings, assume
from hypothesis.strategies import decimals, integers, dates, composite

from src.calculator import PacingEngine
from src.date_logic import DateManager
from src.schema import Campaign, RiskLevel


# Custom strategies for generating valid financial data
@composite
def valid_budgets(draw):
    """Generate valid positive budget amounts (R100 to R10,000,000)."""
    return draw(decimals(
        min_value=Decimal("100"),
        max_value=Decimal("10000000"),
        places=2,
        allow_nan=False,
        allow_infinity=False
    ))


@composite
def valid_campaigns(draw):
    """Generate valid Campaign objects where spend <= budget."""
    budget = draw(valid_budgets())
    # Spend between 0 and budget
    max_spend = budget
    spend = draw(decimals(
        min_value=Decimal("0"),
        max_value=max_spend,
        places=2,
        allow_nan=False,
        allow_infinity=False
    ))
    return Campaign(
        name=f"Campaign_{draw(integers(min_value=1, max_value=9999))}",
        monthly_budget=budget,
        current_spend=spend
    )


@composite
def over_budget_campaigns(draw):
    """Generate Campaign objects where spend > budget."""
    budget = draw(valid_budgets())
    # Spend exceeds budget by 1% to 50%
    overspend_factor = draw(decimals(
        min_value=Decimal("1.01"),
        max_value=Decimal("1.50"),
        places=2,
        allow_nan=False,
        allow_infinity=False
    ))
    spend = (budget * overspend_factor).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_EVEN
    )
    return Campaign(
        name=f"OverBudget_{draw(integers(min_value=1, max_value=9999))}",
        monthly_budget=budget,
        current_spend=spend
    )


class TestPacingEngineUnit:
    """Unit tests for PacingEngine edge cases."""

    def setup_method(self) -> None:
        """Initialise PacingEngine for each test."""
        self.dm = DateManager()
        self.engine = PacingEngine(self.dm)

    def test_rds_basic_calculation(self) -> None:
        """Verify basic RDS calculation."""
        campaign = Campaign("Test", Decimal("10000"), Decimal("3000"))
        ref_date = date(2024, 12, 18)  # 14 days remaining
        
        rds = self.engine.calculate_rds(campaign, ref_date)
        
        # (10000 - 3000) / 14 = 500.00
        expected = Decimal("500.00")
        assert rds == expected

    def test_rds_over_budget_returns_zero(self) -> None:
        """Verify RDS returns 0 when over budget."""
        campaign = Campaign("OverBudget", Decimal("10000"), Decimal("12000"))
        
        rds = self.engine.calculate_rds(campaign)
        
        assert rds == Decimal("0.00")

    def test_rds_exactly_at_budget_returns_zero(self) -> None:
        """Verify RDS returns 0 when exactly at budget."""
        campaign = Campaign("AtBudget", Decimal("10000"), Decimal("10000"))
        
        rds = self.engine.calculate_rds(campaign)
        
        assert rds == Decimal("0.00")

    def test_rds_last_day_of_month(self) -> None:
        """Verify RDS on last day equals remaining budget."""
        campaign = Campaign("LastDay", Decimal("10000"), Decimal("9000"))
        last_day = date(2024, 12, 31)  # 1 day remaining
        
        rds = self.engine.calculate_rds(campaign, last_day)
        
        # (10000 - 9000) / 1 = 1000.00
        assert rds == Decimal("1000.00")

    def test_rds_uses_bankers_rounding(self) -> None:
        """Verify Banker's Rounding is applied to RDS."""
        # Create scenario where rounding matters
        # 7000 / 14 = 500.00 (no rounding needed)
        # 7001 / 14 = 500.0714... -> 500.07
        campaign = Campaign("Rounding", Decimal("10001"), Decimal("3000"))
        ref_date = date(2024, 12, 18)  # 14 days remaining
        
        rds = self.engine.calculate_rds(campaign, ref_date)
        
        # (10001 - 3000) / 14 = 500.0714...
        # Banker's rounding: 500.07
        expected = (Decimal("7001") / Decimal("14")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        assert rds == expected

    def test_rds_returns_decimal_type(self) -> None:
        """Verify RDS returns Decimal type."""
        campaign = Campaign("TypeCheck", Decimal("10000"), Decimal("5000"))
        
        rds = self.engine.calculate_rds(campaign)
        
        assert isinstance(rds, Decimal)

    def test_spend_percentage_calculation(self) -> None:
        """Verify spend percentage calculation."""
        campaign = Campaign("SpendPct", Decimal("10000"), Decimal("3000"))
        
        pct = self.engine.calculate_spend_percentage(campaign)
        
        assert pct == Decimal("30")

    def test_spend_percentage_over_100(self) -> None:
        """Verify spend percentage can exceed 100%."""
        campaign = Campaign("Over100", Decimal("10000"), Decimal("15000"))
        
        pct = self.engine.calculate_spend_percentage(campaign)
        
        assert pct == Decimal("150")

    def test_spend_percentage_zero_budget_raises(self) -> None:
        """Verify zero budget raises ValueError."""
        campaign = Campaign("ZeroBudget", Decimal("0"), Decimal("1000"))
        
        with pytest.raises(ValueError, match="Monthly budget must be positive"):
            self.engine.calculate_spend_percentage(campaign)

    def test_risk_level_critical(self) -> None:
        """Verify CRITICAL risk when variance > 15%."""
        risk = self.engine.determine_risk_level(
            spend_percentage=Decimal("66"),
            time_percentage=Decimal("50")
        )
        assert risk == RiskLevel.CRITICAL

    def test_risk_level_warning(self) -> None:
        """Verify WARNING risk when variance 5-15%."""
        risk = self.engine.determine_risk_level(
            spend_percentage=Decimal("60"),
            time_percentage=Decimal("50")
        )
        assert risk == RiskLevel.WARNING

    def test_risk_level_healthy(self) -> None:
        """Verify HEALTHY risk when variance <= 5%."""
        risk = self.engine.determine_risk_level(
            spend_percentage=Decimal("52"),
            time_percentage=Decimal("50")
        )
        assert risk == RiskLevel.HEALTHY

    def test_risk_level_over_budget(self) -> None:
        """Verify OVER_BUDGET when spend > 100%."""
        risk = self.engine.determine_risk_level(
            spend_percentage=Decimal("105"),
            time_percentage=Decimal("50")
        )
        assert risk == RiskLevel.OVER_BUDGET

    def test_risk_level_boundary_exactly_15(self) -> None:
        """Verify exactly 15% variance is WARNING, not CRITICAL."""
        risk = self.engine.determine_risk_level(
            spend_percentage=Decimal("65"),
            time_percentage=Decimal("50")
        )
        assert risk == RiskLevel.WARNING

    def test_risk_level_boundary_exactly_5(self) -> None:
        """Verify exactly 5% variance is HEALTHY, not WARNING."""
        risk = self.engine.determine_risk_level(
            spend_percentage=Decimal("55"),
            time_percentage=Decimal("50")
        )
        assert risk == RiskLevel.HEALTHY

    def test_analyse_campaign_returns_complete_analysis(self) -> None:
        """Verify analyse_campaign returns all fields."""
        campaign = Campaign("Complete", Decimal("10000"), Decimal("3000"))
        ref_date = date(2024, 12, 18)
        
        analysis = self.engine.analyse_campaign(campaign, ref_date)
        
        assert analysis.campaign == campaign
        assert analysis.rds == Decimal("500.00")
        assert analysis.days_remaining == 14
        assert isinstance(analysis.spend_percentage, Decimal)
        assert isinstance(analysis.time_percentage, Decimal)
        assert isinstance(analysis.risk_level, RiskLevel)


class TestPacingEnginePropertyRDS:
    """
    Property-based tests for RDS calculation.
    
    **Feature: budgetguard-zar, Property 4: RDS Formula Correctness**
    **Validates: Requirements 3.1, 3.4**
    """

    def setup_method(self) -> None:
        """Initialise PacingEngine for each test."""
        self.dm = DateManager()
        self.engine = PacingEngine(self.dm)

    @given(valid_campaigns(), dates(
        min_value=date(2020, 1, 1),
        max_value=date(2030, 12, 31)
    ))
    @settings(max_examples=200)
    def test_rds_never_negative(self, campaign: Campaign, ref_date: date) -> None:
        """
        Property: RDS is never negative.
        
        **Feature: budgetguard-zar, Property 4: RDS Formula Correctness**
        **Validates: Requirements 3.1, 3.4**
        
        For any campaign where spend <= budget, RDS must be >= 0.
        """
        rds = self.engine.calculate_rds(campaign, ref_date)
        
        assert rds >= Decimal("0"), (
            f"RDS={rds} is negative for campaign {campaign.name}"
        )

    @given(valid_campaigns(), dates(
        min_value=date(2020, 1, 1),
        max_value=date(2030, 12, 31)
    ))
    @settings(max_examples=200)
    def test_rds_formula_correctness(self, campaign: Campaign, ref_date: date) -> None:
        """
        Property: RDS equals (budget - spend) / days_remaining.
        
        **Feature: budgetguard-zar, Property 4: RDS Formula Correctness**
        **Validates: Requirements 3.1, 3.4**
        """
        assume(campaign.current_spend < campaign.monthly_budget)
        
        rds = self.engine.calculate_rds(campaign, ref_date)
        days_remaining = self.dm.get_days_remaining(ref_date)
        
        remaining = campaign.monthly_budget - campaign.current_spend
        expected = (remaining / Decimal(str(days_remaining))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        
        assert rds == expected, (
            f"RDS mismatch: got {rds}, expected {expected}"
        )

    @given(valid_campaigns(), dates(
        min_value=date(2020, 1, 1),
        max_value=date(2030, 12, 31)
    ))
    @settings(max_examples=200)
    def test_rds_has_two_decimal_places(self, campaign: Campaign, ref_date: date) -> None:
        """
        Property: RDS always has exactly 2 decimal places.
        
        **Feature: budgetguard-zar, Property 4: RDS Formula Correctness**
        **Validates: Requirements 3.4**
        """
        rds = self.engine.calculate_rds(campaign, ref_date)
        
        # Check that quantizing to 2 places doesn't change the value
        quantized = rds.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        assert rds == quantized, (
            f"RDS {rds} does not have exactly 2 decimal places"
        )

    @given(over_budget_campaigns())
    @settings(max_examples=100)
    def test_rds_zero_when_over_budget(self, campaign: Campaign) -> None:
        """
        Property: RDS is zero when spend exceeds budget.
        
        **Feature: budgetguard-zar, Property 4: RDS Formula Correctness**
        **Validates: Requirements 3.2**
        """
        rds = self.engine.calculate_rds(campaign)
        
        assert rds == Decimal("0.00"), (
            f"RDS should be 0.00 for over-budget campaign, got {rds}"
        )

    @given(valid_campaigns(), dates(
        min_value=date(2020, 1, 1),
        max_value=date(2030, 12, 31)
    ))
    @settings(max_examples=200)
    def test_rds_returns_decimal_type(self, campaign: Campaign, ref_date: date) -> None:
        """
        Property: RDS always returns Decimal type.
        
        Ensures no floating-point arithmetic is used.
        """
        rds = self.engine.calculate_rds(campaign, ref_date)
        
        assert isinstance(rds, Decimal), (
            f"Expected Decimal, got {type(rds)}"
        )


class TestPacingEnginePropertyRisk:
    """
    Property-based tests for risk classification.
    
    **Feature: budgetguard-zar, Property 5: Risk Classification Correctness**
    **Validates: Requirements 4.1, 4.2, 4.3**
    """

    def setup_method(self) -> None:
        """Initialise PacingEngine for each test."""
        self.dm = DateManager()
        self.engine = PacingEngine(self.dm)

    @given(
        decimals(min_value=Decimal("101"), max_value=Decimal("500"),
                 places=2, allow_nan=False, allow_infinity=False),
        decimals(min_value=Decimal("0"), max_value=Decimal("100"),
                 places=2, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_over_budget_classification(
        self, spend_pct: Decimal, time_pct: Decimal
    ) -> None:
        """
        Property: Spend > 100% always returns OVER_BUDGET.
        
        **Feature: budgetguard-zar, Property 5: Risk Classification Correctness**
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        risk = self.engine.determine_risk_level(spend_pct, time_pct)
        
        assert risk == RiskLevel.OVER_BUDGET, (
            f"Expected OVER_BUDGET for spend={spend_pct}%, got {risk}"
        )

    @given(
        decimals(min_value=Decimal("0"), max_value=Decimal("100"),
                 places=2, allow_nan=False, allow_infinity=False),
        decimals(min_value=Decimal("0"), max_value=Decimal("100"),
                 places=2, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=200)
    def test_risk_classification_correctness(
        self, spend_pct: Decimal, time_pct: Decimal
    ) -> None:
        """
        Property: Risk classification follows threshold rules.
        
        **Feature: budgetguard-zar, Property 5: Risk Classification Correctness**
        **Validates: Requirements 4.1, 4.2, 4.3**
        
        - CRITICAL: variance > 15
        - WARNING: 5 < variance <= 15
        - HEALTHY: variance <= 5
        """
        risk = self.engine.determine_risk_level(spend_pct, time_pct)
        variance = spend_pct - time_pct
        
        if variance > Decimal("15"):
            expected = RiskLevel.CRITICAL
        elif variance > Decimal("5"):
            expected = RiskLevel.WARNING
        else:
            expected = RiskLevel.HEALTHY
        
        assert risk == expected, (
            f"Variance={variance}: expected {expected}, got {risk}"
        )

    @given(valid_campaigns(), dates(
        min_value=date(2020, 1, 1),
        max_value=date(2030, 12, 31)
    ))
    @settings(max_examples=200)
    def test_analyse_campaign_risk_consistency(
        self, campaign: Campaign, ref_date: date
    ) -> None:
        """
        Property: analyse_campaign risk matches determine_risk_level.
        
        The risk level in CampaignAnalysis must be consistent with
        the direct calculation from percentages.
        """
        analysis = self.engine.analyse_campaign(campaign, ref_date)
        
        expected_risk = self.engine.determine_risk_level(
            analysis.spend_percentage,
            analysis.time_percentage
        )
        
        assert analysis.risk_level == expected_risk, (
            f"Risk mismatch: analysis={analysis.risk_level}, "
            f"expected={expected_risk}"
        )
