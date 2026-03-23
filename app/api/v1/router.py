from fastapi import APIRouter

from app.api.v1.endpoints.accounts import router as accounts_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.budgets import router as budgets_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.exports import router as exports_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.transactions import router as transactions_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(accounts_router)
api_router.include_router(transactions_router)
api_router.include_router(categories_router)
api_router.include_router(budgets_router)
api_router.include_router(reports_router)
api_router.include_router(exports_router)
