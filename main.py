"""
BudgetGuard ZAR - Main Entry Point.

Financial safety tool for South African advertising agencies.
Processes campaign budget data and generates risk analysis reports.

Usage:
    python main.py <input_csv> [--output-dir <dir>]

Example:
    python main.py campaigns.csv --output-dir reports/
"""

import argparse
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List

from src import __version__
from src.audit import AuditLogger
from src.calculator import PacingEngine
from src.date_logic import DateManager
from src.excel_generator import ExcelReporter
from src.schema import AnalysisSnapshot, CampaignAnalysis, RiskLevel
from src.validator import DataValidator


def print_header() -> None:
    """Prints the application header."""
    print("=" * 60)
    print("  BudgetGuard ZAR - Financial Safety Tool")
    print(f"  Version: {__version__}")
    print("  Zero-Overspend Guarantee for SA Advertising Agencies")
    print("=" * 60)
    print()


def print_summary(snapshot: AnalysisSnapshot) -> None:
    """
    Prints a professional summary to the console.

    Args:
        snapshot: Analysis snapshot with results.
    """
    print("\n" + "=" * 60)
    print("  ANALYSIS COMPLETE")
    print("=" * 60)
    print()
    
    # Portfolio Overview
    print("  PORTFOLIO OVERVIEW")
    print("  " + "-" * 40)
    print(f"  Total Budget:      R {snapshot.total_budget:,.2f}")
    print(f"  Total Spend:       R {snapshot.total_spend:,.2f}")
    remaining = snapshot.total_budget - snapshot.total_spend
    print(f"  Remaining:         R {remaining:,.2f}")
    
    overall_rds = sum(ca.rds for ca in snapshot.campaigns)
    print(f"  Overall RDS:       R {overall_rds:,.2f}")
    print()
    
    # Risk Summary
    print("  RISK SUMMARY")
    print("  " + "-" * 40)
    
    healthy_count = sum(
        1 for ca in snapshot.campaigns
        if ca.risk_level == RiskLevel.HEALTHY
    )
    over_budget_count = sum(
        1 for ca in snapshot.campaigns
        if ca.risk_level == RiskLevel.OVER_BUDGET
    )
    
    if snapshot.critical_count > 0:
        print(f"  ⚠️  CRITICAL:       {snapshot.critical_count} campaigns")
    if snapshot.warning_count > 0:
        print(f"  ⚡ WARNING:        {snapshot.warning_count} campaigns")
    if healthy_count > 0:
        print(f"  ✓  HEALTHY:        {healthy_count} campaigns")
    if over_budget_count > 0:
        print(f"  ❌ OVER BUDGET:    {over_budget_count} campaigns")
    
    print(f"\n  Total Campaigns:   {len(snapshot.campaigns)}")
    print()


def print_critical_alerts(campaigns: List[CampaignAnalysis]) -> None:
    """
    Prints alerts for critical campaigns.

    Args:
        campaigns: List of campaign analyses.
    """
    critical = [ca for ca in campaigns if ca.risk_level == RiskLevel.CRITICAL]
    
    if critical:
        print("  ⚠️  CRITICAL ALERTS - IMMEDIATE ACTION REQUIRED")
        print("  " + "-" * 40)
        for ca in critical:
            variance = ca.spend_percentage - ca.time_percentage
            print(f"  • {ca.campaign.name}")
            print(f"    Spend: {ca.spend_percentage:.1f}% | Time: {ca.time_percentage:.1f}%")
            print(f"    Variance: +{variance:.1f}% over pace")
            print(f"    RDS: R {ca.rds:,.2f}")
            print()


def run_analysis(
    csv_path: Path,
    output_dir: Path
) -> int:
    """
    Runs the complete analysis pipeline.

    Args:
        csv_path: Path to input CSV file.
        output_dir: Directory for output files.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    print_header()
    
    # Step 1: Validate CSV
    print(f"  Loading: {csv_path}")
    validator = DataValidator()
    
    try:
        result = validator.validate_csv(csv_path)
    except FileNotFoundError:
        print(f"\n  ❌ ERROR: File not found: {csv_path}")
        return 1
    except ValueError as e:
        print(f"\n  ❌ ERROR: {e}")
        return 1
    
    if not result.is_valid:
        print(f"\n  ❌ VALIDATION ERRORS ({result.error_count} errors):")
        for error in result.errors[:10]:  # Show first 10 errors
            print(f"     {error}")
        if result.error_count > 10:
            print(f"     ... and {result.error_count - 10} more errors")
        return 1
    
    print(f"  ✓ Validated {result.valid_count} campaigns")
    
    # Step 2: Calculate pacing
    print("  Calculating pacing metrics...")
    date_manager = DateManager()
    engine = PacingEngine(date_manager)
    
    analyses: List[CampaignAnalysis] = []
    for campaign in result.campaigns:
        analysis = engine.analyse_campaign(campaign)
        analyses.append(analysis)
    
    # Step 3: Create snapshot
    total_budget = sum(ca.campaign.monthly_budget for ca in analyses)
    total_spend = sum(ca.campaign.current_spend for ca in analyses)
    critical_count = sum(1 for ca in analyses if ca.risk_level == RiskLevel.CRITICAL)
    warning_count = sum(1 for ca in analyses if ca.risk_level == RiskLevel.WARNING)
    
    snapshot = AnalysisSnapshot(
        timestamp=datetime.now(),
        version=__version__,
        campaigns=analyses,
        total_budget=total_budget,
        total_spend=total_spend,
        critical_count=critical_count,
        warning_count=warning_count
    )
    
    # Step 4: Save audit log
    output_dir.mkdir(parents=True, exist_ok=True)
    
    audit_logger = AuditLogger()
    audit_filename = audit_logger.generate_filename("budget_audit")
    audit_path = output_dir / audit_filename
    audit_logger.save_to_file(snapshot, audit_path)
    print(f"  ✓ Audit log saved: {audit_path}")
    
    # Step 5: Generate Excel report
    excel_reporter = ExcelReporter()
    excel_filename = excel_reporter.generate_filename("budget_report")
    excel_path = output_dir / excel_filename
    excel_reporter.generate_report(snapshot, excel_path)
    print(f"  ✓ Excel report saved: {excel_path}")
    
    # Print summary
    print_summary(snapshot)
    print_critical_alerts(analyses)
    
    print("=" * 60)
    print("  BudgetGuard ZAR - Analysis Complete")
    print("=" * 60)
    
    return 0


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="BudgetGuard ZAR - Financial Safety Tool for SA Agencies"
    )
    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to campaign CSV file"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory for reports (default: output/)"
    )
    
    args = parser.parse_args()
    
    return run_analysis(args.csv_file, args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
