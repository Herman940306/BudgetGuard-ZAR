🔹 BudgetGuard ZAR
Deterministic Backend & Automation Engine for Financial‑Grade Budget Control

A production‑ready Python system demonstrating precision arithmetic, defensive data engineering, and audit‑safe automation under real‑world financial constraints.

```

Executive Summary
BudgetGuard ZAR is a deterministic backend and automation tool designed to prevent budget overspend through mathematically precise pacing logic, rigorous validation, and audit‑ready outputs.

While originally built for South African digital advertising agencies, the system is intentionally engineered around transferable backend reliability patterns applicable to any domain involving money, quotas, or time‑based allocation.

```

Why This Matters to Engineering Teams
This project demonstrates how to:

  * Prevent silent financial errors caused by floating‑point arithmetic

  * Enforce correctness through deterministic logic and property‑based testing

  * Design CLI‑driven automation suitable for scheduled pipelines

  * Produce audit‑ready artifacts for regulated or high‑risk environments

What This Project Demonstrates

  * Backend Engineering: Deterministic business logic, strict data validation, explicit error handling

  * Automation Engineering: CLI tooling, batch processing, reproducible outputs

  * Data Engineering: CSV ingestion, schema enforcement, transformation pipelines

  * Reliability Engineering: Property‑based testing, edge‑case hardening, audit trails

  * Financial Correctness: Decimal arithmetic, banker’s rounding, VAT‑aware accounting

Core Capabilities

  * Real‑time budget pacing analysis with Recommended Daily Spend (RDS)

  * Proactive risk classification before overspend occurs

  * Professional Excel reporting for stakeholders

  * JSON audit snapshots for compliance and traceability

Precision Financial Logic (Why Decimal Matters)
All monetary calculations use decimal.Decimal with ROUND_HALF_EVEN (banker’s rounding) — the same standard used in financial institutions.
This eliminates floating‑point drift and ensures cent‑perfect accuracy across thousands of calculations.

Verified Date & Time Logic
The date engine is hardened against real‑world edge cases:

  * Leap year correctness (e.g., Feb 29 handling)

  * Month‑end boundary conditions

  * Inclusive day counting for pacing accuracy

All date logic is validated using property‑based tests spanning 200 years of calendar data.

Reliability & Testing

  * 101 automated tests

  * 100% pass rate

  * Property‑based tests using Hypothesis

  * Explicit validation of financial and temporal correctness

Validated properties include:

  * Decimal arithmetic preservation

  * Risk classification accuracy

  * VAT‑safe budget separation

  * Audit serialisation round‑trip integrity

Engineering Use Cases Beyond Advertising
The same architecture applies to:

  * Subscription billing systems

  * Usage‑based pricing engines

  * Budget enforcement for SaaS platforms

  * Financial reporting pipelines

  * Quota and allocation systems

## Risk Classification

| Status | Condition | Recommended Action |
|--------|-----------|-------------------|
| 🔴 **CRITICAL** | Spend % exceeds Time % by >15 points | Immediate budget reduction required |
| 🟡 **WARNING** | Spend % exceeds Time % by 5-15 points | Monitor daily, consider adjustment |
| 🟢 **HEALTHY** | Spend % within 5 points of Time % | On track — no action needed |
| ⚫ **OVER BUDGET** | Spend exceeds 100% of budget | Budget exhausted — pause campaign |

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Runtime** | Python 3.11+ | Modern async support, performance improvements |
| **Arithmetic** | `decimal.Decimal` | Eliminates floating-point errors in currency math |
| **Rounding** | `ROUND_HALF_EVEN` | Banker's Rounding — fair distribution over large datasets |
| **Testing** | `hypothesis` | Property-based testing with 100+ iterations per property |
| **Excel** | `openpyxl` | Native .xlsx generation with conditional formatting |
| **Validation** | Custom `DataValidator` | Row-level error reporting for CSV troubleshooting |

---

## Reliability Score

<table>
<tr>
<td align="center">
<h1>101</h1>
<p><strong>Automated Tests</strong></p>
</td>
<td align="center">
<h1>100%</h1>
<p><strong>Pass Rate</strong></p>
</td>
<td align="center">
<h1>7</h1>
<p><strong>Correctness Properties</strong></p>
</td>
</tr>
</table>

