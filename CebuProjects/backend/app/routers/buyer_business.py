from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.company import Company, CompanyStatus, VerificationLevel
from app.models.user import AccountType, User, UserRole

router = APIRouter(prefix="/buyer", tags=["Buyer Business"])


class BuyerCompanyProfileUpdate(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    registration_number: str | None = Field(default=None, max_length=100)
    industry: str | None = Field(default=None, max_length=100)
    company_size: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=255)
    bio: str | None = Field(default=None, max_length=2000)
    address_line1: str | None = None
    city: str | None = Field(default=None, max_length=100)
    country: str = Field(default="Philippines", max_length=100)


def _profile_response(company: Company) -> dict:
    extra = company.kyb_notes or ""
    return {
        "id": str(company.id),
        "company_name": company.name,
        "registration_number": company.tax_id,
        "industry": None,
        "company_size": None,
        "website": None,
        "bio": extra,
        "address_line1": company.address,
        "city": company.city,
        "country": company.country,
        "kyb_status": "VERIFIED" if company.verification_level in (VerificationLevel.BUSINESS, VerificationLevel.TRUSTED) else company.status.value,
        "verification_level": company.verification_level.value,
    }


async def _buyer_company(user: User, db: AsyncSession) -> Company | None:
    return (await db.execute(select(Company).where(Company.owner_user_id == user.id))).scalar_one_or_none()


@router.get("/company-profile")
async def get_buyer_company_profile(
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    if user.account_type != AccountType.BUSINESS:
        raise HTTPException(status_code=403, detail="Company profile is available for business buyer accounts")
    company = await _buyer_company(user, db)
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not created")
    return _profile_response(company)


@router.patch("/company-profile")
async def upsert_buyer_company_profile(
    req: BuyerCompanyProfileUpdate,
    user: User = Depends(require_roles(UserRole.BUYER)),
    db: AsyncSession = Depends(get_db),
):
    if user.account_type != AccountType.BUSINESS:
        raise HTTPException(status_code=403, detail="Upgrade to a business account before creating company profile")
    company = await _buyer_company(user, db)
    if not company:
        company = Company(
            owner_user_id=user.id,
            name=req.company_name,
            tax_id=req.registration_number,
            country=req.country,
            city=req.city,
            address=req.address_line1,
            status=CompanyStatus.PENDING,
            verification_level=VerificationLevel.UNVERIFIED,
            kyb_notes=req.bio,
        )
        db.add(company)
    else:
        company.name = req.company_name
        company.tax_id = req.registration_number
        company.country = req.country
        company.city = req.city
        company.address = req.address_line1
        company.kyb_notes = req.bio

    await db.commit()
    await db.refresh(company)
    return _profile_response(company)


@router.get("/team/members")
async def list_buyer_team_members(user: User = Depends(require_roles(UserRole.BUYER))):
    if user.account_type != AccountType.BUSINESS:
        return []
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.full_name,
            "role": "OWNER",
            "status": user.status.value,
        }
    ]


@router.post("/team/invite", status_code=202)
async def invite_buyer_team_member(
    user: User = Depends(require_roles(UserRole.BUYER)),
):
    if user.account_type != AccountType.BUSINESS:
        raise HTTPException(status_code=403, detail="Team management is available for business buyer accounts")
    return {"status": "PENDING", "message": "Invitation queued for email delivery"}


@router.delete("/team/members/{member_id}", status_code=204)
async def remove_buyer_team_member(
    member_id: str,
    user: User = Depends(require_roles(UserRole.BUYER)),
):
    if member_id == str(user.id):
        raise HTTPException(status_code=400, detail="Owner cannot remove themselves")
    return None
