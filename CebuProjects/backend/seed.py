"""Idempotent seed script — safe to run multiple times."""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.catalog import CatalogItem, CatalogItemStatus
from app.models.category import Category, CategoryStatus
from app.models.company import Branch, Company, CompanyStatus, VerificationLevel
from app.models.notification_template import NotificationTemplate
from app.models.platform_setting import PlatformSetting
from app.models.user import User, UserRole, UserStatus

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

SEED_USERS = [
    {"email": "admin@procureping.local",    "password": "Admin1234!",    "full_name": "Platform Admin",   "role": UserRole.ADMIN},
    {"email": "superadmin@procureping.local","password": "SuperAdmin1234!", "full_name": "Super Admin",  "role": UserRole.SUPER_ADMIN},
    {"email": "buyer@procureping.local",    "password": "Buyer1234!",    "full_name": "Test Buyer",       "role": UserRole.BUYER},
    {"email": "supplier@procureping.local", "password": "Supplier1234!", "full_name": "Test Supplier",    "role": UserRole.SUPPLIER_ADMIN},
    # Demo accounts — simple password for demo mode
    {"email": "buyer@demo.procureping",     "password": "123",           "full_name": "Demo Buyer",       "role": UserRole.BUYER},
    {"email": "supplier@demo.procureping",  "password": "123",           "full_name": "Demo Supplier",    "role": UserRole.SUPPLIER_ADMIN},
    {"email": "admin@procureping.com",      "password": "admin123",      "full_name": "Admin Console",    "role": UserRole.SUPER_ADMIN},
]

DEFAULT_SETTINGS = [
    {"key": "APP_NAME",            "value": "ProcurePing",          "description": "Platform display name"},
    {"key": "APP_DOMAIN",          "value": "procureping.local",    "description": "Platform domain"},
    {"key": "DEFAULT_CURRENCY",    "value": "PHP",                  "description": "Default currency code"},
    {"key": "DEFAULT_LANGUAGE",    "value": "en",                   "description": "Default language code"},
    {"key": "DEFAULT_COUNTRY",     "value": "PH",                   "description": "Default country code"},
    {"key": "ESCROW_PROVIDER",     "value": "SIMULATED",            "description": "Active escrow provider"},
    {"key": "DISPUTE_SLA_HOURS",   "value": "72",                   "description": "Hours to resolve a dispute"},
    {"key": "SUPPLIER_RESPONSE_SLA_HOURS", "value": "24",           "description": "Hours for supplier to respond"},
    {"key": "MAX_OFFERS_PER_INTENT","value": "20",                  "description": "Max offers allowed per intent"},
    {"key": "MAINTENANCE_MODE",    "value": "false",                "description": "Put platform in maintenance mode"},
    # Demo & registration mode
    {"key": "DEMO_MODE",           "value": "true",                 "description": "Show demo banner and allow demo logins. Set false in production."},
    {"key": "REGISTRATION_ENABLED","value": "true",                 "description": "Allow new user self-registration. Set false when email service is not configured and you want invite-only."},
    {"key": "EMAIL_VERIFICATION_REQUIRED", "value": "false",        "description": "Require email verification on registration (needs SMTP config)."},
    {"key": "INTENT_MAX_ATTACHMENTS", "value": "10",                "description": "Maximum number of images allowed when creating a buyer request."},
]

