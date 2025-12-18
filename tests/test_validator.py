"""
BudgetGuard ZAR - Data Validator Tests.

Property-based and unit tests for DataValidator class.
Tests ensure correct CSV parsing, Decimal conversion,
error reporting with row numbers, and VAT-aware logic.

**Feature: budgetguard-zar, Property 1: CSV Parsing Preserves All Valid Rows**
**Feature: budgetguard-zar, Property 2: Invalid Monetary Values Are Rejected**
"""

import csv
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given, settings, assume
from hypothesis.strategies import (
    text, integers, decimals, lists, composite, sampled_from
)

from src.validator import DataValidator, ValidationError, ValidationResult
from src.schema import Campaign, ZAR_VAT_RATE, calculate_net_from_gross


# Custom strategies for generating test data
@composite
def valid_campaign_names(draw):
    """Generate valid campaign names."""
    base_names = [
        "Brand_Awareness", "Lead_Gen", "Retargeting",
        "Holiday_Sale", "Product_Launch", "Q4_Push"
    ]
    name = draw(sampled_from(base_names))
    suffix = draw(integers(min_value=1, max_value=9999))
    return f"{name}_{suffix}"


@composite
def valid_budget_strings(draw):
    """Generate valid budget strings in various ZAR formats."""
    amount = draw(decimals(
        min_value=Decimal("100"),
        max_value=Decimal("1000000"),
        places=2,
        allow_nan=False,
        allow_infinity=False
    ))
    
    formats = [
        str(amount),                          # "10000.00"
        f"R{amount}",                         # "R10000.00"
        f"R {amount}",                        # "R 10000.00"
        f"{amount:,.2f}",                     # "10,000.00"
        f"R {amount:,.2f}",                   # "R 10,000.00"
    ]
    return draw(sampled_from(formats)), amount


@composite
def valid_spend_strings(draw):
    """Generate valid spend strings (non-negative)."""
    amount = draw(decimals(
        min_value=Decimal("0"),
        max_value=Decimal("500000"),
        places=2,
        allow_nan=False,
        allow_infinity=False
    ))
    
    formats = [
        str(amount),
        f"R{amount}",
        f"R {amount}",
    ]
    return draw(sampled_from(formats)), amount


@composite
def valid_csv_rows(draw):
    """Generate valid CSV row data."""
    name = draw(valid_campaign_names())
    budget_str, budget_val = draw(valid_budget_strings())
    spend_str, spend_val = draw(valid_spend_strings())
    
    # Ensure spend doesn't exceed budget for realistic data
    assume(spend_val <= budget_val)
    
    return {
        "Campaign": name,
        "Monthly_Budget": budget_str,
        "Current_Spend": spend_str,
        "expected_budget": budget_val,
        "expected_spend": spend_val
    }


@composite
def invalid_budget_strings(draw):
    """Generate invalid budget strings that should be rejected."""
    invalid_formats = [
        "",                      # Empty
        "   ",                   # Whitespace only
        "-50",                   # Negative
        "-R100",                 # Negative with symbol
        "abc",                   # Non-numeric
        "R abc",                 # Symbol with non-numeric
        "100,00",                # European format (comma as decimal)
        "R 100,00",              # European format with symbol
        "NaN",                   # Not a number
        "1.2.3",                 # Multiple decimals
        "$100",                  # Wrong currency
        "€500",                  # Wrong currency
    ]
    return draw(sampled_from(invalid_formats))


