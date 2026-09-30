from pydantic import BaseModel, EmailStr

from app.models.account import CurrencyCode

# ── Incoming (what the client sends) ─────────────────────────────────────────


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    base_currency: CurrencyCode = CurrencyCode.USD


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserSettingsUpdate(BaseModel):
    """PATCH /auth/me. Password changes need the current password, so they're not here."""

    full_name: str | None = None
    base_currency: CurrencyCode | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None


# ── Outgoing (what the API sends back) ───────────────────────────────────────


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    base_currency: CurrencyCode

    model_config = {"from_attributes": True}


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
