from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import AdminUser, DB
from app.models.finance import ProjectFinance
from app.models.lead import Lead
from app.models.product import Product
from app.models.project import Project
from app.models.ticket import Ticket
from app.models.user import Company
from app.services import lifecycle_alerts

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
async def dashboard_stats(db: DB, admin: AdminUser):
    new_leads = await db.execute(
        select(func.count()).select_from(Lead).where(Lead.status == "new")
    )
    pending_vendors = await db.execute(
        select(func.count()).select_from(Company).where(
            Company.type == "vendor", Company.verification_status == "pending"
        )
    )
    pending_products = await db.execute(
        select(func.count()).select_from(Product).where(Product.status == "pending")
    )
    active_projects = await db.execute(
        select(func.count()).select_from(Project).where(
            Project.status.notin_(["closed"])
        )
    )
    open_tickets = await db.execute(
        select(func.count()).select_from(Ticket).where(
            Ticket.status.notin_(["closed", "resolved"])
        )
    )

    recent_leads_q = await db.execute(
        select(Lead).order_by(Lead.created_at.desc()).limit(5)
    )
    recent_leads = recent_leads_q.scalars().all()

    recent_vendors_q = await db.execute(
        select(Company)
        .where(Company.type == "vendor")
        .order_by(Company.created_at.desc())
        .limit(5)
    )
    recent_vendors = recent_vendors_q.scalars().all()

    return {
        "stats": {
            "new_leads": new_leads.scalar() or 0,
            "pending_vendors": pending_vendors.scalar() or 0,
            "pending_products": pending_products.scalar() or 0,
            "active_projects": active_projects.scalar() or 0,
            "open_tickets": open_tickets.scalar() or 0,
        },
        "recent_leads": [
            {
                "id": str(l.id),
                "contact_name": l.contact_name,
                "project_type": l.project_type,
                "country": l.country,
                "status": l.status,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in recent_leads
        ],
        "recent_vendors": [
            {
                "id": str(v.id),
                "name": v.name,
                "country": v.country,
                "verification_status": v.verification_status,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in recent_vendors
        ],
    }


@router.get("/lifecycle-dashboard")
async def lifecycle_dashboard(db: DB, admin: AdminUser):
    """FI.6.4 — recurring-revenue control tower: ARR, due dates, margin ranking."""
    # Pipeline ARR (from scored leads) and contracted ARR (from project finance).
    arr_pipeline = (await db.execute(
        select(func.coalesce(func.sum(Lead.estimated_arr), 0)).where(
            Lead.status.notin_(["lost", "closed"])
        )
    )).scalar() or 0
    arr_contracted = (await db.execute(
        select(func.coalesce(func.sum(ProjectFinance.annual_recurring_revenue), 0)).where(
            ProjectFinance.project_id.is_not(None)
        )
    )).scalar() or 0
    high_ltv_leads = (await db.execute(
        select(func.count()).select_from(Lead).where(Lead.recurring_revenue_score >= 70)
    )).scalar() or 0
    open_tickets = (await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.status.notin_(["closed", "resolved"]))
    )).scalar() or 0

    summary = await lifecycle_alerts.lifecycle_alert_summary(db)
    alert_counts = {key: block["count"] for key, block in summary.items()}

    # Margin ranking: top project finances by gross margin.
    ranking_q = await db.execute(
        select(ProjectFinance)
        .where(ProjectFinance.project_id.is_not(None))
        .order_by(ProjectFinance.gross_margin_percent.desc().nullslast())
        .limit(10)
    )
    margin_ranking = [
        {
            "id": str(f.id),
            "project_id": str(f.project_id) if f.project_id else None,
            "solution_line": f.solution_line,
            "contract_total": f.contract_total,
            "gross_profit": f.gross_profit,
            "gross_margin_percent": f.gross_margin_percent,
            "ltv_3_year": f.ltv_3_year,
            "ltv_5_year": f.ltv_5_year,
        }
        for f in ranking_q.scalars().all()
    ]

    return {
        "arr": {
            "pipeline": round(float(arr_pipeline), 2),
            "contracted": round(float(arr_contracted), 2),
        },
        "high_ltv_leads": high_ltv_leads,
        "open_tickets": open_tickets,
        "alerts": alert_counts,
        "margin_ranking": margin_ranking,
    }
