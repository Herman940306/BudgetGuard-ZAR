"""
BudgetGuard ZAR - Audit Logger Tests.

Property-based and unit tests for AuditLogger class.
Tests ensure correct JSON serialisation, Decimal precision
preservation, and round-trip consistency.

**Feature: budgetguard-zar, Property 7: Serialisation Round-Trip**
"""

import json
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given, settings, assume
from hypothesis.strategies import (
    decimals, integers, lists, composite, sampled_from, datetimes
)

from src.audit import AuditLogger, DecimalEncoder
from src.schema import (
    AnalysisSnapshot,
    Campaign,
    CampaignAnalysis,
    RiskLevel,
)


# Custom strategies for generating test data
@composite
def valid_campaigns(draw):
    """Generate valid Campaign objects."""
    names = ["Brand_Awareness", "Lead_Gen", "Retargeting", "Holiday_Sale"]
    name = f"{draw(sampled_from(names))}_{draw(integers(1, 9999))}"
    
    budget = draw(decimals(
        min_value=Decimal("100"),
        max_value=Decimal("1000000"),
        places=2,
        allow_nan=False,
        allow_infinity=False
    ))
    
    spend = draw(decimals(
        min_value=Decimal("0"),
        max_value=budget,
        places=2,
        allow_nan=False,
        allow_infinity=False
    ))
    
    return Campaign(
        name=name,
        monthly_budget=budget,
        current_spend=spend,
        gross_budget=None
    )


@composite
def valid_campaign_analyses(draw):
    """Generate valid CampaignAnalysis objects."""
    campaign = draw(valid_campaigns())
    
    rds = draw(decimals(
        min_value=Decimal("0"),
        max_value=Decimal("50000"),
        places=2,
        allow_nan=False,
        allow_infinity=False
    ))
    
    spend_pct = draw(decimals(
        min_value=Decimal("0"),
        max_value=Decimal("150"),
        places=2,
        allow_nan=False,
        allow_infinity=False
    ))
    
    time_pct = draw(decimals(
        min_value=Decimal("1"),
        max_value=Decimal("100"),
        places=2,
        allow_nan=False,
        allow_infinity=False
    ))
    
    risk_level = draw(sampled_from(list(RiskLevel)))
    days_remaining = draw(integers(min_value=1, max_value=31))
    
    return CampaignAnalysis(
        campaign=campaign,
        rds=rds,
        spend_percentage=spend_pct,
        time_percentage=time_pct,
        risk_level=risk_level,
        days_remaining=days_remaining
    )