DEFAULT_NOTIFICATION_TEMPLATES = [
    {"template_key": "NEW_INTENT_FOR_SUPPLIER", "channel": "IN_APP",  "subject": "New Purchase Request", "body": "A buyer posted a new request: {{intent_title}}. Log in to submit your offer."},
    {"template_key": "NEW_OFFER_FOR_BUYER",     "channel": "IN_APP",  "subject": "New Offer Received",   "body": "You received a new offer for: {{intent_title}}."},
    {"template_key": "OFFER_AWARDED_SUPPLIER",  "channel": "IN_APP",  "subject": "Your Offer Was Awarded","body": "Congratulations! Your offer for {{intent_title}} was awarded. Order ID: {{order_id}}."},
    {"template_key": "ORDER_CREATED_BUYER",     "channel": "IN_APP",  "subject": "Order Created",        "body": "Your order {{order_id}} has been created. Escrow is active."},
    {"template_key": "DELIVERY_UPDATED_BUYER",  "channel": "IN_APP",  "subject": "Delivery Update",      "body": "Delivery status for order {{order_id}}: {{delivery_status}}."},
    {"template_key": "ORDER_ACCEPTED_SUPPLIER", "channel": "IN_APP",  "subject": "Order Accepted",       "body": "Buyer accepted delivery for order {{order_id}}. Payout is being processed."},
    {"template_key": "DISPUTE_OPENED_ADMIN",    "channel": "IN_APP",  "subject": "Dispute Opened",       "body": "A dispute was opened for order {{order_id}}. Please review."},
    {"template_key": "DISPUTE_UPDATED_PARTIES", "channel": "IN_APP",  "subject": "Dispute Update",       "body": "Dispute for order {{order_id}} has been updated: {{dispute_status}}."},
    {"template_key": "NEW_INTENT_FOR_SUPPLIER", "channel": "EMAIL",   "subject": "New Purchase Request — {{intent_title}}", "body": "Dear Supplier,\n\nA buyer has posted a new purchase request that matches your catalog.\n\nTitle: {{intent_title}}\nCategory: {{category}}\nLocation: {{location}}\n\nLog in to submit your offer."},
    {"template_key": "OFFER_AWARDED_SUPPLIER",  "channel": "EMAIL",   "subject": "Offer Awarded — Order {{order_id}}", "body": "Your offer for {{intent_title}} has been awarded.\n\nOrder ID: {{order_id}}\nAmount: {{amount}} {{currency}}\n\nPlease proceed with fulfillment."},
    {"template_key": "DISPUTE_OPENED_ADMIN",    "channel": "EMAIL",   "subject": "Dispute Opened — Order {{order_id}}", "body": "A dispute has been opened for order {{order_id}}.\n\nReason: {{dispute_reason}}\n\nPlease review in the admin console."},
    {"template_key": "NEW_INTENT_FOR_SUPPLIER", "channel": "TELEGRAM","subject": None, "body": "📦 New Request: {{intent_title}}\nCategory: {{category}} | Location: {{location}}\nLog in to submit your offer."},
    {"template_key": "OFFER_AWARDED_SUPPLIER",  "channel": "TELEGRAM","subject": None, "body": "🎉 Offer Awarded!\nOrder ID: {{order_id}}\nAmount: {{amount}} {{currency}}\nProceed with fulfillment."},
]

BASE_CATEGORY_SCHEMA = {
    "required": ["brand"],
    "fields": [
        {"key": "brand", "type": "string", "label": "Brand"},
        {"key": "model", "type": "string", "label": "Model"},
        {"key": "condition", "type": "enum", "options": ["new", "used", "refurbished"]},
    ],
}

