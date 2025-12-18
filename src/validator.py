"""
BudgetGuard ZAR - Data Validation Module.

This module provides CSV validation and parsing for campaign budget data.
All monetary values are converted to Decimal type with comprehensive
error reporting including row numbers.

South African Market Context:
    - Supports both Gross (VAT inclusive) and Net (VAT exclusive) budgets
    - Default VAT rate: 15%
    - Handles ZAR currency formatting variations

Classes:
    ValidationError: Custom exception for validation failures.
    ValidationResult: Container for validation outcomes.
    DataValidator: Main validation class for CSV processing.
"""

import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path
from typing import List, Optional, Tuple, Union

from src.schema import Campaign, ZAR_VAT_RATE, calculate_net_from_gross


@dataclass
class ValidationError:
    """
    Represents a single validation error with context.

    Attributes:
        row_number: The 1-based row number in the CSV (excluding header).
        field_name: The name of the field that failed validation.
        value: The invalid value that was provided.
        message: A client-facing error message.
    """

    row_number: int
    field_name: str
    value: str
    message: str

    def __str__(self) -> str:
        """Returns a formatted error message for client display."""
        return f"Error: Row {self.row_number} '{self.field_name}' - {self.message}"


@dataclass
class ValidationResult:
    """
    Container for CSV validation results.

    Attributes:
        campaigns: List of successfully validated Campaign objects.
        errors: List of ValidationError objects for failed rows.
        is_valid: True if no errors occurred.
        total_rows: Total number of data rows processed.
    """

    campaigns: List[Campaign] = field(default_factory=list)
    errors: List[ValidationError] = field(default_factory=list)
    total_rows: int = 0

    @property
    def is_valid(self) -> bool:
        """Returns True if validation produced no errors."""
        return len(self.errors) == 0

    @property
    def valid_count(self) -> int:
        """Returns the number of successfully validated campaigns."""
        return len(self.campaigns)

    @property
    def error_count(self) -> int:
        """Returns the number of validation errors."""
        return len(self.errors)


