from app.models.base_model import Base
from app.models.user import User, Company
from app.models.product import Product, ProductCategory, ProductCompatibility
from app.models.solution import Solution, SolutionPackage
from app.models.lead import Lead, SiteSurvey
from app.models.project import Project
from app.models.quote import Quote
from app.models.inquiry import Inquiry
from app.models.service import ServicePackage, ServicePartner, PartnerCapability
from app.models.ticket import Ticket
from app.models.integration import IntegrationEvent, AIRun
from app.models.file import FileAsset
from app.models.certification import CertificationRecord, WarrantyPolicy
from app.models.region import Region
from app.models.audit import AuditLog
from app.models.portal_policy import PortalPolicy
from app.models.procurement import (
    BoqItem,
    BoqItemOption,
    BoqVersion,
    CommercialSnapshot,
    ProcurementPackage,
    ProcurementPackageItem,
    ProcurementProject,
    ProcurementProjectFact,
    ProcurementTemplate,
    SolutionPlan,
)
from app.models.founder import FounderProfile
from app.models.lifecycle import (
    SupplierWarranty,
    CustomerWarranty,
    AMCContract,
    MonitoringPoint,
    InventoryItem,
    StockMovement,
    MaintenanceSchedule,
    CalibrationRecord,
)
from app.models.finance import ProjectFinance, PlatformFeeRule
from app.models.crm import SupplierScorecard
from app.models.notification import NotificationPreference, ReportJob
from app.models.settings import IntegrationSetting
from app.models.marketing import (
    MarketingActivity,
    MarketingAsset,
    MarketingCampaign,
    MarketingContact,
    MarketingCreativeBrief,
    MarketingCreativeBriefVersion,
    MarketingIntegrationClient,
    MarketingIntegrationIdempotency,
    MarketingMediaRequest,
    MarketingMediaUpload,
    RegionMarketingProfile,
)
from app.models.ai import (
    KnowledgeDocument,
    DocumentChunk,
    Conversation,
    ConversationMessage,
    AgentRun,
    AIReview,
)
from app.models.channels import ChannelAccount, ChannelThread, ChannelMessage, ChannelDeliveryLog
from app.models.ai import AIMemory
from app.models.costing import ProductCost, PriceList, ExchangeRate
from app.models.rfq import RFQ, RFQInvitation, PartnerBid, PartnerMetric, PartnerMetricSnapshot
from app.models.asset import Site, Asset
from app.models.case_library import CaseStudy
from app.models.payment import PaymentPlan, PaymentMilestone, LedgerEntry, PartnerDeposit
from app.models.content import (
    SeoPage,
    DocumentTemplate,
    GeneratedDocument,
    PublishJob,
    DesignRevision,
    DocumentSignature,
)
from app.models.agent import Agent, AgentGrant
from app.models.ecosystem import AgentInstallation, MarketplaceListing, StoreOrder, StoreOrderItem
from app.models.showroom import Store, KioskDevice, ShowroomSession, ShowroomOrder

__all__ = [
    "Base",
    "User", "Company",
    "Product", "ProductCategory", "ProductCompatibility",
    "Solution", "SolutionPackage",
    "Lead", "SiteSurvey",
    "Project",
    "Quote",
    "Inquiry",
    "ServicePackage", "ServicePartner",
    "Ticket",
    "IntegrationEvent", "AIRun",
    "FileAsset",
    "CertificationRecord", "WarrantyPolicy",
    "Region",
    "AuditLog",
    "PortalPolicy",
    "ProcurementProject", "ProcurementProjectFact", "ProcurementTemplate",
    "BoqVersion", "BoqItem", "BoqItemOption", "SolutionPlan",
    "FounderProfile",
    "SupplierWarranty", "CustomerWarranty", "AMCContract",
    "MonitoringPoint",
    "InventoryItem", "StockMovement",
    "MaintenanceSchedule", "CalibrationRecord",
    "ProjectFinance", "PlatformFeeRule",
    "SupplierScorecard",
    "NotificationPreference", "ReportJob",
    "IntegrationSetting",
    "MarketingActivity", "MarketingAsset", "MarketingCampaign", "MarketingContact",
    "MarketingCreativeBrief", "MarketingCreativeBriefVersion",
    "MarketingIntegrationClient", "MarketingIntegrationIdempotency",
    "MarketingMediaRequest", "MarketingMediaUpload",
    "KnowledgeDocument", "DocumentChunk",
    "Conversation", "ConversationMessage", "AgentRun", "AIReview", "AIMemory",
    "ChannelAccount", "ChannelThread", "ChannelMessage", "ChannelDeliveryLog",
    "ProductCost", "PriceList", "ExchangeRate",
    "RFQ", "RFQInvitation", "PartnerBid", "PartnerMetric", "PartnerMetricSnapshot",
    "Site", "Asset", "CaseStudy",
    "PaymentPlan", "PaymentMilestone", "LedgerEntry", "PartnerDeposit",
    "RegionMarketingProfile",
    "SeoPage", "DocumentTemplate", "GeneratedDocument", "PublishJob", "DesignRevision",
    "DocumentSignature",
    "Agent", "AgentGrant",
    "AgentInstallation", "MarketplaceListing", "StoreOrder", "StoreOrderItem",
    "Store", "KioskDevice", "ShowroomSession", "ShowroomOrder",
]