@composite
def valid_snapshots(draw):
    """Generate valid AnalysisSnapshot objects."""
    campaigns = draw(lists(valid_campaign_analyses(), min_size=1, max_size=10))
    
    total_budget = sum(ca.campaign.monthly_budget for ca in campaigns)
    total_spend = sum(ca.campaign.current_spend for ca in campaigns)
    critical_count = sum(1 for ca in campaigns if ca.risk_level == RiskLevel.CRITICAL)
    warning_count = sum(1 for ca in campaigns if ca.risk_level == RiskLevel.WARNING)
    
    timestamp = draw(datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    
    return AnalysisSnapshot(
        timestamp=timestamp,
        version="0.1.0",
        campaigns=campaigns,
        total_budget=total_budget,
        total_spend=total_spend,
        critical_count=critical_count,
        warning_count=warning_count
    )


class TestAuditLoggerUnit:
    """Unit tests for AuditLogger edge cases."""

    def setup_method(self) -> None:
        """Initialise AuditLogger for each test."""
        self.logger = AuditLogger()

    def test_decimal_encoder_preserves_precision(self) -> None:
        """Verify DecimalEncoder converts Decimal to string."""
        value = Decimal("12345.67")
        encoded = json.dumps({"amount": value}, cls=DecimalEncoder)
        
        assert '"12345.67"' in encoded
        assert "12345.67" in encoded

    def test_decimal_encoder_handles_datetime(self) -> None:
        """Verify DecimalEncoder handles datetime."""
        dt = datetime(2024, 12, 18, 14, 30, 0)
        encoded = json.dumps({"timestamp": dt}, cls=DecimalEncoder)
        
        assert "2024-12-18T14:30:00" in encoded

    def test_decimal_encoder_handles_risk_level(self) -> None:
        """Verify DecimalEncoder handles RiskLevel enum."""
        encoded = json.dumps({"risk": RiskLevel.CRITICAL}, cls=DecimalEncoder)
        
        assert '"CRITICAL"' in encoded

    def test_serialise_simple_snapshot(self) -> None:
        """Verify basic snapshot serialisation."""
        campaign = Campaign("Test", Decimal("10000.00"), Decimal("3000.00"))
        analysis = CampaignAnalysis(
            campaign=campaign,
            rds=Decimal("500.00"),
            spend_percentage=Decimal("30.00"),
            time_percentage=Decimal("50.00"),
            risk_level=RiskLevel.HEALTHY,
            days_remaining=14
        )
        snapshot = AnalysisSnapshot(
            timestamp=datetime(2024, 12, 18, 14, 30, 0),
            version="0.1.0",
            campaigns=[analysis],
            total_budget=Decimal("10000.00"),
            total_spend=Decimal("3000.00"),
            critical_count=0,
            warning_count=0
        )
        
        json_str = self.logger.serialise_snapshot(snapshot)
        data = json.loads(json_str)
        
        # Verify structure
        assert "metadata" in data
        assert "summary" in data
        assert "campaigns" in data
        
        # Verify metadata
        assert data["metadata"]["version"] == "0.1.0"
        assert data["metadata"]["generated_by"] == "BudgetGuard ZAR"
        
        # Verify Decimal values are strings
        assert data["summary"]["total_budget"] == "10000.00"
        assert data["summary"]["total_spend"] == "3000.00"

    def test_deserialise_restores_decimal_types(self) -> None:
        """Verify deserialisation restores Decimal types."""
        campaign = Campaign("Test", Decimal("10000.00"), Decimal("3000.00"))
        analysis = CampaignAnalysis(
            campaign=campaign,
            rds=Decimal("500.00"),
            spend_percentage=Decimal("30.00"),
            time_percentage=Decimal("50.00"),
            risk_level=RiskLevel.HEALTHY,
            days_remaining=14
        )
        snapshot = AnalysisSnapshot(
            timestamp=datetime(2024, 12, 18, 14, 30, 0),
            version="0.1.0",
            campaigns=[analysis],
            total_budget=Decimal("10000.00"),
            total_spend=Decimal("3000.00"),
            critical_count=0,
            warning_count=0
        )
        
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        # Verify Decimal types
        assert isinstance(restored.total_budget, Decimal)
        assert isinstance(restored.total_spend, Decimal)
        assert isinstance(restored.campaigns[0].rds, Decimal)
        assert isinstance(restored.campaigns[0].campaign.monthly_budget, Decimal)

    def test_round_trip_preserves_values(self) -> None:
        """Verify round-trip preserves exact Decimal values."""
        # Use values that would lose precision with float
        campaign = Campaign("Precision", Decimal("10000.01"), Decimal("3333.33"))
        analysis = CampaignAnalysis(
            campaign=campaign,
            rds=Decimal("476.19"),
            spend_percentage=Decimal("33.33"),
            time_percentage=Decimal("58.06"),
            risk_level=RiskLevel.HEALTHY,
            days_remaining=14
        )
        snapshot = AnalysisSnapshot(
            timestamp=datetime(2024, 12, 18, 14, 30, 0),
            version="0.1.0",
            campaigns=[analysis],
            total_budget=Decimal("10000.01"),
            total_spend=Decimal("3333.33"),
            critical_count=0,
            warning_count=0
        )
        
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        # Verify exact equality
        assert restored.total_budget == snapshot.total_budget
        assert restored.total_spend == snapshot.total_spend
        assert restored.campaigns[0].rds == analysis.rds
        assert restored.campaigns[0].spend_percentage == analysis.spend_percentage

    def test_save_and_load_file(self) -> None:
        """Verify file save and load operations."""
        campaign = Campaign("FileTest", Decimal("10000.00"), Decimal("5000.00"))
        analysis = CampaignAnalysis(
            campaign=campaign,
            rds=Decimal("357.14"),
            spend_percentage=Decimal("50.00"),
            time_percentage=Decimal("50.00"),
            risk_level=RiskLevel.HEALTHY,
            days_remaining=14
        )
        snapshot = AnalysisSnapshot(
            timestamp=datetime(2024, 12, 18, 14, 30, 0),
            version="0.1.0",
            campaigns=[analysis],
            total_budget=Decimal("10000.00"),
            total_spend=Decimal("5000.00"),
            critical_count=0,
            warning_count=0
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_audit.json"
            
            self.logger.save_to_file(snapshot, file_path)
            assert file_path.exists()
            
            loaded = self.logger.load_from_file(file_path)
            assert loaded.total_budget == snapshot.total_budget

    def test_load_nonexistent_file_raises(self) -> None:
        """Verify FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            self.logger.load_from_file("nonexistent.json")

    def test_generate_filename(self) -> None:
        """Verify filename generation format."""
        filename = self.logger.generate_filename("budget_audit")
        
        assert filename.startswith("budget_audit_")
        assert filename.endswith(".json")
        assert len(filename) > 20  # Has timestamp

    def test_gross_budget_preserved(self) -> None:
        """Verify gross_budget is preserved in round-trip."""
        campaign = Campaign(
            "VAT_Test",
            Decimal("10000.00"),
            Decimal("3000.00"),
            gross_budget=Decimal("11500.00")
        )
        analysis = CampaignAnalysis(
            campaign=campaign,
            rds=Decimal("500.00"),
            spend_percentage=Decimal("30.00"),
            time_percentage=Decimal("50.00"),
            risk_level=RiskLevel.HEALTHY,
            days_remaining=14
        )
        snapshot = AnalysisSnapshot(
            timestamp=datetime(2024, 12, 18, 14, 30, 0),
            version="0.1.0",
            campaigns=[analysis],
            total_budget=Decimal("10000.00"),
            total_spend=Decimal("3000.00"),
            critical_count=0,
            warning_count=0
        )
        
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        assert restored.campaigns[0].campaign.gross_budget == Decimal("11500.00")

    def test_json_structure_sample(self) -> None:
        """Generate sample JSON structure for documentation."""
        campaign = Campaign("Holiday_Campaign_2024", Decimal("50000.00"), Decimal("15000.00"))
        analysis = CampaignAnalysis(
            campaign=campaign,
            rds=Decimal("2500.00"),
            spend_percentage=Decimal("30.00"),
            time_percentage=Decimal("58.06"),
            risk_level=RiskLevel.HEALTHY,
            days_remaining=14
        )
        snapshot = AnalysisSnapshot(
            timestamp=datetime(2024, 12, 18, 14, 30, 0),
            version="0.1.0",
            campaigns=[analysis],
            total_budget=Decimal("50000.00"),
            total_spend=Decimal("15000.00"),
            critical_count=0,
            warning_count=0
        )
        
        json_str = self.logger.serialise_snapshot(snapshot)
        
        print("\n>>> SAMPLE JSON OUTPUT STRUCTURE:")
        print(json_str)
        print(">>> END SAMPLE\n")
        
        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data is not None


class TestAuditLoggerPropertyRoundTrip:
    """
    Property-based tests for serialisation round-trip.
    
    **Feature: budgetguard-zar, Property 7: Serialisation Round-Trip**
    **Validates: Requirements 6.1, 6.2, 6.3**
    """

    def setup_method(self) -> None:
        """Initialise AuditLogger for each test."""
        self.logger = AuditLogger()

    @given(valid_snapshots())
    @settings(max_examples=100)
    def test_round_trip_preserves_total_budget(
        self, snapshot: AnalysisSnapshot
    ) -> None:
        """
        Property: Round-trip preserves total_budget exactly.
        
        **Feature: budgetguard-zar, Property 7: Serialisation Round-Trip**
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        assert restored.total_budget == snapshot.total_budget, (
            f"total_budget mismatch: {restored.total_budget} != {snapshot.total_budget}"
        )

    @given(valid_snapshots())
    @settings(max_examples=100)
    def test_round_trip_preserves_total_spend(
        self, snapshot: AnalysisSnapshot
    ) -> None:
        """
        Property: Round-trip preserves total_spend exactly.
        
        **Feature: budgetguard-zar, Property 7: Serialisation Round-Trip**
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        assert restored.total_spend == snapshot.total_spend, (
            f"total_spend mismatch: {restored.total_spend} != {snapshot.total_spend}"
        )

    @given(valid_snapshots())
    @settings(max_examples=100)
    def test_round_trip_preserves_campaign_count(
        self, snapshot: AnalysisSnapshot
    ) -> None:
        """
        Property: Round-trip preserves number of campaigns.
        
        **Feature: budgetguard-zar, Property 7: Serialisation Round-Trip**
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        assert len(restored.campaigns) == len(snapshot.campaigns)

    @given(valid_snapshots())
    @settings(max_examples=100)
    def test_round_trip_preserves_rds_values(
        self, snapshot: AnalysisSnapshot
    ) -> None:
        """
        Property: Round-trip preserves all RDS values exactly.
        
        **Feature: budgetguard-zar, Property 7: Serialisation Round-Trip**
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        for orig, rest in zip(snapshot.campaigns, restored.campaigns):
            assert rest.rds == orig.rds, (
                f"RDS mismatch: {rest.rds} != {orig.rds}"
            )

    @given(valid_snapshots())
    @settings(max_examples=100)
    def test_round_trip_preserves_risk_levels(
        self, snapshot: AnalysisSnapshot
    ) -> None:
        """
        Property: Round-trip preserves all risk levels.
        
        **Feature: budgetguard-zar, Property 7: Serialisation Round-Trip**
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        for orig, rest in zip(snapshot.campaigns, restored.campaigns):
            assert rest.risk_level == orig.risk_level

    @given(valid_snapshots())
    @settings(max_examples=100)
    def test_round_trip_preserves_decimal_types(
        self, snapshot: AnalysisSnapshot
    ) -> None:
        """
        Property: Round-trip restores Decimal types (not float).
        
        **Feature: budgetguard-zar, Property 7: Serialisation Round-Trip**
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        assert isinstance(restored.total_budget, Decimal)
        assert isinstance(restored.total_spend, Decimal)
        
        for ca in restored.campaigns:
            assert isinstance(ca.rds, Decimal)
            assert isinstance(ca.spend_percentage, Decimal)
            assert isinstance(ca.campaign.monthly_budget, Decimal)

    @given(valid_snapshots())
    @settings(max_examples=100)
    def test_round_trip_preserves_timestamp(
        self, snapshot: AnalysisSnapshot
    ) -> None:
        """
        Property: Round-trip preserves timestamp.
        
        **Feature: budgetguard-zar, Property 7: Serialisation Round-Trip**
        **Validates: Requirements 6.4**
        """
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        assert restored.timestamp == snapshot.timestamp

    @given(valid_snapshots())
    @settings(max_examples=100)
    def test_round_trip_preserves_version(
        self, snapshot: AnalysisSnapshot
    ) -> None:
        """
        Property: Round-trip preserves version identifier.
        
        **Feature: budgetguard-zar, Property 7: Serialisation Round-Trip**
        **Validates: Requirements 6.4**
        """
        json_str = self.logger.serialise_snapshot(snapshot)
        restored = self.logger.deserialise_snapshot(json_str)
        
        assert restored.version == snapshot.version
