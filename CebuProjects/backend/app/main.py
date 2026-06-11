import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import async_session
from app.routers import (
    addresses,
    admin,
    admin_trust,
    auth,
    buyer_business,
    buyer_projects,
    catalog,
    categories,
    companies,
    deliveries,
    disputes,
    intents,
    maps,
    marketplace,
    messages,
    notifications,
    offers,
    orders,
    payments,
    ranking,
    reviews,
    shipping,
    trust,
    uploads,
    users,
    wallets,
)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(buyer_business.router)
app.include_router(buyer_projects.router)
app.include_router(users.router)
app.include_router(companies.router)
app.include_router(categories.router)
app.include_router(catalog.router)
app.include_router(intents.router)
app.include_router(maps.router)
app.include_router(offers.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(deliveries.router)
app.include_router(disputes.router)
app.include_router(messages.router)
app.include_router(notifications.router)
app.include_router(addresses.router)
app.include_router(shipping.router)
app.include_router(marketplace.router)
app.include_router(ranking.router)
app.include_router(reviews.router)
app.include_router(admin.router)
app.include_router(admin_trust.router)
app.include_router(uploads.router)
app.include_router(trust.router)
app.include_router(wallets.router)


@app.get("/health", tags=["Health"])
async def health():
    from sqlalchemy import text
    from app.core.database import async_session
    try:
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}
