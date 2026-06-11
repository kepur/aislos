from app.models.base_model import Base

from app.models.user import User, Company  # noqa: F401
from app.models.product import Product, ProductCategory, ProductCompatibility  # noqa: F401
from app.models.solution import Solution, SolutionPackage  # noqa: F401
from app.models.lead import Lead, SiteSurvey  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.quote import Quote  # noqa: F401
from app.models.inquiry import Inquiry  # noqa: F401
from app.models.service import ServicePackage, ServicePartner  # noqa: F401
from app.models.ticket import Ticket  # noqa: F401
from app.models.integration import IntegrationEvent, AIRun  # noqa: F401
from app.models.file import FileAsset  # noqa: F401
from app.models.certification import CertificationRecord, WarrantyPolicy  # noqa: F401
from app.models.region import Region  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.legacy_bridge import LegacyBridgeIdempotency, LegacyIdentityMapping  # noqa: F401
from app.models.portal_policy import PortalPolicy  # noqa: F401
from app.models.procurement import (  # noqa: F401
    BoqItem,
    BoqItemOption,
    BoqVersion,
    ProcurementProject,
    ProcurementProjectFact,
    ProcurementTemplate,
    SolutionPlan,
)
from app.models.procurement import (  # noqa: F401
    ProcurementProject,
    ProcurementProjectFact,
    ProcurementTemplate,
)
from app.models.founder import FounderProfile  # noqa: F401
from app.models.proposal import ProposalPlan, BOMItem  # noqa: F401
from app.models.marketing import (  # noqa: F401
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
from app.models.ai import (  # noqa: F401
    KnowledgeDocument,
    DocumentChunk,
    Conversation,
    ConversationMessage,
    AgentRun,
    AIReview,
)
from app.models.channels import ChannelAccount, ChannelThread, ChannelMessage, ChannelDeliveryLog  # noqa: F401
from app.models.ai import AIMemory  # noqa: F401
from app.models.costing import ProductCost, PriceList, ExchangeRate  # noqa: F401
from app.models.rfq import RFQ, RFQInvitation, PartnerBid, PartnerMetric, PartnerMetricSnapshot  # noqa: F401
from app.models.asset import Site, Asset  # noqa: F401
from app.models.case_library import CaseStudy  # noqa: F401
from app.models.payment import PaymentPlan, PaymentMilestone, LedgerEntry, PartnerDeposit  # noqa: F401
from app.models.content import (  # noqa: F401
    SeoPage,
    DocumentTemplate,
    GeneratedDocument,
    PublishJob,
    DesignRevision,
    DocumentSignature,
)
from app.models.agent import Agent, AgentGrant, AgentObjectGrant  # noqa: F401
from app.models.mission import AgentMission, AgentMissionTask  # noqa: F401
from app.models.ecosystem import AgentInstallation, MarketplaceListing, StoreOrder, StoreOrderItem  # noqa: F401

__all__ = ["Base"]
