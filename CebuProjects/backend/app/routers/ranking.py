"""Ranking rules CRUD API for admin configuration of marketplace feed ranking."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.user import User, UserRole
from app.services.ranking_service import SORT_WEIGHTS

require_admin = require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)

router = APIRouter(tags=["ranking"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class WeightProfile(BaseModel):
    category: float = 0.25
    trust: float = 0.20
    distance: float = 0.20
    deal_rate: float = 0.15
    stock: float = 0.10
    verification: float = 0.10
    price: float = 0.0
    ad_boost: float = 0.0


class RankingProfileCreate(BaseModel):
    name: str
    description: str = ""
    weights: WeightProfile
    is_default: bool = False


class RankingProfileUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    weights: WeightProfile | None = None
    is_default: bool | None = None


class RankingProfileResponse(BaseModel):
    id: str
    name: str
    description: str
    weights: dict
    is_default: bool
    total_weight: float


# ── In-memory store (upgrade to DB model if needed) ──────────────────────────
# Using SORT_WEIGHTS from ranking_service as base; admin can override at runtime.

_profiles: list[dict] = [
    {
        "id": "default",
        "name": "Comprehensive (Default)",
        "description": "Balanced multi-dimensional ranking. Used for the 'comprehensive' sort mode.",
        "weights": dict(SORT_WEIGHTS["comprehensive"]),
        "is_default": True,
    },
    {
        "id": "cost",
        "name": "Cost-First",
        "description": "Prioritizes lowest price. Used for 'cost' sort mode.",
        "weights": dict(SORT_WEIGHTS["cost"]),
        "is_default": False,
    },
    {
        "id": "trust",
        "name": "Trust-First",
        "description": "Prioritizes highest trust score. Used for 'trust' sort mode.",
        "weights": dict(SORT_WEIGHTS["trust"]),
        "is_default": False,
    },
    {
        "id": "distance",
        "name": "Nearest First",
        "description": "Prioritizes suppliers closest to the buyer. Used for 'distance' sort mode.",
        "weights": dict(SORT_WEIGHTS["distance"]),
        "is_default": False,
    },
    {
        "id": "delivery",
        "name": "Fastest Delivery",
        "description": "Prioritizes in-stock items from nearby suppliers.",
        "weights": dict(SORT_WEIGHTS["delivery"]),
        "is_default": False,
    },
]


def _to_response(p: dict) -> dict:
    weights = p["weights"]
    total = sum(weights.values())
    return {**p, "total_weight": round(total, 4)}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/ranking/profiles", response_model=list[RankingProfileResponse])
async def list_ranking_profiles(admin: User = Depends(require_admin)):
    """List all ranking weight profiles."""
    return [_to_response(p) for p in _profiles]


@router.get("/ranking/profiles/{profile_id}", response_model=RankingProfileResponse)
async def get_ranking_profile(profile_id: str, admin: User = Depends(require_admin)):
    """Get a single ranking profile by ID."""
    p = next((p for p in _profiles if p["id"] == profile_id), None)
    if not p:
        raise HTTPException(404, "Profile not found")
    return _to_response(p)


@router.post("/ranking/profiles", response_model=RankingProfileResponse, status_code=201)
async def create_ranking_profile(body: RankingProfileCreate, admin: User = Depends(require_admin)):
    """Create a new ranking weight profile."""
    import uuid
    new_id = str(uuid.uuid4())[:8]
    profile = {
        "id": new_id,
        "name": body.name,
        "description": body.description,
        "weights": body.weights.model_dump(),
        "is_default": False,  # new profiles are never default until explicitly set
    }
    _profiles.append(profile)
    return _to_response(profile)


@router.patch("/ranking/profiles/{profile_id}", response_model=RankingProfileResponse)
async def update_ranking_profile(
    profile_id: str,
    body: RankingProfileUpdate,
    admin: User = Depends(require_admin),
):
    """Update a ranking weight profile. Weights must sum to ≤ 1.0."""
    p = next((p for p in _profiles if p["id"] == profile_id), None)
    if not p:
        raise HTTPException(404, "Profile not found")

    if body.name is not None:
        p["name"] = body.name
    if body.description is not None:
        p["description"] = body.description
    if body.weights is not None:
        new_weights = body.weights.model_dump()
        total = sum(new_weights.values())
        if total > 1.05:
            raise HTTPException(400, f"Weights sum to {total:.3f}. Must be ≤ 1.0 (allow 5% tolerance).")
        p["weights"] = new_weights
        # Also update live SORT_WEIGHTS so ranking_service picks it up immediately
        if profile_id in SORT_WEIGHTS:
            SORT_WEIGHTS[profile_id].update({
                "category_match": new_weights["category_match"],
                "trust": new_weights["trust_score"],
                "distance": new_weights["distance"],
                "deal_rate": new_weights["deal_completion_rate"],
                "stock": new_weights["stock"],
                "ad_boost": new_weights["ad_boost"],
            })
    if body.is_default is not None:
        if body.is_default:
            for other in _profiles:
                other["is_default"] = False
        p["is_default"] = body.is_default

    return _to_response(p)


@router.delete("/ranking/profiles/{profile_id}", status_code=204)
async def delete_ranking_profile(profile_id: str, admin: User = Depends(require_admin)):
    """Delete a custom ranking profile (cannot delete built-in profiles)."""
    built_in = {"default", "cost", "trust", "distance", "delivery"}
    if profile_id in built_in:
        raise HTTPException(400, "Cannot delete built-in profiles. Patch weights instead.")
    global _profiles
    before = len(_profiles)
    _profiles = [p for p in _profiles if p["id"] != profile_id]
    if len(_profiles) == before:
        raise HTTPException(404, "Profile not found")


@router.get("/admin/ranking/summary")
async def ranking_summary(admin: User = Depends(require_admin)):
    """Summary of current live ranking weights for all sort modes."""
    return {
        mode: {
            "category_match": w.get("category_match", 0),
            "trust": w.get("trust", 0),
            "distance": w.get("distance", 0),
            "deal_rate": w.get("deal_rate", 0),
            "stock": w.get("stock", 0),
            "ad_boost": w.get("ad_boost", 0),
        }
        for mode, w in SORT_WEIGHTS.items()
    }
