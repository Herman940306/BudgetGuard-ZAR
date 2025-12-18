"""
BudgetGuard ZAR - Date Logic Module.

This module provides date calculations for budget pacing, including
leap year detection, days-in-month calculations, and time percentage
computations.

Classes:
    DateManager: Manages all date-related calculations for budget pacing.
"""

import calendar
from datetime import date
from decimal import Decimal
from typing import Optional


class DateManager:
    """
    Manages date calculations for budget pacing.

    Handles month-end detection, leap year logic, and days remaining
    calculations. All percentage calculations return Decimal values
    for precision.

    Example:
        >>> dm = DateManager()
        >>> dm.get_days_remaining(date(2024, 12, 15))
        17
        >>> dm.is_leap_year(2024)
        True
    """

    def is_leap_year(self, year: int) -> bool:
        """
        Determines if the specified year is a leap year.

        A year is a leap year if it is divisible by 4, except for
        century years which must be divisible by 400.

        Args:
            year: Four-digit year to check.

        Returns:
            True if the year is a leap year, False otherwise.
        """
        return calendar.isleap(year)

    def get_days_in_month(self, year: int, month: int) -> int:
        """
        Returns the total number of days in the specified month.

        Correctly handles February in leap years (29 days) and
        non-leap years (28 days).

        Args:
            year: Four-digit year.
            month: Month number (1-12).

        Returns:
            Number of days in the specified month.

        Raises:
            ValueError: If month is not in range 1-12.
        """
        if not 1 <= month <= 12:
            raise ValueError(f"Month must be between 1 and 12, got {month}")
        return calendar.monthrange(year, month)[1]

    def get_days_remaining(self, reference_date: Optional[date] = None) -> int:
        """
        Calculates days remaining in the current month, inclusive of today.

        The current day is counted as a spending day, so the last day
        of the month returns 1, not 0.

        Args:
            reference_date: Date to calculate from. Defaults to today.

        Returns:
            Number of days remaining including the reference date.
            Minimum value is 1.
        """
        if reference_date is None:
            reference_date = date.today()

        total_days = self.get_days_in_month(reference_date.year, reference_date.month)
        days_remaining = total_days - reference_date.day + 1

        return days_remaining

    def get_days_elapsed(self, reference_date: Optional[date] = None) -> int:
        """
        Calculates the number of days elapsed in the current month.

        Includes the current day as an elapsed day.

        Args:
            reference_date: Date to calculate from. Defaults to today.

        Returns:
            Number of days elapsed including the reference date.
        """
        if reference_date is None:
            reference_date = date.today()

        return reference_date.day

    def get_time_percentage(self, reference_date: Optional[date] = None) -> Decimal:
        """
        Calculates the percentage of the month elapsed.

        Uses Decimal arithmetic for precision. The percentage represents
        how much of the month has passed based on days elapsed.

        Args:
            reference_date: Date to calculate from. Defaults to today.

        Returns:
            Decimal percentage (0-100) of month elapsed.
        """
        if reference_date is None:
            reference_date = date.today()

        days_elapsed = Decimal(str(self.get_days_elapsed(reference_date)))
        total_days = Decimal(str(self.get_days_in_month(
            reference_date.year,
            reference_date.month
        )))

        percentage = (days_elapsed / total_days) * Decimal("100")
        return percentage
