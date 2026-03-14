from pydantic import BaseModel


# ── Incoming ──────────────────────────────────────────────────────────────────


class CategoryCreate(BaseModel):
    name: str
    # parent_id allows sub-categories, e.g. "Food" → "Groceries", "Restaurants"
    # None means it is a top-level category
    parent_id: int | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None


# ── Outgoing ──────────────────────────────────────────────────────────────────


class CategoryRead(BaseModel):
    id: int
    name: str
    owner_id: int
    parent_id: int | None

    model_config = {"from_attributes": True}
