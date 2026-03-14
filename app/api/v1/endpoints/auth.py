from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
async def register():
    return {"message": "register endpoint hit ✓", "method": "POST", "path": "/auth/register"}


@router.post("/login")
async def login():
    return {"message": "login endpoint hit ✓", "method": "POST", "path": "/auth/login"}


@router.get("/me")
async def me():
    return {"message": "me endpoint hit ✓", "method": "GET", "path": "/auth/me"}