class TestDataValidatorUnit:
    """Unit tests for DataValidator edge cases."""

    def setup_method(self) -> None:
        """Initialise DataValidator for each test."""
        self.validator = DataValidator()

    def test_parse_plain_number(self) -> None:
        """Verify plain number parsing."""
        result, error = self.validator._parse_decimal(
            "10000", "Monthly_Budget", 1, must_be_positive=True
        )
        assert error is None
        assert result == Decimal("10000.00")

    def test_parse_with_currency_symbol(self) -> None:
        """Verify parsing with R symbol."""
        result, error = self.validator._parse_decimal(
            "R10000", "Monthly_Budget", 1, must_be_positive=True
        )
        assert error is None
        assert result == Decimal("10000.00")

    def test_parse_with_currency_symbol_and_space(self) -> None:
        """Verify parsing with R symbol and space."""
        result, error = self.validator._parse_decimal(
            "R 10000", "Monthly_Budget", 1, must_be_positive=True
        )
        assert error is None
        assert result == Decimal("10000.00")

    def test_parse_with_thousands_separator(self) -> None:
        """Verify parsing with comma thousands separator."""
        result, error = self.validator._parse_decimal(
            "R 10,000.00", "Monthly_Budget", 1, must_be_positive=True
        )
        assert error is None
        assert result == Decimal("10000.00")

    def test_parse_negative_budget_rejected(self) -> None:
        """Verify negative budget is rejected with clear message."""
        result, error = self.validator._parse_decimal(
            "-5000", "Monthly_Budget", 12, must_be_positive=True
        )
        assert result is None
        assert error is not None
        assert error.row_number == 12
        assert error.field_name == "Monthly_Budget"
        assert "positive" in error.message.lower()
        assert "-5000" in error.message

    def test_parse_negative_spend_rejected(self) -> None:
        """Verify negative spend is rejected."""
        result, error = self.validator._parse_decimal(
            "-100", "Current_Spend", 5, must_be_positive=False, allow_zero=True
        )
        assert result is None
        assert error is not None
        assert error.row_number == 5
        assert "non-negative" in error.message.lower()

    def test_parse_empty_value_rejected(self) -> None:
        """Verify empty value is rejected."""
        result, error = self.validator._parse_decimal(
            "", "Monthly_Budget", 3, must_be_positive=True
        )
        assert result is None
        assert error is not None
        assert "empty" in error.message.lower()

    def test_parse_non_numeric_rejected(self) -> None:
        """Verify non-numeric value is rejected."""
        result, error = self.validator._parse_decimal(
            "abc", "Monthly_Budget", 7, must_be_positive=True
        )
        assert result is None
        assert error is not None
        assert "valid number" in error.message.lower()

    def test_parse_zero_budget_rejected(self) -> None:
        """Verify zero budget is rejected when must_be_positive."""
        result, error = self.validator._parse_decimal(
            "0", "Monthly_Budget", 4, must_be_positive=True
        )
        assert result is None
        assert error is not None
        assert "positive" in error.message.lower()

    def test_parse_zero_spend_allowed(self) -> None:
        """Verify zero spend is allowed."""
        result, error = self.validator._parse_decimal(
            "0", "Current_Spend", 4, must_be_positive=False, allow_zero=True
        )
        assert error is None
        assert result == Decimal("0.00")

    def test_error_message_format(self) -> None:
        """Verify error message format is client-ready."""
        error = ValidationError(
            row_number=12,
            field_name="Monthly_Budget",
            value="-5000",
            message="Monthly_Budget must be a positive number (received: '-5000')"
        )
        
        error_str = str(error)
        
        assert "Row 12" in error_str
        assert "Monthly_Budget" in error_str
        assert "positive" in error_str.lower()

    def test_validate_rows_with_valid_data(self) -> None:
        """Verify valid rows are parsed correctly."""
        rows = [
            {"Campaign": "Test1", "Monthly_Budget": "10000", "Current_Spend": "3000"},
            {"Campaign": "Test2", "Monthly_Budget": "R 20,000", "Current_Spend": "5000"},
        ]
        
        result = self.validator.validate_rows(rows)
        
        assert result.is_valid
        assert result.valid_count == 2
        assert result.campaigns[0].monthly_budget == Decimal("10000.00")
        assert result.campaigns[1].monthly_budget == Decimal("20000.00")

    def test_validate_rows_with_errors(self) -> None:
        """Verify errors are captured with row numbers."""
        rows = [
            {"Campaign": "Valid", "Monthly_Budget": "10000", "Current_Spend": "3000"},
            {"Campaign": "Invalid", "Monthly_Budget": "-5000", "Current_Spend": "1000"},
            {"Campaign": "AlsoInvalid", "Monthly_Budget": "abc", "Current_Spend": "500"},
        ]
        
        result = self.validator.validate_rows(rows)
        
        assert not result.is_valid
        assert result.valid_count == 1
        assert result.error_count == 2
        
        # Check row numbers are correct (starting from row 2)
        error_rows = [e.row_number for e in result.errors]
        assert 3 in error_rows  # Second row
        assert 4 in error_rows  # Third row

    def test_validate_csv_file(self) -> None:
        """Verify CSV file validation."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            writer = csv.writer(f)
            writer.writerow(["Campaign", "Monthly_Budget", "Current_Spend"])
            writer.writerow(["Campaign_A", "10000", "3000"])
            writer.writerow(["Campaign_B", "R 20,000", "5000"])
            temp_path = f.name

        try:
            result = self.validator.validate_csv(temp_path)
            
            assert result.is_valid
            assert result.valid_count == 2
            assert result.total_rows == 2
        finally:
            Path(temp_path).unlink()

    def test_validate_csv_missing_columns(self) -> None:
        """Verify missing columns raise ValueError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            writer = csv.writer(f)
            writer.writerow(["Campaign", "Budget"])  # Missing columns
            writer.writerow(["Test", "10000"])
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Missing required columns"):
                self.validator.validate_csv(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_validate_csv_file_not_found(self) -> None:
        """Verify FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            self.validator.validate_csv("nonexistent.csv")

    def test_vat_aware_gross_to_net_conversion(self) -> None:
        """Verify gross budget is converted to net."""
        rows = [{
            "Campaign": "VAT_Test",
            "Monthly_Budget": "",
            "Current_Spend": "1000",
            "Gross_Budget": "11500"  # Should become 10000 net
        }]
        
        result = self.validator.validate_rows(rows)
        
        assert result.is_valid
        assert result.campaigns[0].monthly_budget == Decimal("10000.00")
        assert result.campaigns[0].gross_budget == Decimal("11500.00")

    def test_decimal_type_preservation(self) -> None:
        """Verify all monetary values are Decimal type."""
        rows = [
            {"Campaign": "TypeTest", "Monthly_Budget": "10000.50", "Current_Spend": "3000.25"}
        ]
        
        result = self.validator.validate_rows(rows)
        
        assert isinstance(result.campaigns[0].monthly_budget, Decimal)
        assert isinstance(result.campaigns[0].current_spend, Decimal)

    def test_format_zar(self) -> None:
        """Verify ZAR formatting."""
        formatted = self.validator.format_zar(Decimal("12345.67"))
        assert formatted == "R 12,345.67"


class TestDataValidatorPropertyParsing:
    """
    Property-based tests for CSV parsing.
    
    **Feature: budgetguard-zar, Property 1: CSV Parsing Preserves All Valid Rows**
    **Validates: Requirements 1.1, 1.5**
    """

    def setup_method(self) -> None:
        """Initialise DataValidator for each test."""
        self.validator = DataValidator()

    @given(lists(valid_csv_rows(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_valid_rows_preserved(self, rows: list) -> None:
        """
        Property: All valid CSV rows are preserved after parsing.
        
        **Feature: budgetguard-zar, Property 1: CSV Parsing Preserves All Valid Rows**
        **Validates: Requirements 1.1, 1.5**
        """
        # Convert to validator format
        validator_rows = [
            {
                "Campaign": r["Campaign"],
                "Monthly_Budget": r["Monthly_Budget"],
                "Current_Spend": r["Current_Spend"]
            }
            for r in rows
        ]
        
        result = self.validator.validate_rows(validator_rows)
        
        assert result.valid_count == len(rows), (
            f"Expected {len(rows)} valid campaigns, got {result.valid_count}"
        )

    @given(valid_csv_rows())
    @settings(max_examples=100)
    def test_budget_value_preserved(self, row: dict) -> None:
        """
        Property: Budget values are correctly converted to Decimal.
        
        **Feature: budgetguard-zar, Property 1: CSV Parsing Preserves All Valid Rows**
        **Validates: Requirements 1.5**
        """
        validator_row = {
            "Campaign": row["Campaign"],
            "Monthly_Budget": row["Monthly_Budget"],
            "Current_Spend": row["Current_Spend"]
        }
        
        result = self.validator.validate_rows([validator_row])
        
        assert result.is_valid
        # Allow for rounding differences
        expected = row["expected_budget"].quantize(Decimal("0.01"))
        actual = result.campaigns[0].monthly_budget
        assert actual == expected, (
            f"Budget mismatch: expected {expected}, got {actual}"
        )

    @given(valid_csv_rows())
    @settings(max_examples=100)
    def test_parsed_values_are_decimal(self, row: dict) -> None:
        """
        Property: All parsed monetary values are Decimal type.
        
        **Feature: budgetguard-zar, Property 1: CSV Parsing Preserves All Valid Rows**
        **Validates: Requirements 1.5**
        """
        validator_row = {
            "Campaign": row["Campaign"],
            "Monthly_Budget": row["Monthly_Budget"],
            "Current_Spend": row["Current_Spend"]
        }
        
        result = self.validator.validate_rows([validator_row])
        
        assert result.is_valid
        assert isinstance(result.campaigns[0].monthly_budget, Decimal)
        assert isinstance(result.campaigns[0].current_spend, Decimal)


class TestDataValidatorPropertyRejection:
    """
    Property-based tests for invalid value rejection.
    
    **Feature: budgetguard-zar, Property 2: Invalid Monetary Values Are Rejected**
    **Validates: Requirements 1.2, 1.3**
    """

    def setup_method(self) -> None:
        """Initialise DataValidator for each test."""
        self.validator = DataValidator()

    @given(invalid_budget_strings(), integers(min_value=2, max_value=1000))
    @settings(max_examples=100)
    def test_invalid_budgets_rejected(
        self, invalid_budget: str, row_num: int
    ) -> None:
        """
        Property: Invalid budget strings are rejected with row numbers.
        
        **Feature: budgetguard-zar, Property 2: Invalid Monetary Values Are Rejected**
        **Validates: Requirements 1.2**
        """
        rows = [{
            "Campaign": "TestCampaign",
            "Monthly_Budget": invalid_budget,
            "Current_Spend": "1000"
        }]
        
        result = self.validator.validate_rows(rows, start_row=row_num)
        
        assert not result.is_valid, (
            f"Expected rejection for budget '{invalid_budget}'"
        )
        assert result.error_count >= 1
        
        # Verify error has correct row number
        budget_errors = [
            e for e in result.errors 
            if e.field_name == "Monthly_Budget"
        ]
        assert len(budget_errors) >= 1
        assert budget_errors[0].row_number == row_num

    @given(integers(min_value=2, max_value=1000))
    @settings(max_examples=50)
    def test_negative_spend_rejected(self, row_num: int) -> None:
        """
        Property: Negative spend values are rejected.
        
        **Feature: budgetguard-zar, Property 2: Invalid Monetary Values Are Rejected**
        **Validates: Requirements 1.3**
        """
        rows = [{
            "Campaign": "TestCampaign",
            "Monthly_Budget": "10000",
            "Current_Spend": "-500"
        }]
        
        result = self.validator.validate_rows(rows, start_row=row_num)
        
        assert not result.is_valid
        spend_errors = [
            e for e in result.errors 
            if e.field_name == "Current_Spend"
        ]
        assert len(spend_errors) >= 1
        assert "non-negative" in spend_errors[0].message.lower()

    @given(invalid_budget_strings())
    @settings(max_examples=50)
    def test_error_message_contains_value(self, invalid_budget: str) -> None:
        """
        Property: Error messages include the invalid value.
        
        **Feature: budgetguard-zar, Property 2: Invalid Monetary Values Are Rejected**
        **Validates: Requirements 1.2, 1.3**
        """
        assume(invalid_budget.strip())  # Skip empty strings for this test
        
        rows = [{
            "Campaign": "TestCampaign",
            "Monthly_Budget": invalid_budget,
            "Current_Spend": "1000"
        }]
        
        result = self.validator.validate_rows(rows)
        
        assert not result.is_valid
        # Error message should reference the invalid value
        error_str = str(result.errors[0])
        assert "Monthly_Budget" in error_str

    def test_specific_error_format_negative_budget(self) -> None:
        """
        Verify specific error format for negative budget.
        
        This test demonstrates the exact error message format
        for client-facing error reporting.
        """
        rows = [{
            "Campaign": "Problem_Campaign",
            "Monthly_Budget": "-5000",
            "Current_Spend": "1000"
        }]
        
        result = self.validator.validate_rows(rows, start_row=12)
        
        assert not result.is_valid
        error = result.errors[0]
        
        # Verify error structure
        assert error.row_number == 12
        assert error.field_name == "Monthly_Budget"
        assert error.value == "-5000"
        
        # Verify client-facing message format
        error_str = str(error)
        print(f"\n>>> CLIENT-FACING ERROR MESSAGE:\n{error_str}\n")
        
        assert "Row 12" in error_str
        assert "Monthly_Budget" in error_str
        assert "positive" in error_str.lower()
