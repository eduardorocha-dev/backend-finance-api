from fastapi import APIRouter

from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=201)
async def register(data: UserCreate):
    return {
        "id": 1,
        "email": data.email,
        "full_name": data.full_name,
        "is_active": True,
    }


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    return {"access_token": "fake-token-123", "refresh_token": "fake-refresh-123"}


@router.get("/me", response_model=UserRead)
async def me():
    return {
        "id": 1,
        "email": "alice@example.com",
        "full_name": "Alice",
        "is_active": True,
    }
