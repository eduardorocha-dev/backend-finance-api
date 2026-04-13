"""Currency helpers for NUMERIC(12,2) monetary values."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

_CENT = Decimal("0.01")


def to_decimal(value: float | str | Decimal) -> Decimal:
    """Convert any numeric value to a Decimal rounded to 2 decimal places."""
    return Decimal(str(value)).quantize(_CENT, rounding=ROUND_HALF_UP)


def format_amount(value: Decimal, symbol: str = "$") -> str:
    """Format a Decimal amount as a human-readable currency string."""
    return f"{symbol}{value:,.2f}"


def add(a: Decimal, b: Decimal) -> Decimal:
    return (a + b).quantize(_CENT, rounding=ROUND_HALF_UP)


def subtract(a: Decimal, b: Decimal) -> Decimal:
    return (a - b).quantize(_CENT, rounding=ROUND_HALF_UP)


def convert(amount: Decimal, rate: Decimal) -> Decimal:
    """Multiply *amount* by *rate* and round to 2 decimal places."""
    return (amount * rate).quantize(_CENT, rounding=ROUND_HALF_UP)