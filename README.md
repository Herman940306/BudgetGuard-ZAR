# BudgetGuard ZAR

**Financial Safety Tool for South African Advertising Agencies**

Zero-Overspend Guarantee — Catch budget overruns before they happen.

## Key Features

- **Risk Mitigation Engine**: Automatically flags campaigns at risk of overspend
- **ZAR Native**: Built for South African Rand with 15% VAT awareness
- **Precision Arithmetic**: Uses Decimal math with Banker's Rounding — no floating-point errors
- **Executive Reporting**: Professional Excel reports with Finance Summary and Campaign Deep-Dive tabs
- **Audit Trail**: JSON snapshots for financial compliance

## Risk Classification

| Status | Condition | Action |
|--------|-----------|--------|
| 🔴 CRITICAL | Spend % exceeds Time % by >15 points | Immediate intervention required |
| 🟡 WARNING | Spend % exceeds Time % by 5-15 points | Monitor closely |
| 🟢 HEALTHY | Spend % within 5 points of Time % | On track |
| ⚫ OVER BUDGET | Spend exceeds 100% of budget | Budget exceeded |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Your CSV

Create a CSV file with your campaign data:

```csv
Campaign,Monthly_Budget,Current_Spend
Holiday_Sale_2024,R 50000,R 35000
Brand_Awareness_Q4,R 30000,R 12000
Lead_Gen_December,R 25000,R 20000
```

**Columns:**
- `Campaign`: Campaign name/identifier
- `Monthly_Budget`: Net Platform Spend in ZAR (VAT exclusive)
- `Current_Spend`: Amount spent to date

### 3. Run Analysis

```bash
python main.py your_campaigns.csv --output-dir reports/
```

### 4. Review Output

The tool generates:
- **Excel Report** (`budget_report_*.xlsx`): Professional dashboard with risk highlighting
- **Audit Log** (`budget_audit_*.json`): JSON snapshot for compliance

## Example Output

```
============================================================
  BudgetGuard ZAR - Financial Safety Tool
  Version: 0.1.0
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

  ⚠️  CRITICAL ALERTS - IMMEDIATE ACTION REQUIRED
  ----------------------------------------
  • Lead_Gen_December
    Spend: 80.0% | Time: 58.1%
    Variance: +21.9% over pace
    RDS: R 357.14
```

## Tech Stack

- **Python 3.11+**
- **Decimal**: Precision financial arithmetic
- **openpyxl**: Excel report generation
- **hypothesis**: Property-based testing

## Project Structure

```
BudgetGuard-ZAR/
├── src/
│   ├── schema.py          # Data models (Decimal types)
│   ├── date_logic.py      # DateManager (leap year, days remaining)
│   ├── calculator.py      # PacingEngine (RDS, risk classification)
│   ├── validator.py       # CSV validation with row-level errors
│   ├── audit.py           # JSON serialisation for audit trails
│   └── excel_generator.py # Professional Excel reports
├── tests/                 # 101 tests (unit + property-based)
├── main.py                # CLI entry point
└── README.md
```

## Testing

Run the full test suite:

```bash
pytest tests/ -v
```

**Test Coverage:**
- 101 tests passing
- Property-based tests using Hypothesis
- Validates: Decimal precision, leap years, risk thresholds, round-trip serialisation

## License

MIT License

---

**Built for South African advertising agencies who demand financial precision.**
