"""
BudgetGuard ZAR - Audit and Serialisation Module.

This module provides JSON serialisation for financial audit trails.
All Decimal values are converted to string representation to preserve
precision during serialisation and deserialisation.

South African Market Context:
    - Every snapshot includes timestamp and version for compliance
    - Decimal precision is preserved for financial auditing
    - JSON format enables integration with external audit systems

Classes:
    AuditLogger: Manages JSON serialisation for audit and persistence.
"""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Union

from src import __version__
from src.schema import (
    AnalysisSnapshot,
    Campaign,
    CampaignAnalysis,
    RiskLevel,
)


class DecimalEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that converts Decimal to string.

    Preserves full precision of Decimal values by encoding them
    as strings rather than floats.
    """

    def default(self, obj: Any) -> Any:
        """
        Encode Decimal and datetime objects.

        Args:
            obj: Object to encode.

        Returns:
            JSON-serialisable representation.
        """
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, RiskLevel):
            return obj.value
        return super().default(obj)


class AuditLogger:
    """
    Manages JSON serialisation for audit and persistence.

    Converts Decimal values to string representation to preserve
    precision during serialisation and deserialisation. Every
    snapshot includes timestamp and version identifier.

    Example:
        >>> logger = AuditLogger()
        >>> json_str = logger.serialise_snapshot(snapshot)
        >>> restored = logger.deserialise_snapshot(json_str)
        >>> assert snapshot.total_budget == restored.total_budget
    """

    def __init__(self, version: str = None):
        """
        Initialises the AuditLogger.

        Args:
            version: Version identifier for snapshots.
                     Defaults to package version.
        """
        self._version = version or __version__

    def serialise_snapshot(self, snapshot: AnalysisSnapshot) -> str:
        """
        Serialises an AnalysisSnapshot to JSON string.

        Decimal values are converted to strings to preserve precision.
        Includes timestamp and version identifier.

        Args:
            snapshot: Analysis snapshot to serialise.

        Returns:
            JSON string representation.
        """
        data = self._snapshot_to_dict(snapshot)
        return json.dumps(data, cls=DecimalEncoder, indent=2)

    def deserialise_snapshot(self, json_str: str) -> AnalysisSnapshot:
        """
        Deserialises a JSON string to AnalysisSnapshot.

        String values are converted back to Decimal types.

        Args:
            json_str: JSON string to deserialise.

        Returns:
            Reconstructed AnalysisSnapshot.

        Raises:
            json.JSONDecodeError: If JSON is malformed.
            KeyError: If required fields are missing.
            ValueError: If data types are invalid.
        """
        data = json.loads(json_str)
        return self._dict_to_snapshot(data)

    def save_to_file(
        self,
        snapshot: AnalysisSnapshot,
        file_path: Union[str, Path]
    ) -> None:
        """
        Saves an AnalysisSnapshot to a JSON file.

        Args:
            snapshot: Analysis snapshot to save.
            file_path: Output file path.

        Raises:
            PermissionError: If file cannot be written.
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        json_str = self.serialise_snapshot(snapshot)
        file_path.write_text(json_str, encoding="utf-8")

    def load_from_file(self, file_path: Union[str, Path]) -> AnalysisSnapshot:
        """
        Loads an AnalysisSnapshot from a JSON file.

        Args:
            file_path: Path to JSON file.

        Returns:
            Loaded AnalysisSnapshot.

        Raises:
            FileNotFoundError: If file does not exist.
            json.JSONDecodeError: If JSON is malformed.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Audit file not found: {file_path}")

        json_str = file_path.read_text(encoding="utf-8")
        return self.deserialise_snapshot(json_str)

    def _snapshot_to_dict(self, snapshot: AnalysisSnapshot) -> Dict[str, Any]:
        """
        Converts AnalysisSnapshot to dictionary for JSON serialisation.

        Args:
            snapshot: Snapshot to convert.

        Returns:
            Dictionary representation.
        """
        return {
            "metadata": {
                "timestamp": snapshot.timestamp.isoformat(),
                "version": snapshot.version,
                "generated_by": "BudgetGuard ZAR",
            },
            "summary": {
                "total_budget": str(snapshot.total_budget),
                "total_spend": str(snapshot.total_spend),
                "critical_count": snapshot.critical_count,
                "warning_count": snapshot.warning_count,
                "campaign_count": len(snapshot.campaigns),
            },
            "campaigns": [
                self._campaign_analysis_to_dict(ca)
                for ca in snapshot.campaigns
            ],
        }

    def _campaign_analysis_to_dict(
        self,
        analysis: CampaignAnalysis
    ) -> Dict[str, Any]:
        """
        Converts CampaignAnalysis to dictionary.

        Args:
            analysis: Campaign analysis to convert.

        Returns:
            Dictionary representation.
        """
        campaign_dict = {
            "name": analysis.campaign.name,
            "monthly_budget": str(analysis.campaign.monthly_budget),
            "current_spend": str(analysis.campaign.current_spend),
        }

        if analysis.campaign.gross_budget is not None:
            campaign_dict["gross_budget"] = str(analysis.campaign.gross_budget)

        return {
            "campaign": campaign_dict,
            "analysis": {
                "rds": str(analysis.rds),
                "spend_percentage": str(analysis.spend_percentage),
                "time_percentage": str(analysis.time_percentage),
                "risk_level": analysis.risk_level.value,
                "days_remaining": analysis.days_remaining,
            },
        }

    def _dict_to_snapshot(self, data: Dict[str, Any]) -> AnalysisSnapshot:
        """
        Converts dictionary to AnalysisSnapshot.

        Args:
            data: Dictionary from JSON.

        Returns:
            Reconstructed AnalysisSnapshot.
        """
        metadata = data["metadata"]
        summary = data["summary"]

        campaigns = [
            self._dict_to_campaign_analysis(ca_data)
            for ca_data in data["campaigns"]
        ]

        return AnalysisSnapshot(
            timestamp=datetime.fromisoformat(metadata["timestamp"]),
            version=metadata["version"],
            campaigns=campaigns,
            total_budget=Decimal(summary["total_budget"]),
            total_spend=Decimal(summary["total_spend"]),
            critical_count=summary["critical_count"],
            warning_count=summary["warning_count"],
        )

    def _dict_to_campaign_analysis(
        self,
        data: Dict[str, Any]
    ) -> CampaignAnalysis:
        """
        Converts dictionary to CampaignAnalysis.

        Args:
            data: Dictionary from JSON.

        Returns:
            Reconstructed CampaignAnalysis.
        """
        campaign_data = data["campaign"]
        analysis_data = data["analysis"]

        gross_budget = None
        if "gross_budget" in campaign_data:
            gross_budget = Decimal(campaign_data["gross_budget"])

        campaign = Campaign(
            name=campaign_data["name"],
            monthly_budget=Decimal(campaign_data["monthly_budget"]),
            current_spend=Decimal(campaign_data["current_spend"]),
            gross_budget=gross_budget,
        )

        return CampaignAnalysis(
            campaign=campaign,
            rds=Decimal(analysis_data["rds"]),
            spend_percentage=Decimal(analysis_data["spend_percentage"]),
            time_percentage=Decimal(analysis_data["time_percentage"]),
            risk_level=RiskLevel(analysis_data["risk_level"]),
            days_remaining=analysis_data["days_remaining"],
        )

    def generate_filename(self, prefix: str = "audit") -> str:
        """
        Generates a timestamped filename for audit files.

        Args:
            prefix: Filename prefix. Defaults to "audit".

        Returns:
            Filename like "audit_2024-12-18_143052.json".
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        return f"{prefix}_{timestamp}.json"
