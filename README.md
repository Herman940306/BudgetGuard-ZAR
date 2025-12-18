# BudgetGuard ZAR

## Financial Safety Tool for South African Advertising Agencies

**Zero-Overspend Guarantee** — Precision budget monitoring that catches overruns before they happen.

---

## Executive Summary

BudgetGuard ZAR is an enterprise-grade financial safety tool engineered specifically for South African advertising agencies managing digital media spend. The system provides real-time budget pacing analysis, calculating Recommended Daily Spend (RDS) values and flagging campaigns at risk of overspend before budget breaches occur.

**Core Value Proposition:**
- Prevent client budget overruns with proactive risk detection
- Generate professional Excel reports for stakeholder presentations
- Maintain auditable JSON snapshots for financial compliance
- Ensure media buyers set accurate daily budgets in Meta/Google Ads

---

## The South African Edge

BudgetGuard ZAR is purpose-built for the South African advertising market with localisation features that generic tools cannot match:

### ZAR VAT-Awareness (15%)

The system natively distinguishes between **Gross Budget** (VAT inclusive) and **Net Platform Spend** (VAT exclusive). This critical distinction ensures that ad spend never accidentally consumes the VAT portion, protecting agency margins and preventing costly reconciliation errors.

```
Gross Budget (Client Invoice):  R 115,000.00
VAT Component (15%):            R  15,000.00
Net Platform Spend (Actual):    R 100,000.00  ← This is what goes to Meta/Google
```

### Banker's Rounding for Financial Integrity

All monetary calculations use `decimal.Decimal` with `ROUND_HALF_EVEN` (Banker's Rounding) — the same standard used by financial institutions. This eliminates the floating-point precision errors that plague spreadsheet-based solutions and ensures cent-perfect accuracy across thousands of transactions.

### Verified Date Logic

The date engine has been rigorously tested against edge cases that commonly cause pacing errors:

- **Leap Year Handling**: February 29th correctly identified in leap years (2024, 2028)
- **Month-End Boundaries**: Last day of month returns exactly 1 day remaining
- **Inclusive Day Counting**: December 18th in a 31-day month = 14 days remaining (not 13)

Every date calculation is backed by property-based tests spanning 200 years of calendar data.

---

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