CATEGORIES = [
    {"name": "Construction Materials", "name_zh": "建筑材料", "slug": "construction-materials", "level": 1, "sort_order": 10, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "IT & Office Equipment", "name_zh": "IT与办公设备", "slug": "it-office-equipment", "level": 1, "sort_order": 20, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Automotive Parts", "name_zh": "汽车零配件", "slug": "automotive-parts", "level": 1, "sort_order": 30, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Electronics & Components", "name_zh": "电子电气元器件", "slug": "electronics-components", "level": 1, "sort_order": 40, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Machinery & Industrial", "name_zh": "机械与工业设备", "slug": "machinery-industrial", "level": 1, "sort_order": 50, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Raw Materials & Chemicals", "name_zh": "原材料与化工", "slug": "raw-materials-chemicals", "level": 1, "sort_order": 60, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Textiles & Garments", "name_zh": "纺织与服装", "slug": "textiles-garments", "level": 1, "sort_order": 70, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Food & Beverages", "name_zh": "食品饮料", "slug": "food-beverages", "level": 1, "sort_order": 80, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Agriculture & Farming", "name_zh": "农业与农资", "slug": "agriculture-farming", "level": 1, "sort_order": 90, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Medical & Healthcare", "name_zh": "医疗健康", "slug": "medical-healthcare", "level": 1, "sort_order": 100, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Packaging & Printing", "name_zh": "包装印刷", "slug": "packaging-printing", "level": 1, "sort_order": 110, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Furniture & Home", "name_zh": "家具家居", "slug": "furniture-home", "level": 1, "sort_order": 120, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Lighting & Electrical", "name_zh": "照明电气", "slug": "lighting-electrical", "level": 1, "sort_order": 130, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Plumbing & HVAC", "name_zh": "管道暖通", "slug": "plumbing-hvac", "level": 1, "sort_order": 140, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Safety & Security", "name_zh": "安防消防", "slug": "safety-security", "level": 1, "sort_order": 150, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Sports & Outdoor", "name_zh": "运动户外", "slug": "sports-outdoor", "level": 1, "sort_order": 160, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Beauty & Personal Care", "name_zh": "美妆个护", "slug": "beauty-personal-care", "level": 1, "sort_order": 170, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Toys & Baby Products", "name_zh": "玩具母婴", "slug": "toys-baby-products", "level": 1, "sort_order": 180, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Pet Supplies", "name_zh": "宠物用品", "slug": "pet-supplies", "level": 1, "sort_order": 190, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Jewelry & Accessories", "name_zh": "珠宝饰品", "slug": "jewelry-accessories", "level": 1, "sort_order": 200, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Marine & Shipping", "name_zh": "船舶航海", "slug": "marine-shipping", "level": 1, "sort_order": 210, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Energy & Solar", "name_zh": "能源与太阳能", "slug": "energy-solar", "level": 1, "sort_order": 220, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Mining & Minerals", "name_zh": "矿业矿产", "slug": "mining-minerals", "level": 1, "sort_order": 230, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Telecom & Networking", "name_zh": "通信与网络", "slug": "telecom-networking", "level": 1, "sort_order": 240, "schema_json": BASE_CATEGORY_SCHEMA},
    {"name": "Tools & Hardware", "name_zh": "工具五金", "slug": "tools-hardware", "level": 1, "sort_order": 250, "schema_json": BASE_CATEGORY_SCHEMA},
]


