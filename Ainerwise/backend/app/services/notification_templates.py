"""Telegram admin notification templates (FI.8.1, FI.8.2).

Registry of event_type -> message formatter. Lifecycle events include the
solution line, monitoring points, compliance needs, ARR range, due date, and a
recommended action so the admin can act straight from the alert.
"""
from __future__ import annotations

from typing import Any, Callable

PRELIMINARY = "Preliminary recommendation. Final solution requires engineering review and site verification."

# FI.8.1 — lifecycle event types created across the platform.
LIFECYCLE_EVENT_TYPES = (
    "lead.high_recurring",
    "lead.compliance_cashflow",
    "payment.due",
    "amc.renewal_due",
    "warranty.expiry",
    "calibration.due",
    "probe.replacement",
    "ticket.opened",
    "supplier.claim",
)


def _g(p: dict, key: str, default: str = "-") -> Any:
    v = p.get(key)
    return v if v not in (None, "") else default


def _lead_created(p: dict) -> str:
    return (
        "New lead received\n"
        f"Contact: {_g(p, 'contact_name', _g(p, 'contact_email'))}\n"
        f"Project: {_g(p, 'project_type')}\n"
        f"Location: {_g(p, 'country')} {p.get('city') or ''}\n"
        f"Budget: {_g(p, 'budget_range')}\n"
        f"Lead ID: {p.get('lead_id')}"
    )


def _vendor_applied(p: dict) -> str:
    return (
        "New supplier/partner application\n"
        f"Company: {_g(p, 'company_name')}\n"
        f"Location: {_g(p, 'country')} {p.get('city') or ''}\n"
        f"Email: {_g(p, 'email')}\n"
        f"Vendor ID: {p.get('vendor_id')}"
    )


def _product_submitted(p: dict) -> str:
    return (
        "Product submitted for review\n"
        f"Product: {_g(p, 'name')}\n"
        f"Brand: {_g(p, 'brand')}\n"
        f"Status: {_g(p, 'status')}\n"
        f"Product ID: {p.get('product_id')}"
    )


def _ai_completed(p: dict) -> str:
    return (
        "AI lead analysis completed\n"
        f"Lead ID: {p.get('lead_id')}\n"
        f"Classification: {_g(p, 'classification')}\n"
        f"Completeness: {p.get('completeness_score')}%\n"
        f"{PRELIMINARY}"
    )


def _arr_line(p: dict) -> str:
    lo, hi = p.get("arr_min"), p.get("arr_max")
    if lo or hi:
        return f"Estimated ARR: EUR {lo or '?'} - {hi or '?'}\n"
    if p.get("estimated_arr"):
        return f"Estimated ARR: EUR {p.get('estimated_arr')}\n"
    return ""


def _lead_recurring(title: str) -> Callable[[dict], str]:
    def fmt(p: dict) -> str:
        return (
            f"[AinerWise] {title}\n"
            f"Solution: {_g(p, 'solution_line')}\n"
            f"Client type: {_g(p, 'project_type')}\n"
            f"Region: {_g(p, 'country')}\n"
            f"Monitoring points: {_g(p, 'monitoring_points')}\n"
            f"Compliance risk: {_g(p, 'compliance_risk')}\n"
            f"Recurring score: {_g(p, 'recurring_revenue_score')}\n"
            f"{_arr_line(p)}"
            f"Recommended action: {_g(p, 'recommended_action', 'Offer a multi-year AMC')}\n"
            f"Lead ID: {p.get('lead_id')}"
        )
    return fmt


def _due(title: str, action: str) -> Callable[[dict], str]:
    def fmt(p: dict) -> str:
        return (
            f"[AinerWise] {title}\n"
            f"Solution: {_g(p, 'solution_line')}\n"
            f"Project: {_g(p, 'project_title', p.get('project_id', '-'))}\n"
            f"Item: {_g(p, 'item')}\n"
            f"Due: {_g(p, 'due_date')}\n"
            f"Recommended action: {_g(p, 'recommended_action', action)}"
        )
    return fmt


def _ticket_opened(p: dict) -> str:
    return (
        "[AinerWise] Ticket opened\n"
        f"Title: {_g(p, 'title')}\n"
        f"Type: {_g(p, 'issue_type')}\n"
        f"Device: {_g(p, 'affected_device')}\n"
        f"Coverage: {_g(p, 'coverage_type', 'to be evaluated')}\n"
        f"Ticket ID: {p.get('ticket_id')}"
    )


def _supplier_claim(p: dict) -> str:
    return (
        "[AinerWise] Supplier warranty claim needed\n"
        f"Device: {_g(p, 'device')}\n"
        f"Supplier: {_g(p, 'supplier')}\n"
        f"Reason: {_g(p, 'reason')}\n"
        f"Ticket ID: {p.get('ticket_id')}"
    )


def _payment_due(p: dict) -> str:
    return (
        "[AinerWise] Payment due\n"
        f"Project: {_g(p, 'project_title', p.get('project_id', '-'))}\n"
        f"Amount: {_g(p, 'amount')} {_g(p, 'currency', 'EUR')}\n"
        f"Due: {_g(p, 'due_date')}"
    )


_TEMPLATES: dict[str, Callable[[dict], str]] = {
    "lead.created": _lead_created,
    "vendor.applied": _vendor_applied,
    "product.submitted": _product_submitted,
    "ai.completed": _ai_completed,
    "lead.high_recurring": _lead_recurring("High Recurring Revenue Lead"),
    "lead.compliance_cashflow": _lead_recurring("Compliance Cashflow Lead"),
    "payment.due": _payment_due,
    "amc.renewal_due": _due("AMC Renewal Due", "Offer AMC renewal before expiry"),
    "warranty.expiry": _due("Warranty Expiring", "Confirm renewal or managed warranty"),
    "calibration.due": _due("Calibration Due", "Schedule calibration + certificate"),
    "probe.replacement": _due("Probe Replacement Opportunity", "Quote probe replacement"),
    "ticket.opened": _ticket_opened,
    "supplier.claim": _supplier_claim,
    "briefing.daily": lambda p: f"🧠 AinerWise Business Brain\n\n{p.get('text') or 'No briefing text.'}",
}


def render_telegram(event_type: str, payload: dict) -> str:
    fmt = _TEMPLATES.get(event_type)
    if fmt:
        return fmt(payload or {})
    return f"{event_type}\n{payload}"