**Validated Properties:**
1. CSV Parsing Preserves All Valid Rows
2. Invalid Monetary Values Are Rejected with Row Numbers
3. Days Remaining Calculation Survives Leap Years
4. RDS Formula Correctness with Banker's Rounding
5. Risk Classification Threshold Accuracy
6. Decimal Arithmetic Preservation (No Float Contamination)
7. Serialisation Round-Trip Preserves Precision

---

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/Herman940306/BudgetGuard-ZAR.git
cd BudgetGuard-ZAR
pip install -r requirements.txt
```

### 2. Prepare Your Campaign Data

Create a CSV file with your campaign spend data:

```csv
Campaign,Monthly_Budget,Current_Spend
Holiday_Sale_2024,R 50000,R 35000
Brand_Awareness_Q4,R 30000,R 12000
Lead_Gen_December,R 25000,R 20000
Retargeting_Campaign,R 15000,R 16500
Product_Launch_ZA,R 40000,R 18000
```

**Column Definitions:**
- `Campaign`: Unique campaign identifier
- `Monthly_Budget`: Net Platform Spend in ZAR (VAT exclusive)
- `Current_Spend`: Amount spent to date on ad platforms

### 3. Run Analysis

```bash
python main.py data/sample_campaigns.csv --output-dir reports/
```

### 4. Review Output

The tool generates two files:
- `budget_report_YYYY-MM-DD_HHMMSS.xlsx` — Professional Excel dashboard
- `budget_audit_YYYY-MM-DD_HHMMSS.json` — JSON snapshot for audit compliance

---

## Sample Output

```
============================================================
  BudgetGuard ZAR - Financial Safety Tool
  Version: 0.1.0
  Zero-Overspend Guarantee for SA Advertising Agencies
============================================================

  Loading: sample_campaigns.csv
  ✓ Validated 5 campaigns
  Calculating pacing metrics...
  ✓ Audit log saved: output/budget_audit_2024-12-18_143758.json
  ✓ Excel report saved: output/budget_report_2024-12-18_143758.xlsx

============================================================
  ANALYSIS COMPLETE
============================================================

  PORTFOLIO OVERVIEW
  ----------------------------------------
  Total Budget:      R 160,000.00
  Total Spend:       R 101,500.00
  Remaining:         R 58,500.00
  Overall RDS:       R 4,285.71

  RISK SUMMARY
  ----------------------------------------
  ⚠️  CRITICAL:       1 campaigns
  ⚡ WARNING:        1 campaigns
  ✓  HEALTHY:        2 campaigns
  ❌ OVER BUDGET:    1 campaigns

  Total Campaigns:   5

  ⚠️  CRITICAL ALERTS - IMMEDIATE ACTION REQUIRED
  ----------------------------------------
  • Lead_Gen_December
    Spend: 80.0% | Time: 58.1%
    Variance: +21.9% over pace
    RDS: R 357.14

============================================================
  BudgetGuard ZAR - Analysis Complete
============================================================
```

---

## Project Structure

```
BudgetGuard-ZAR/
├── src/
│   ├── __init__.py        # Package version (0.1.0)
│   ├── schema.py          # Data models with Decimal types
│   ├── date_logic.py      # DateManager (leap year, days remaining)
│   ├── calculator.py      # PacingEngine (RDS, risk classification)
│   ├── validator.py       # CSV validation with row-level errors
│   ├── audit.py           # JSON serialisation for audit trails
│   └── excel_generator.py # Professional Excel reports
├── tests/
│   ├── test_date_logic.py      # 19 tests
│   ├── test_calculator.py      # 24 tests
│   ├── test_validator.py       # 26 tests
│   ├── test_audit.py           # 19 tests
│   └── test_excel_generator.py # 13 tests
├── main.py                # CLI entry point
├── requirements.txt       # Dependencies
└── README.md              # This file
```

---

## Running Tests

```bash
# Full test suite
pytest tests/ -v

# With coverage
pytest tests/ -v --tb=short
```

---

## License

MIT License

---

**Built with precision for South African advertising agencies who demand financial accuracy.**

*BudgetGuard ZAR — Because 99% correct is 100% wrong in financial reporting.*