async def seed():
    async with SessionLocal() as db:
        # ── Users ──────────────────────────────────────────────────
        users: dict[str, User] = {}
        for u in SEED_USERS:
            result = await db.execute(select(User).where(User.email == u["email"]))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    status=UserStatus.ACTIVE,
                )
                db.add(user)
                await db.flush()
                print(f"  Created user: {u['email']}")
            else:
                user.password_hash = hash_password(u["password"])
                user.full_name = u["full_name"]
                user.status = UserStatus.ACTIVE
                print(f"  Updated user: {u['email']}")
            users[u["email"]] = user

        async def seed_supplier_company(supplier_user: User, company_name: str) -> tuple[Company, Branch]:
            result = await db.execute(select(Company).where(Company.owner_user_id == supplier_user.id))
            company = result.scalar_one_or_none()
            if not company:
                company = Company(
                    owner_user_id=supplier_user.id,
                    name=company_name,
                    country="PH",
                    city="Cebu City",
                    address="123 Commerce St, Cebu City",
                    verification_level=VerificationLevel.BUSINESS,
                    status=CompanyStatus.ACTIVE,
                )
                db.add(company)
                await db.flush()
                print(f"  Created company: {company_name}")
            else:
                print(f"  Exists company: {company_name}")

            result = await db.execute(select(Branch).where(Branch.company_id == company.id))
            branch = result.scalar_one_or_none()
            if not branch:
                branch = Branch(
                    company_id=company.id,
                    name="Main Cebu Warehouse",
                    country="PH",
                    city="Cebu City",
                    address="123 Commerce St, Cebu City",
                    lat=10.3157,
                    lng=123.8854,
                    radius_km=50,
                    delivery_methods=["truck", "pickup"],
                )
                db.add(branch)
                await db.flush()
                print("  Created branch: Main Cebu Warehouse")
            return company, branch

        company, branch = await seed_supplier_company(
            users["supplier@procureping.local"],
            "Cebu Building Supply Co.",
        )
        await seed_supplier_company(
            users["supplier@demo.procureping"],
            "Demo Cebu Building Supply Co.",
        )

        # ── Categories ─────────────────────────────────────────────
        cat_by_slug: dict[str, Category] = {}
        for c in CATEGORIES:
            result = await db.execute(select(Category).where(Category.slug == c["slug"]))
            cat = result.scalar_one_or_none()
            if not cat:
                cat = Category(**c, status=CategoryStatus.ACTIVE)
                db.add(cat)
                await db.flush()
                print(f"  Created category: {c['name']}")
            else:
                # Keep seed idempotent while backfilling newly added fields.
                cat.name = c["name"]
                cat.name_zh = c.get("name_zh")
                cat.level = c.get("level", cat.level or 1)
                cat.sort_order = c.get("sort_order", cat.sort_order or 0)
                cat.schema_json = c.get("schema_json") or cat.schema_json
                cat.status = CategoryStatus.ACTIVE
            cat_by_slug[c["slug"]] = cat

        construction_cat = cat_by_slug["construction-materials"]
        it_cat = cat_by_slug["it-office-equipment"]

        # ── Catalog items ──────────────────────────────────────────
        result = await db.execute(select(CatalogItem).where(CatalogItem.company_id == company.id))
        existing_items = result.scalars().all()
        if not existing_items:
            db.add(CatalogItem(
                company_id=company.id,
                branch_id=branch.id,
                category_id=construction_cat.id,
                title="Holcim Portland Cement 40kg",
                description="Factory-fresh Holcim Portland cement, 40kg per bag.",
                attrs_jsonb={"brand": "Holcim", "type": "Portland", "bag_weight_kg": 40, "condition": "new"},
                price_minor=49500,
                currency="PHP",
                stock_qty=5000,
                unit="bag",
                tags=["cement", "holcim", "portland"],
                status=CatalogItemStatus.ACTIVE,
            ))
            db.add(CatalogItem(
                company_id=company.id,
                branch_id=branch.id,
                category_id=it_cat.id,
                title="Lenovo ThinkPad E14 Gen 5",
                description="Business laptop, Intel Core i5, 8GB RAM, 256GB SSD.",
                attrs_jsonb={"brand": "Lenovo", "model": "ThinkPad E14 Gen 5", "condition": "new", "warranty_months": 12},
                price_minor=5990000,
                currency="PHP",
                stock_qty=20,
                unit="unit",
                tags=["laptop", "lenovo", "thinkpad"],
                status=CatalogItemStatus.ACTIVE,
            ))
            print("  Created catalog items: Cement, Laptop")

        # ── Platform Settings ───────────────────────────────────────
        for s in DEFAULT_SETTINGS:
            result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == s["key"]))
            if not result.scalar_one_or_none():
                db.add(PlatformSetting(**s))
        print("  Platform settings seeded")

        # ── Notification Templates ──────────────────────────────────
        for t in DEFAULT_NOTIFICATION_TEMPLATES:
            key = f"{t['template_key']}_{t['channel']}"
            result = await db.execute(select(NotificationTemplate).where(NotificationTemplate.template_key == key))
            if not result.scalar_one_or_none():
                db.add(NotificationTemplate(
                    template_key=key,
                    channel=t["channel"],
                    subject=t.get("subject"),
                    body=t["body"],
                    variables_hint="{{intent_title}}, {{order_id}}, {{amount}}, {{currency}}, {{category}}, {{location}}, {{delivery_status}}, {{dispute_reason}}, {{dispute_status}}",
                ))
        print("  Notification templates seeded")

        await db.commit()

    print("\nSeed complete.")
    print("  admin@procureping.local       / Admin1234!")
    print("  superadmin@procureping.local  / SuperAdmin1234!")
    print("  buyer@procureping.local       / Buyer1234!")
    print("  supplier@procureping.local    / Supplier1234!")
    print("\n  --- Demo accounts ---")
    print("  buyer@demo.procureping        / 123  (BUYER)")
    print("  supplier@demo.procureping     / 123  (SUPPLIER)")
    print("  admin@procureping.com         / admin123  (SUPER_ADMIN / admin console)")


if __name__ == "__main__":
    asyncio.run(seed())
