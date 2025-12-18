"""
BudgetGuard ZAR - Date Logic Tests.

Property-based and unit tests for DateManager class.
Tests ensure correct handling of leap years, month boundaries,
and inclusive day counting.

**Feature: budgetguard-zar, Property 3: Days Remaining Calculation Correctness**
"""

import calendar
from datetime import date
from decimal import Decimal

import pytest
from hypothesis import given, settings, assume
from hypothesis.strategies import integers, dates

from src.date_logic import DateManager


class TestDateManagerUnit:
    """Unit tests for DateManager edge cases."""

    def setup_method(self) -> None:
        """Initialise DateManager for each test."""
        self.dm = DateManager()

    def test_leap_year_2024(self) -> None:
        """Verify 2024 is correctly identified as a leap year."""
        assert self.dm.is_leap_year(2024) is True

    def test_leap_year_2000(self) -> None:
        """Verify 2000 (divisible by 400) is a leap year."""
        assert self.dm.is_leap_year(2000) is True

    def test_non_leap_year_2023(self) -> None:
        """Verify 2023 is correctly identified as non-leap year."""
        assert self.dm.is_leap_year(2023) is False

    def test_non_leap_year_1900(self) -> None:
        """Verify 1900 (divisible by 100 but not 400) is not a leap year."""
        assert self.dm.is_leap_year(1900) is False

    def test_february_leap_year_days(self) -> None:
        """Verify February has 29 days in leap year."""
        assert self.dm.get_days_in_month(2024, 2) == 29

    def test_february_non_leap_year_days(self) -> None:
        """Verify February has 28 days in non-leap year."""
        assert self.dm.get_days_in_month(2023, 2) == 28

    def test_days_remaining_last_day_of_month(self) -> None:
        """Verify last day of month returns 1 day remaining."""
        last_day = date(2024, 12, 31)
        assert self.dm.get_days_remaining(last_day) == 1

    def test_days_remaining_first_day_of_month(self) -> None:
        """Verify first day of month returns total days."""
        first_day = date(2024, 12, 1)
        assert self.dm.get_days_remaining(first_day) == 31

    def test_days_remaining_dec_18_2024(self) -> None:
        """
        Verify Dec 18, 2024 returns 14 days remaining.
        
        Calculation: 31 - 18 + 1 = 14 (inclusive of current day).
        """
        dec_18 = date(2024, 12, 18)
        assert self.dm.get_days_remaining(dec_18) == 14

    def test_days_remaining_feb_29_leap_year(self) -> None:
        """Verify Feb 29 in leap year returns 1 day remaining."""
        feb_29 = date(2024, 2, 29)
        assert self.dm.get_days_remaining(feb_29) == 1

    def test_time_percentage_mid_month(self) -> None:
        """Verify time percentage calculation at mid-month."""
        mid_dec = date(2024, 12, 15)
        time_pct = self.dm.get_time_percentage(mid_dec)
        # 15/31 * 100 = 48.387...
        expected = (Decimal("15") / Decimal("31")) * Decimal("100")
        assert time_pct == expected

    def test_time_percentage_returns_decimal(self) -> None:
        """Verify time percentage returns Decimal type."""
        time_pct = self.dm.get_time_percentage(date(2024, 12, 18))
        assert isinstance(time_pct, Decimal)

    def test_invalid_month_raises_error(self) -> None:
        """Verify invalid month raises ValueError."""
        with pytest.raises(ValueError):
            self.dm.get_days_in_month(2024, 13)

        with pytest.raises(ValueError):
            self.dm.get_days_in_month(2024, 0)


class TestDateManagerProperty:
    """
    Property-based tests for DateManager.
    
    **Feature: budgetguard-zar, Property 3: Days Remaining Calculation Correctness**
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    """

    def setup_method(self) -> None:
        """Initialise DateManager for each test."""
        self.dm = DateManager()

    @given(dates(min_value=date(1900, 1, 1), max_value=date(2100, 12, 31)))
    @settings(max_examples=200)
    def test_days_remaining_formula(self, test_date: date) -> None:
        """
        Property: Days remaining equals (total_days - day + 1).
        
        **Feature: budgetguard-zar, Property 3: Days Remaining Calculation Correctness**
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
        
        For any date within a month, the days remaining calculation
        SHALL equal (total_days_in_month - day_of_month + 1).
        """
        total_days = calendar.monthrange(test_date.year, test_date.month)[1]
        expected = total_days - test_date.day + 1
        actual = self.dm.get_days_remaining(test_date)
        
        assert actual == expected, (
            f"Date {test_date}: expected {expected}, got {actual}"
        )

    @given(dates(min_value=date(1900, 1, 1), max_value=date(2100, 12, 31)))
    @settings(max_examples=200)
    def test_days_remaining_always_positive(self, test_date: date) -> None:
        """
        Property: Days remaining is always >= 1.
        
        The minimum value is 1 (on the last day of the month),
        ensuring there is always at least one spending day.
        """
        days_remaining = self.dm.get_days_remaining(test_date)
        assert days_remaining >= 1, (
            f"Date {test_date}: days_remaining={days_remaining} < 1"
        )

    @given(integers(min_value=1900, max_value=2100))
    @settings(max_examples=100)
    def test_leap_year_february_has_29_days(self, year: int) -> None:
        """
        Property: Leap year February has 29 days.
        
        **Feature: budgetguard-zar, Property 3: Days Remaining Calculation Correctness**
        **Validates: Requirements 2.2**
        """
        assume(calendar.isleap(year))
        assert self.dm.get_days_in_month(year, 2) == 29

    @given(integers(min_value=1900, max_value=2100))
    @settings(max_examples=100)
    def test_non_leap_year_february_has_28_days(self, year: int) -> None:
        """
        Property: Non-leap year February has 28 days.
        
        **Feature: budgetguard-zar, Property 3: Days Remaining Calculation Correctness**
        **Validates: Requirements 2.3**
        """
        assume(not calendar.isleap(year))
        assert self.dm.get_days_in_month(year, 2) == 28

    @given(dates(min_value=date(1900, 1, 1), max_value=date(2100, 12, 31)))
    @settings(max_examples=200)
    def test_time_percentage_in_valid_range(self, test_date: date) -> None:
        """
        Property: Time percentage is always between 0 and 100 (inclusive).
        
        On day 1, percentage > 0. On last day, percentage <= 100.
        """
        time_pct = self.dm.get_time_percentage(test_date)
        assert Decimal("0") < time_pct <= Decimal("100"), (
            f"Date {test_date}: time_percentage={time_pct} out of range"
        )

    @given(dates(min_value=date(1900, 1, 1), max_value=date(2100, 12, 31)))
    @settings(max_examples=200)
    def test_time_percentage_returns_decimal(self, test_date: date) -> None:
        """
        Property: Time percentage always returns Decimal type.
        
        Ensures no floating-point arithmetic is used.
        """
        time_pct = self.dm.get_time_percentage(test_date)
        assert isinstance(time_pct, Decimal), (
            f"Expected Decimal, got {type(time_pct)}"
        )
