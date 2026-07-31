"""Customer projection schemas must exclude internal operating fields."""
from app.schemas import lifecycle as ls
from app.schemas.inquiry import InquiryCustomerRead
from app.schemas.lead import LeadCustomerRead
from app.schemas.project import ProjectCustomerRead
from app.schemas.ticket import TicketCustomerRead


def test_customer_projection_schemas_exclude_internal_fields():
    boundaries = {
        LeadCustomerRead: {"notes", "assigned_admin_id", "lead_score", "estimated_ltv"},
        InquiryCustomerRead: {"admin_notes", "vendor_company_id", "buyer_user_id"},
        ProjectCustomerRead: {"notes", "telegram_chat_id", "buyer_company_id"},
        TicketCustomerRead: {"assigned_to", "buyer_user_id", "buyer_company_id"},
        ls.AMCContractCustomerRead: {"customer_id", "pricing_mode", "notes"},
        ls.CustomerWarrantyCustomerRead: {"customer_id", "notes"},
        ls.MonitoringPointCustomerRead: {"notes"},
        ls.MaintenanceScheduleCustomerRead: {"assigned_to", "cost", "notes"},
        ls.CalibrationRecordCustomerRead: {"notes"},
    }
    for schema, forbidden in boundaries.items():
        assert forbidden.isdisjoint(schema.model_fields), schema.__name__