class DataValidator:
    """
    Validates CSV input and converts to Campaign objects.

    Ensures all monetary values are converted to Decimal type
    and validates required columns and data formats. Supports
    VAT-aware budget handling for South African market.

    Attributes:
        REQUIRED_COLUMNS: List of mandatory CSV column names.
        OPTIONAL_COLUMNS: List of optional CSV column names.

    Example:
        >>> validator = DataValidator()
        >>> result = validator.validate_csv("campaigns.csv")
        >>> if result.is_valid:
        ...     for campaign in result.campaigns:
        ...         print(campaign.name)
    """

    REQUIRED_COLUMNS = ["Campaign", "Monthly_Budget", "Current_Spend"]
    OPTIONAL_COLUMNS = ["Gross_Budget"]

    # Pattern to clean currency strings (removes R, spaces, commas)
    CURRENCY_CLEAN_PATTERN = re.compile(r"[R\s,]")

    def __init__(self, vat_rate: Optional[Decimal] = None):
        """
        Initialises the DataValidator.

        Args:
            vat_rate: VAT rate for gross-to-net conversion.
                      Defaults to ZAR_VAT_RATE (15%).
        """
        self._vat_rate = vat_rate if vat_rate is not None else ZAR_VAT_RATE

    def validate_csv(
        self,
        file_path: Union[str, Path],
        has_header: bool = True
    ) -> ValidationResult:
        """
        Validates a CSV file for required structure and data types.

        Parses the CSV, validates each row, and converts monetary
        values to Decimal type. Errors are collected with row numbers
        for easy identification.

        Args:
            file_path: Path to the CSV file.
            has_header: Whether the CSV has a header row. Defaults to True.

        Returns:
            ValidationResult with campaigns list and any errors.

        Raises:
            FileNotFoundError: If the CSV file does not exist.
            ValueError: If required columns are missing.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {file_path}"
            )

        result = ValidationResult()

        with open(file_path, "r", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile) if has_header else None

            if has_header:
                # Validate columns
                missing = self._check_required_columns(reader.fieldnames or [])
                if missing:
                    raise ValueError(
                        f"Missing required columns: {', '.join(missing)}"
                    )

                for row_num, row in enumerate(reader, start=2):
                    result.total_rows += 1
                    campaign, errors = self._validate_row(row, row_num)

                    if campaign:
                        result.campaigns.append(campaign)
                    result.errors.extend(errors)
            else:
                # Handle CSV without header (use positional columns)
                csvfile.seek(0)
                reader = csv.reader(csvfile)
                for row_num, row in enumerate(reader, start=1):
                    result.total_rows += 1
                    if len(row) < 3:
                        result.errors.append(ValidationError(
                            row_number=row_num,
                            field_name="Row",
                            value=str(row),
                            message="Row must have at least 3 columns: "
                                    "Campaign, Monthly_Budget, Current_Spend"
                        ))
                        continue

                    row_dict = {
                        "Campaign": row[0],
                        "Monthly_Budget": row[1],
                        "Current_Spend": row[2],
                    }
                    if len(row) > 3:
                        row_dict["Gross_Budget"] = row[3]

                    campaign, errors = self._validate_row(row_dict, row_num)
                    if campaign:
                        result.campaigns.append(campaign)
                    result.errors.extend(errors)

        return result

    def validate_rows(
        self,
        rows: List[dict],
        start_row: int = 2
    ) -> ValidationResult:
        """
        Validates a list of row dictionaries.

        Useful for validating data from sources other than CSV files.

        Args:
            rows: List of dictionaries with campaign data.
            start_row: Starting row number for error reporting.

        Returns:
            ValidationResult with campaigns list and any errors.
        """
        result = ValidationResult()
        result.total_rows = len(rows)

        for idx, row in enumerate(rows):
            row_num = start_row + idx
            campaign, errors = self._validate_row(row, row_num)

            if campaign:
                result.campaigns.append(campaign)
            result.errors.extend(errors)

        return result

    def _check_required_columns(
        self,
        columns: List[str]
    ) -> List[str]:
        """
        Checks if all required columns are present.

        Args:
            columns: List of column names from CSV header.

        Returns:
            List of missing column names (empty if all present).
        """
        columns_lower = [c.lower().strip() for c in columns]
        missing = []

        for required in self.REQUIRED_COLUMNS:
            if required.lower() not in columns_lower:
                missing.append(required)

        return missing

    def _validate_row(
        self,
        row: dict,
        row_number: int
    ) -> Tuple[Optional[Campaign], List[ValidationError]]:
        """
        Validates a single row and converts to Campaign.

        Args:
            row: Dictionary with row data.
            row_number: Row number for error reporting.

        Returns:
            Tuple of (Campaign or None, list of errors).
        """
        errors: List[ValidationError] = []

        # Validate campaign name
        campaign_name = row.get("Campaign", "").strip()
        if not campaign_name:
            errors.append(ValidationError(
                row_number=row_number,
                field_name="Campaign",
                value=row.get("Campaign", ""),
                message="Campaign name cannot be empty"
            ))

        # Handle optional Gross_Budget first (for VAT conversion)
        gross_budget: Optional[Decimal] = None
        gross_str = row.get("Gross_Budget", "").strip()
        if gross_str:
            gross_budget, gross_error = self._parse_decimal(
                gross_str,
                "Gross_Budget",
                row_number,
                must_be_positive=True
            )
            if gross_error:
                errors.append(gross_error)
                gross_budget = None

        # Validate Monthly_Budget (must be positive, unless Gross_Budget provided)
        budget_str = row.get("Monthly_Budget", "").strip()
        monthly_budget: Optional[Decimal] = None
        
        if budget_str:
            monthly_budget, budget_error = self._parse_decimal(
                budget_str,
                "Monthly_Budget",
                row_number,
                must_be_positive=True
            )
            if budget_error:
                errors.append(budget_error)
        elif gross_budget is not None:
            # Calculate net from gross if Monthly_Budget is empty
            monthly_budget = calculate_net_from_gross(gross_budget)
        else:
            # Neither Monthly_Budget nor Gross_Budget provided
            errors.append(ValidationError(
                row_number=row_number,
                field_name="Monthly_Budget",
                value=budget_str,
                message="Monthly_Budget cannot be empty (or provide Gross_Budget)"
            ))

        # Validate Current_Spend (must be non-negative)
        spend_str = row.get("Current_Spend", "")
        current_spend, spend_error = self._parse_decimal(
            spend_str,
            "Current_Spend",
            row_number,
            must_be_positive=False,
            allow_zero=True
        )
        if spend_error:
            errors.append(spend_error)

        # Return None if any required field failed
        if errors or monthly_budget is None or current_spend is None:
            return None, errors

        campaign = Campaign(
            name=campaign_name,
            monthly_budget=monthly_budget,
            current_spend=current_spend,
            gross_budget=gross_budget
        )

        return campaign, errors

    def _parse_decimal(
        self,
        value: str,
        field_name: str,
        row_number: int,
        must_be_positive: bool = False,
        allow_zero: bool = False
    ) -> Tuple[Optional[Decimal], Optional[ValidationError]]:
        """
        Parses a string value to Decimal with validation.

        Handles various ZAR currency formats:
        - "10000" (plain number)
        - "10,000" (with thousands separator)
        - "R 10,000" (with currency symbol)
        - "R10000.00" (with symbol and decimals)

        Args:
            value: String value to parse.
            field_name: Name of the field for error messages.
            row_number: Row number for error messages.
            must_be_positive: If True, value must be > 0.
            allow_zero: If True, zero is allowed (for non-negative fields).

        Returns:
            Tuple of (Decimal value or None, ValidationError or None).
        """
        if value is None:
            value = ""

        original_value = value
        value = value.strip()

        if not value:
            return None, ValidationError(
                row_number=row_number,
                field_name=field_name,
                value=original_value,
                message=f"{field_name} cannot be empty"
            )

        # Detect European format (comma as decimal separator) - reject it
        # Pattern: digits,digits without a period (e.g., "100,00" or "1000,50")
        if re.match(r"^R?\s*\d+,\d{2}$", value):
            return None, ValidationError(
                row_number=row_number,
                field_name=field_name,
                value=original_value,
                message=f"{field_name} appears to use European format (comma as decimal). "
                        f"Please use period as decimal separator (e.g., '100.00' not '100,00')"
            )

        # Clean the value: remove R, spaces, commas (thousands separator)
        cleaned = self.CURRENCY_CLEAN_PATTERN.sub("", value)

        # Check for invalid characters
        if not re.match(r"^-?\d+\.?\d*$", cleaned):
            return None, ValidationError(
                row_number=row_number,
                field_name=field_name,
                value=original_value,
                message=f"{field_name} must be a valid number "
                        f"(received: '{original_value}')"
            )

        try:
            decimal_value = Decimal(cleaned)
        except InvalidOperation:
            return None, ValidationError(
                row_number=row_number,
                field_name=field_name,
                value=original_value,
                message=f"{field_name} must be a valid number "
                        f"(received: '{original_value}')"
            )

        # Round to 2 decimal places
        decimal_value = decimal_value.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_EVEN
        )

        # Validate sign constraints
        if must_be_positive and decimal_value <= Decimal("0"):
            return None, ValidationError(
                row_number=row_number,
                field_name=field_name,
                value=original_value,
                message=f"{field_name} must be a positive number "
                        f"(received: '{original_value}')"
            )

        if not allow_zero and not must_be_positive and decimal_value < Decimal("0"):
            return None, ValidationError(
                row_number=row_number,
                field_name=field_name,
                value=original_value,
                message=f"{field_name} must be a non-negative number "
                        f"(received: '{original_value}')"
            )

        if allow_zero and decimal_value < Decimal("0"):
            return None, ValidationError(
                row_number=row_number,
                field_name=field_name,
                value=original_value,
                message=f"{field_name} must be a non-negative number "
                        f"(received: '{original_value}')"
            )

        return decimal_value, None

    def format_zar(self, amount: Decimal) -> str:
        """
        Formats a Decimal amount as ZAR currency string.

        Args:
            amount: Decimal amount to format.

        Returns:
            Formatted string like "R 12,345.67".
        """
        return f"R {amount:,.2f}"
