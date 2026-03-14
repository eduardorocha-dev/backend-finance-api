from pydantic import BaseModel, EmailStr


# ── Incoming (what the client sends) ─────────────────────────────────────────


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None


# ── Outgoing (what the API sends back) ───────────────────────────────────────


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
