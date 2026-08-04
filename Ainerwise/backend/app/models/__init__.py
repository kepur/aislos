from app.models.base_model import Base
from app.models.user import User, Company, PasswordResetToken
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
from app.models.backup import BackupJob, BackupSchedule
from app.models.admin_config import AdminNote, NotificationTemplate, PlatformSetting
from app.models.commerce_geo import CompanyBranch, ServiceArea
from app.models.legacy_bridge import LegacyBridgeIdempotency, LegacyIdentityMapping
from app.models.legacy_migration import LegacyMigrationRecord, LegacyMigrationRun
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
from app.models.notification import NotificationPreference, PortalNotification, ReportJob
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
from app.models.portal_access import Workspace, WorkspaceMembership, PortalGrant
from app.models.privacy import PrivacyRequest
from app.models.commerce import (
    BuyerWatchlistItem,
    CommerceOrder,
    CommercePaymentIntent,
    CommerceReconciliationRun,
    CommerceSettlement,
    CommerceThread,
    CommerceMessage,
    OrderDelivery,
    OrderDispute,
    ProcurementRequest,
    RiskFlag,
    SupplierListing,
    SupplierOffer,
    TradeCategorySchema,
    TransactionReview,
    TrustProfile,
    TrustScoreEvent,
)
from app.models.secondhand import (
    SecondhandAddressDisclosure,
    SecondhandDeal,
    SecondhandListing,
)
from app.models.syndication import (
    ChannelCategoryMap,
    ChannelListing,
)
from app.models.analytics import (
    AnalyticsEvent,
    AnalyticsProjectionCursor,
    Creative,
)
from app.models.field_service import (
    PartnerCrew,
    CrewMembership,
    WorkPackage,
    FieldTask,
    TaskAssignment,
    TaskEvidence,
)
from app.modules.buyer_project.models import (
    ProjectMetricTemplate,
    ProjectMetricValue,
    ProjectPriceSnapshot,
    ProjectReport,
    ProjectReportVersion,
    ProjectReportColumn,
    ProjectReportRow,
    ProjectReportChangeLog,
)
from app.modules.cebu_trade.models import (
    CurrencyConfig,
    FeeLineItem,
    FeeRule,
    FxQuote,
    PaymentEvent,
    PaymentMethodConfig,
    PaymentQuote,
    ProviderPaymentIntent,
    RegionPaymentConfig,
    SettlementAdjustment,
    SettlementEvent,
)

# Cebu trade models live under app.modules.cebu_trade.models and are registered
# in app.db.base to avoid circular imports (they depend on base_model which
# lives inside app.models).  Import them from their own module directly.

__all__ = [
    "Base",
    "User", "Company", "PasswordResetToken",
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
    "BackupJob", "BackupSchedule",
    "AdminNote", "NotificationTemplate", "PlatformSetting",
    "CompanyBranch", "ServiceArea",
    "LegacyBridgeIdempotency", "LegacyIdentityMapping",
    "LegacyMigrationRecord", "LegacyMigrationRun",
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
    "NotificationPreference", "PortalNotification", "ReportJob",
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
    "Workspace", "WorkspaceMembership", "PortalGrant", "PrivacyRequest",
    "PartnerCrew", "CrewMembership", "WorkPackage", "FieldTask", "TaskAssignment", "TaskEvidence",
    "ProjectMetricTemplate", "ProjectMetricValue", "ProjectPriceSnapshot",
    "ProjectReport", "ProjectReportVersion", "ProjectReportColumn",
    "ProjectReportRow", "ProjectReportChangeLog",
    "RegionPaymentConfig", "CurrencyConfig", "PaymentMethodConfig", "FeeRule",
    "FxQuote", "PaymentQuote", "ProviderPaymentIntent", "FeeLineItem",
    "SettlementEvent", "SettlementAdjustment", "PaymentEvent",
    "TradeCategorySchema", "SupplierListing", "BuyerWatchlistItem", "ProcurementRequest", "SupplierOffer", "CommerceOrder",
    "OrderDelivery", "OrderDispute",
    "TrustProfile", "TrustScoreEvent", "TransactionReview", "RiskFlag", "CommercePaymentIntent",
    "CommerceThread", "CommerceMessage",
    "CommerceSettlement", "CommerceReconciliationRun",
    "SecondhandListing", "SecondhandAddressDisclosure", "SecondhandDeal",
    "ChannelListing", "ChannelCategoryMap",
    "AnalyticsEvent", "Creative", "AnalyticsProjectionCursor",
]
