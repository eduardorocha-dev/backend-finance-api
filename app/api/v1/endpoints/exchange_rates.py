from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.account import CurrencyCode
from app.models.user import User
from app.schemas.exchange_rate import (
    ConvertRequest,
    ConvertResponse,
    ExchangeRateCreate,
    ExchangeRateRead,
    ExchangeRateUpdate,
)
from app.services.exchange_rate import ExchangeRateService

router = APIRouter(prefix="/exchange-rates", tags=["Exchange Rates"])


@router.post("", response_model=ExchangeRateRead, status_code=status.HTTP_201_CREATED)
async def create_exchange_rate(
    data: ExchangeRateCreate,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    er = await ExchangeRateService(session).create(data)
    await session.commit()
    return er


@router.get("/latest", response_model=ExchangeRateRead)
async def get_latest_rate(
    from_currency: Annotated[CurrencyCode, Query()],
    to_currency: Annotated[CurrencyCode, Query()],
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await ExchangeRateService(session).get_latest(from_currency, to_currency)


@router.get("", response_model=list[ExchangeRateRead])
async def list_rates_for_pair(
    from_currency: Annotated[CurrencyCode, Query()],
    to_currency: Annotated[CurrencyCode, Query()],
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
):
    return await ExchangeRateService(session).list_for_pair(from_currency, to_currency, limit)


@router.get("/{exchange_rate_id}", response_model=ExchangeRateRead)
async def get_exchange_rate(
    exchange_rate_id: int,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await ExchangeRateService(session).get(exchange_rate_id)


@router.patch("/{exchange_rate_id}", response_model=ExchangeRateRead)
async def update_exchange_rate(
    exchange_rate_id: int,
    data: ExchangeRateUpdate,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    er = await ExchangeRateService(session).update(exchange_rate_id, data)
    await session.commit()
    return er


@router.delete("/{exchange_rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange_rate(
    exchange_rate_id: int,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    await ExchangeRateService(session).delete(exchange_rate_id)
    await session.commit()


@router.post("/convert", response_model=ConvertResponse)
async def convert_currency(
    data: ConvertRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await ExchangeRateService(session).convert(data)
