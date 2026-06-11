from pydantic import BaseModel, EmailStr

from app.models.user import AccountType, UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None
    role: UserRole = UserRole.BUYER
    account_type: AccountType = AccountType.INDIVIDUAL


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class SystemModeResponse(BaseModel):
    demo_mode: bool
    registration_enabled: bool
    app_name: str
    intent_max_attachments: int
