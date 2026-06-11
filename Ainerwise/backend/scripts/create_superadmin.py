"""Create a superadmin user. Run: python -m scripts.create_superadmin"""
import asyncio
import sys
sys.path.insert(0, "/app")

from sqlalchemy import select
from app.core.permissions import UserRole
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.user import Company, User


async def main():
    async with async_session_factory() as db:
        existing = await db.execute(select(User).where(User.email == "admin@ainerwise.com"))
        if existing.scalar_one_or_none():
            print("Superadmin already exists")
            return

        company = Company(name="AinerWise Official", type="official", country="Serbia", city="Belgrade")
        db.add(company)
        await db.flush()

        user = User(
            email="admin@ainerwise.com",
            password_hash=hash_password("admin123456"),
            full_name="AinerWise Admin",
            role="super_admin",
            language="en",
            country="Serbia",
            company_id=company.id,
        )
        db.add(user)
        await db.commit()
        print(f"Superadmin created: admin@ainerwise.com / admin123456")


if __name__ == "__main__":
    asyncio.run(main())
