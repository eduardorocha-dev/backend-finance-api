from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.schemas.account import CurrencyCode


class ExchangeRateCreate(BaseModel):
    from_currency: CurrencyCode
    to_currency: CurrencyCode
    rate: Decimal
    effective_date: date

    @field_validator("rate")
    @classmethod
    def rate_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("rate must be positive")
        return v

    @field_validator("to_currency")
    @classmethod
    def currencies_must_differ(cls, v: CurrencyCode, info) -> CurrencyCode:
        if "from_currency" in info.data and v == info.data["from_currency"]:
            raise ValueError("from_currency and to_currency must be different")
        return v


class ExchangeRateUpdate(BaseModel):
    rate: Decimal

    @field_validator("rate")
    @classmethod
    def rate_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("rate must be positive")
        return v


class ExchangeRateRead(BaseModel):
    id: int
    from_currency: CurrencyCode
    to_currency: CurrencyCode
    rate: Decimal
    effective_date: date

    model_config = {"from_attributes": True}


class ConvertRequest(BaseModel):
    from_currency: CurrencyCode
    to_currency: CurrencyCode
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class ConvertResponse(BaseModel):
    from_currency: CurrencyCode
    to_currency: CurrencyCode
    original_amount: Decimal
    converted_amount: Decimal
    rate: Decimal
    effective_date: date
