from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.company import Branch, Company, CompanyStatus
from app.models.company_document import CompanyDocument
from app.models.user import User, UserRole
from app.models.verification_review import VerificationQueueStatus, VerificationReview
from app.schemas.company import (
    BranchCreate,
    BranchResponse,
    BranchUpdate,
    CompanyDocumentCreate,
    CompanyDocumentResponse,
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
    VerificationSubmitResponse,
)

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    req: CompanyCreate,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already have a company")

    company = Company(owner_user_id=user.id, **req.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


@router.get("/me", response_model=CompanyResponse)
async def get_my_company(
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    return company


@router.patch("/me", response_model=CompanyResponse)
async def update_my_company(
    req: CompanyUpdate,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    await db.commit()
    await db.refresh(company)
    return company


@router.post("/me/branches", response_model=BranchResponse, status_code=201)
async def create_branch(
    req: BranchCreate,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")

    branch = Branch(company_id=company.id, **req.model_dump())
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return branch


@router.get("/me/branches", response_model=list[BranchResponse])
async def list_branches(
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    result = await db.execute(select(Branch).where(Branch.company_id == company.id))
    return result.scalars().all()


@router.patch("/me/branches/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: str,
    req: BranchUpdate,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")

    result = await db.execute(select(Branch).where(Branch.id == branch_id, Branch.company_id == company.id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(branch, field, value)
    await db.commit()
    await db.refresh(branch)
    return branch


@router.get("/me/documents", response_model=list[CompanyDocumentResponse])
async def list_my_company_documents(
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN, UserRole.SUPPLIER_AGENT)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    docs = await db.execute(select(CompanyDocument).where(CompanyDocument.company_id == company.id).order_by(CompanyDocument.created_at.desc()))
    return docs.scalars().all()


@router.post("/me/documents", response_model=CompanyDocumentResponse, status_code=201)
async def create_my_company_document(
    req: CompanyDocumentCreate,
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    doc = CompanyDocument(company_id=company.id, **req.model_dump())
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.post("/me/verification/submit", response_model=VerificationSubmitResponse, status_code=201)
async def submit_my_company_verification(
    user: User = Depends(require_roles(UserRole.SUPPLIER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.owner_user_id == user.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="No company found")
    doc_count = (await db.execute(select(CompanyDocument).where(CompanyDocument.company_id == company.id))).scalars().all()
    if not doc_count:
        raise HTTPException(status_code=400, detail="Upload at least one KYB document before submitting")

    existing = await db.execute(select(VerificationReview).where(VerificationReview.company_id == company.id))
    review = existing.scalar_one_or_none()
    if review:
        review.status = VerificationQueueStatus.SUBMITTED
    else:
        review = VerificationReview(company_id=company.id, status=VerificationQueueStatus.SUBMITTED)
        db.add(review)
    company.status = CompanyStatus.PENDING
    await db.commit()
    await db.refresh(review)
    return review
