from __future__ import annotations

import os
import logging
import json
import httpx
import smtplib
import secrets
from email.message import EmailMessage

email_logger = logging.getLogger('fundbridge.email')
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Optional

import bcrypt
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/funding_platform"
    jwt_secret: str = "change-this-production-secret-to-a-long-random-value"
    frontend_url: str = "http://localhost:5173"
    xai_model: str = "grok-4"
    environment: str = "development"
    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def resolved_database_url(self) -> str:
        value = os.getenv("DATABASE_URL") or os.getenv("SPRING_DATASOURCE_URL") or self.database_url
        if value.startswith("jdbc:"):
            value = value[5:]
        if value.startswith("postgresql://"):
            value = value.replace("postgresql://", "postgresql+psycopg://", 1)
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql+psycopg://") and "sslmode=" not in value:
            value += "?sslmode=require"
        return value

    def resolved_jwt_secret(self) -> str:
        return os.getenv("APP_JWT_SECRET") or os.getenv("JWT_SECRET") or self.jwt_secret


settings = Settings()
engine = create_engine(settings.resolved_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)




class EmailVerification(Base):
    __tablename__ = "email_verifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="ENTREPRENEUR")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(100))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BusinessProfile(Base):
    __tablename__ = "business_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    business_stage: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    funding_needed: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    intended_use_of_funds: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    analysis_result: Mapped[Optional[str]] = mapped_column(Text)


class FunderOrganisation(Base):
    __tablename__ = "funder_organisations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    organisation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organisation_type: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(100))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    approval_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)


class FundingProgramme(Base):
    __tablename__ = "funding_programmes"
    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey("funder_organisations.id"), nullable=False)
    programme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    funding_type: Mapped[str] = mapped_column(String(255), nullable=False)
    minimum_funding: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    maximum_funding: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    business_stage: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    requirements: Mapped[Optional[str]] = mapped_column(Text)
    application_deadline: Mapped[Optional[date]] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class FundingApplication(Base):
    __tablename__ = "funding_applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    entrepreneur_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    programme_id: Mapped[int] = mapped_column(ForeignKey("funding_programmes.id"), nullable=False)
    proposal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ChatConversation(Base):
    __tablename__ = "chat_conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    entrepreneur_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    funder_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    programme_id: Mapped[Optional[int]] = mapped_column(ForeignKey("funding_programmes.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("chat_conversations.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=8)
    accountType: str = "ENTREPRENEUR"
    organisationName: Optional[str] = None
    organisationType: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str = Field(min_length=6, max_length=6)
    newPassword: str = Field(min_length=8)




class VerifyEmailRequest(BaseModel):
    email: str
    code: str = Field(min_length=6, max_length=6)


class UserProfileRequest(BaseModel):
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None

class ProfileRequest(BaseModel):
    businessName: str
    industry: str
    businessStage: str
    description: str
    location: str
    fundingNeeded: Optional[Decimal] = None
    intendedUseOfFunds: Optional[str] = None
    analysis: Optional[dict[str, Any]] = None


class AnalysisRequest(BaseModel):
    profileId: Optional[int] = None
    startupCosts: Decimal
    monthlyRevenue: Decimal
    monthlyExpenses: Decimal
    monthlyGrowthPercent: Decimal = Decimal("0")
    industry: str = ""
    businessDescription: str = ""
    businessStage: str = ""


class ApplicationRequest(BaseModel):
    programmeId: int
    proposal: str = Field(min_length=20, max_length=10000)

class ApplicationUpdateRequest(BaseModel):
    proposal: str = Field(min_length=20, max_length=10000)

class ConversationRequest(BaseModel):
    entrepreneurId: Optional[int] = None
    funderId: Optional[int] = None
    programmeId: Optional[int] = None


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)

class ApplicationStatusRequest(BaseModel):
    status: str


class OrganisationRequest(BaseModel):
    organisationName: str
    organisationType: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


class ProgrammeRequest(BaseModel):
    programmeName: str
    fundingType: str
    minimumFunding: Decimal
    maximumFunding: Decimal
    industry: str
    businessStage: str
    location: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    applicationDeadline: Optional[date] = None


bearer = HTTPBearer(auto_error=False)


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


def send_email(to_email: str, subject: str, body: str) -> None:
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("MAIL_FROM_EMAIL", username or "")
    if not username or not password or not sender:
        email_logger.error("SMTP email not configured. Required variables: SMTP_USERNAME, SMTP_PASSWORD, MAIL_FROM_EMAIL")
        return
    message = EmailMessage()
    message["From"] = os.getenv("MAIL_FROM_NAME", "FundBridge") + " <" + sender + ">"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    try:
        with smtplib.SMTP(os.getenv("SMTP_HOST", settings.smtp_host), int(os.getenv("SMTP_PORT", str(settings.smtp_port))), timeout=15) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(message)
    except Exception as exc:
        email_logger.error("Brevo SMTP send failed: %s", exc)
        return


def make_token(user: User) -> str:
    payload = {"sub": user.email, "role": user.role, "exp": datetime.now(timezone.utc) + timedelta(days=1)}
    return jwt.encode(payload, settings.resolved_jwt_secret(), algorithm="HS256")


def current_user(credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)], db: Session = Depends(db_session)) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, settings.resolved_jwt_secret(), algorithms=["HS256"])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_role(role: str):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role != role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency


def user_response(user: User) -> dict[str, Any]:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "createdAt": user.created_at}


def programme_response(programme: FundingProgramme, organisation_name: Optional[str] = None) -> dict[str, Any]:
    return {"id": programme.id, "programmeName": programme.programme_name, "fundingType": programme.funding_type, "minimumFunding": programme.minimum_funding, "maximumFunding": programme.maximum_funding, "industry": programme.industry, "businessStage": programme.business_stage, "location": programme.location, "description": programme.description, "requirements": programme.requirements, "applicationDeadline": programme.application_deadline, "active": programme.active, "organisationName": organisation_name}


app = FastAPI(title="FundBridge API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url, "https://funding-platform-snowy.vercel.app", "https://funding-platform-mt7.vercel.app", "http://localhost:5173", "http://localhost:5174"], allow_origin_regex=r"https://.*\.vercel\.app$", allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup():
    if os.getenv("RENDER") and settings.resolved_jwt_secret() == "change-this-production-secret-to-a-long-random-value":
        raise RuntimeError("APP_JWT_SECRET must be configured in production")
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE funder_organisations ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'PENDING'"))
        connection.execute(text("ALTER TABLE business_profiles ADD COLUMN IF NOT EXISTS analysis_result TEXT"))
        connection.execute(text("ALTER TABLE business_profiles DROP CONSTRAINT IF EXISTS business_profiles_user_id_key"))
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_email and admin_password:
        with SessionLocal() as db:
            if not db.scalar(select(User).where(User.email == admin_email.strip().lower())):
                db.add(User(name=os.getenv("ADMIN_NAME", "FundBridge Administrator"), email=admin_email.strip().lower(), password=hash_password(admin_password), role="ADMIN"))
                db.commit()


@app.get("/", include_in_schema=False)
def root():
    return {"name": "FundBridge API", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/register")
def register(request: RegisterRequest, background_tasks: BackgroundTasks, db: Session = Depends(db_session)):
    email = request.email.strip().lower()
    if len(request.name.strip()) < 2:
        raise HTTPException(status_code=422, detail="Name must contain at least 2 characters")
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Email already registered")
    account_type = request.accountType.strip().upper()
    if account_type not in {"ENTREPRENEUR", "ORGANISATION"}:
        raise HTTPException(status_code=400, detail="Choose entrepreneur or organisation registration")
    role = "ENTREPRENEUR" if account_type == "ENTREPRENEUR" else "FUNDER"
    if account_type == "ORGANISATION" and (not request.organisationName or len(request.organisationName.strip()) < 2):
        raise HTTPException(status_code=400, detail="Organisation name is required")
    user = User(name=request.name.strip(), email=email, password=hash_password(request.password), role=role)
    db.add(user); db.flush()
    if account_type == "ORGANISATION":
        db.add(FunderOrganisation(user_id=user.id, organisation_name=request.organisationName.strip(), organisation_type=request.organisationType, description=request.description, website=request.website, phone=request.phone, location=request.location))
    db.commit(); db.refresh(user)
    verification_code = f"{secrets.randbelow(1000000):06d}"
    db.add(EmailVerification(email=email, code_hash=hash_password(verification_code), expires_at=datetime.utcnow() + timedelta(minutes=15)))
    db.commit()
    background_tasks.add_task(send_email, email, "Verify your FundBridge email", f"Your FundBridge verification code is {verification_code}. It expires in 15 minutes.")
    response = user_response(user)
    response["verificationRequired"] = True
    response["message"] = "Your account was created. Check your email for the six-digit verification code before logging in."
    if account_type == "ORGANISATION":
        response["message"] = "Organisation registration submitted. Check your email for the verification code, then wait for administrator approval."
        response["pendingApproval"] = True
        admin_email = os.getenv("ADMIN_EMAIL")
        if admin_email:
            background_tasks.add_task(send_email, admin_email, "New FundBridge organisation registration", f"Organisation {request.organisationName} registered with email {email} and is waiting for approval.")
    return response



@app.post("/api/auth/verify-email")
def verify_email(request: VerifyEmailRequest, db: Session = Depends(db_session)):
    email = request.email.strip().lower()
    verification = db.scalar(select(EmailVerification).where(EmailVerification.email == email, EmailVerification.used.is_(False)).order_by(EmailVerification.created_at.desc()))
    if not verification or verification.expires_at < datetime.utcnow() or not verify_password(request.code, verification.code_hash):
        raise HTTPException(status_code=400, detail="Invalid or expired email verification code")
    verification.used = True
    db.commit()
    return {"message": "Email verified successfully. You can now log in."}

@app.post("/api/auth/login")
def login(request: LoginRequest, db: Session = Depends(db_session)):
    user = db.scalar(select(User).where(User.email == request.email.strip().lower()))
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    pending_verification = db.scalar(select(EmailVerification).where(EmailVerification.email == user.email, EmailVerification.used.is_(False)).order_by(EmailVerification.created_at.desc()))
    if pending_verification:
        raise HTTPException(status_code=403, detail="Please verify your email address before logging in")
    if user.role == "FUNDER":
        organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id))
        if organisation and organisation.approval_status != "APPROVED":
            detail = "Organisation registration was not approved" if organisation.approval_status == "REJECTED" else "Organisation account is waiting for administrator approval"
            raise HTTPException(status_code=403, detail=detail)
    return {"token": make_token(user), **user_response(user)}

@app.post("/api/auth/forgot-password")
def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(db_session)):
    email = request.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=404, detail="No FundBridge account was found with that email address.")
    otp = f"{secrets.randbelow(1000000):06d}"
    db.add(PasswordReset(email=email, otp_hash=hash_password(otp), expires_at=datetime.utcnow() + timedelta(minutes=10)))
    db.commit()
    background_tasks.add_task(send_email, email, "Your FundBridge password reset code", f"Your one-time password is {otp}. It expires in 10 minutes.")
    return {"message": "A password reset code has been sent to your email address."}

@app.post("/api/auth/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(db_session)):
    email = request.email.strip().lower(); reset = db.scalar(select(PasswordReset).where(PasswordReset.email == email, PasswordReset.used.is_(False)).order_by(PasswordReset.created_at.desc()))
    if not reset or reset.expires_at < datetime.utcnow() or not verify_password(request.otp, reset.otp_hash): raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    user = db.scalar(select(User).where(User.email == email))
    if not user: raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    user.password = hash_password(request.newPassword); reset.used = True; db.commit()
    return {"message": "Password reset successfully. You can now log in."}


@app.get("/api/entrepreneur/dashboard")
def entrepreneur_dashboard(user: User = Depends(require_role("ENTREPRENEUR"))):
    return f"Welcome to the Entrepreneur Dashboard, {user.email}"


@app.post("/api/entrepreneur/business-profile", status_code=201)
def create_profile(request: ProfileRequest, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    profile = BusinessProfile(user_id=user.id, business_name=request.businessName, industry=request.industry, business_stage=request.businessStage, description=request.description, location=request.location, funding_needed=request.fundingNeeded, intended_use_of_funds=request.intendedUseOfFunds, analysis_result=json.dumps(request.analysis, default=str) if request.analysis else None)
    db.add(profile); db.commit(); db.refresh(profile)
    return profile_response(profile)


@app.get("/api/entrepreneur/business-profiles")
def list_business_profiles(user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    return [profile_response(row) for row in db.scalars(select(BusinessProfile).where(BusinessProfile.user_id == user.id).order_by(BusinessProfile.updated_at.desc())).all()]


@app.get("/api/entrepreneur/business-profile")
def get_profile(user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.user_id == user.id).order_by(BusinessProfile.updated_at.desc()))
    if not profile: raise HTTPException(status_code=404, detail="Business profile not found")
    return profile_response(profile)


@app.put("/api/entrepreneur/business-profiles/{profile_id}")
def update_business_profile(profile_id: int, request: ProfileRequest, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.id == profile_id, BusinessProfile.user_id == user.id))
    if not profile: raise HTTPException(status_code=404, detail="Business profile not found")
    for key, value in {"business_name": request.businessName, "industry": request.industry, "business_stage": request.businessStage, "description": request.description, "location": request.location, "funding_needed": request.fundingNeeded, "intended_use_of_funds": request.intendedUseOfFunds, "analysis_result": json.dumps(request.analysis, default=str) if request.analysis else profile.analysis_result}.items(): setattr(profile, key, value)
    db.commit(); db.refresh(profile); return profile_response(profile)


@app.delete("/api/entrepreneur/business-profiles/{profile_id}", status_code=204)
def delete_business_profile(profile_id: int, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.id == profile_id, BusinessProfile.user_id == user.id))
    if not profile: raise HTTPException(status_code=404, detail="Business profile not found")
    db.delete(profile); db.commit(); return None


@app.put("/api/entrepreneur/business-profile")
def update_profile(request: ProfileRequest, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.user_id == user.id).order_by(BusinessProfile.updated_at.desc()))
    if not profile: raise HTTPException(status_code=404, detail="Business profile not found")
    for key, value in {"business_name": request.businessName, "industry": request.industry, "business_stage": request.businessStage, "description": request.description, "location": request.location, "funding_needed": request.fundingNeeded, "intended_use_of_funds": request.intendedUseOfFunds, "analysis_result": json.dumps(request.analysis, default=str) if request.analysis else profile.analysis_result}.items(): setattr(profile, key, value)
    db.commit(); db.refresh(profile)
    return profile_response(profile)


def profile_response(profile: BusinessProfile) -> dict[str, Any]:
    return {"id": profile.id, "businessName": profile.business_name, "industry": profile.industry, "businessStage": profile.business_stage, "description": profile.description, "location": profile.location, "fundingNeeded": profile.funding_needed, "intendedUseOfFunds": profile.intended_use_of_funds, "createdAt": profile.created_at, "updatedAt": profile.updated_at, "analysis": json.loads(profile.analysis_result) if profile.analysis_result else None}


async def grok_assessment(request: AnalysisRequest, deterministic: dict[str, Any]) -> Optional[dict[str, Any]]:
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        return None
    prompt = "Return JSON with riskLevel, recommendation, keyRisks, assumptions, narrative for this business proposal: " + json.dumps({"startupCosts": str(request.startupCosts), "monthlyRevenue": str(request.monthlyRevenue), "monthlyExpenses": str(request.monthlyExpenses), "monthlyGrowthPercent": str(request.monthlyGrowthPercent), "deterministic": deterministic})
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.post("https://api.x.ai/v1/responses", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": os.getenv("XAI_MODEL", "grok-4"), "input": prompt, "max_output_tokens": 700})
            response.raise_for_status()
            data = response.json()
        text = "".join(content.get("text", "") for item in data.get("output", []) for content in item.get("content", [])).strip()
        return json.loads(text.replace("```json", "").replace("```", "").strip())
    except Exception:
        return None

@app.post("/api/entrepreneur/business-analysis")
async def analyse(request: AnalysisRequest, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    if min(request.startupCosts, request.monthlyRevenue, request.monthlyExpenses, request.monthlyGrowthPercent) < 0:
        raise HTTPException(status_code=400, detail="Financial values cannot be negative.")
    revenue = float(request.monthlyRevenue); expenses = float(request.monthlyExpenses); startup = float(request.startupCosts); growth = min(float(request.monthlyGrowthPercent), 25.0) / 100; monthly_profit = revenue - expenses
    factors = {"technology": (88, "High", "Technology benefits from continued digital adoption, but competition is strong."), "ai": (92, "Very high", "AI demand is strong, but the proposal must solve a specific customer problem."), "artificial intelligence": (92, "Very high", "AI demand is strong, but the proposal must solve a specific customer problem."), "healthcare": (84, "High", "Healthcare demand is durable, but compliance and trust affect growth."), "agriculture": (78, "High", "Agricultural demand is durable, while weather and input costs create risk."), "education": (76, "High", "Education has durable demand, with affordability and customer acquisition risks."), "manufacturing": (74, "Moderate-high", "Manufacturing can scale through contracts, but working capital matters."), "retail": (65, "Moderate", "Retail depends on pricing, location, repeat customers, and competition."), "tourism": (63, "Moderate", "Tourism is sensitive to seasonality and economic conditions.")}
    demand_score, demand_level, demand_note = (60, "Moderate", "Demand depends on the target market, customer validation, pricing, and execution.")
    for key, factor in factors.items():
        if key in request.industry.strip().lower(): demand_score, demand_level, demand_note = factor; break
    def projection(month):
        projected_revenue = revenue * ((1 + growth) ** month); projected_expenses = expenses * ((1 + (growth * 0.55)) ** month); return projected_revenue, projected_expenses, projected_revenue - projected_expenses
    monthly = projection(0)[2]; projected12 = projection(12)[2]; projected18 = projection(18)[2]; projected24 = projection(24)[2]
    break_even = int((startup / monthly_profit) + 0.9999) if monthly_profit > 0 and startup > 0 else (0 if monthly_profit > 0 else None)
    profitability_month = 0 if monthly_profit > 0 else None
    if profitability_month is None:
        for month in range(1, 61):
            if projection(month)[2] > 0: profitability_month = month; break
    risks = []
    if monthly_profit <= 0: risks.append("Current monthly expenses are higher than revenue.")
    if startup > 0 and monthly_profit > 0 and break_even and break_even > 24: risks.append("Startup-cost recovery is expected to take more than two years.")
    if growth == 0: risks.append("No monthly growth was provided; the forecast assumes flat revenue.")
    if len(request.businessDescription.strip()) < 40: risks.append("Add customer, pricing, and traction detail to improve confidence.")
    if not risks: risks.append("Validate demand with paying customers before committing the full investment.")
    outlook = "Strong potential" if monthly_profit > 0 and demand_score >= 80 else "Potentially profitable" if monthly_profit > 0 else "Needs improvement"
    confidence = "High" if monthly_profit > 0 and growth > 0 and len(request.businessDescription.strip()) >= 40 else "Medium" if monthly_profit > 0 else "Low"
    horizon = f"about {profitability_month / 12:.1f} years" if profitability_month and profitability_month >= 12 else "within the first year" if profitability_month == 0 else "not reached within the five-year forecast"
    result = {"outlook": outlook, "summary": f"At the figures supplied, the business is projected to become monthly-profitable {horizon}. The industry demand signal is {demand_level.lower()}, but execution and customer validation remain essential.", "estimatedBreakEvenMonths": break_even, "estimatedProfitabilityMonths": profitability_month, "estimatedMonthlyProfit": round(monthly_profit, 2), "estimatedAnnualProfit": round(monthly_profit * 12, 2), "projectedProfit12Months": round(projected12, 2), "projectedProfit18Months": round(projected18, 2), "projectedProfit24Months": round(projected24, 2), "monthlyExpenses": round(expenses, 2), "demandScore": demand_score, "demandLevel": demand_level, "demandNote": demand_note, "riskFlags": risks, "confidence": confidence, "aiAssessment": None, "aiProvider": "free-rules-engine", "disclaimer": "This is an advisory estimate based on the figures and general industry heuristics you entered. It is not live market research, a funding decision, or a profit guarantee."}
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.id == request.profileId, BusinessProfile.user_id == user.id)) if request.profileId else db.scalar(select(BusinessProfile).where(BusinessProfile.user_id == user.id).order_by(BusinessProfile.updated_at.desc()))
    if profile: profile.analysis_result = json.dumps(result, default=str); db.commit()
    return result

@app.get("/api/funder/programmes/active")
@app.get("/api/funder/programmes/active/")
def active_programmes(db: Session = Depends(db_session)):
    rows = db.scalars(select(FundingProgramme).where(FundingProgramme.active.is_(True)).order_by(FundingProgramme.created_at.desc())).all()
    return [programme_response(row) for row in rows]


@app.get("/api/funder/programmes/industry/{industry}")
def programmes_by_industry(industry: str, db: Session = Depends(db_session)):
    rows = db.scalars(select(FundingProgramme).where(FundingProgramme.active.is_(True), FundingProgramme.industry.ilike(industry))).all()
    return [programme_response(row) for row in rows]


@app.get("/api/funder/programmes/stage/{business_stage}")
def programmes_by_stage(business_stage: str, db: Session = Depends(db_session)):
    rows = db.scalars(select(FundingProgramme).where(FundingProgramme.active.is_(True), FundingProgramme.business_stage.ilike(business_stage))).all()
    return [programme_response(row) for row in rows]


@app.get("/api/entrepreneur/applications")
def my_applications(user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    rows = db.scalars(select(FundingApplication).where(FundingApplication.entrepreneur_id == user.id).order_by(FundingApplication.created_at.desc())).all()
    result = []
    for row in rows:
        programme = db.get(FundingProgramme, row.programme_id)
        organisation = db.get(FunderOrganisation, programme.organisation_id) if programme else None
        funder = db.get(User, organisation.user_id) if organisation else None
        result.append({"id": row.id, "programmeId": row.programme_id, "programmeName": programme.programme_name if programme else "Unknown programme", "funderId": funder.id if funder else None, "organisationName": organisation.organisation_name if organisation else None, "proposal": row.proposal, "status": row.status, "createdAt": row.created_at})
    return result


@app.post("/api/entrepreneur/applications", status_code=201)
def submit_application(request: ApplicationRequest, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    programme = db.scalar(select(FundingProgramme).where(FundingProgramme.id == request.programmeId, FundingProgramme.active.is_(True)))
    if not programme: raise HTTPException(status_code=404, detail="Active funding programme not found.")
    if db.scalar(select(FundingApplication).where(FundingApplication.entrepreneur_id == user.id, FundingApplication.programme_id == programme.id)):
        raise HTTPException(status_code=409, detail="You have already applied to this programme")
    row = FundingApplication(entrepreneur_id=user.id, programme_id=programme.id, proposal=request.proposal.strip(), status="SUBMITTED")
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "programmeName": programme.programme_name, "proposal": row.proposal, "status": row.status, "createdAt": row.created_at}


@app.put("/api/entrepreneur/applications/{application_id}")
def edit_application(application_id: int, request: ApplicationUpdateRequest, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    row = db.get(FundingApplication, application_id)
    if not row or row.entrepreneur_id != user.id: raise HTTPException(status_code=404, detail="Application not found")
    if row.status in {"ACCEPTED", "DECLINED"}: raise HTTPException(status_code=409, detail="This application can no longer be edited")
    row.proposal = request.proposal.strip(); db.commit(); db.refresh(row)
    programme = db.get(FundingProgramme, row.programme_id); organisation = db.get(FunderOrganisation, programme.organisation_id) if programme else None
    return application_response(row, programme, user, organisation, db)


@app.delete("/api/entrepreneur/applications/{application_id}", status_code=204)
def delete_application(application_id: int, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    row = db.get(FundingApplication, application_id)
    if not row or row.entrepreneur_id != user.id: raise HTTPException(status_code=404, detail="Application not found")
    db.delete(row); db.commit(); return None

def application_response(row: FundingApplication, programme: Optional[FundingProgramme], entrepreneur: Optional[User], organisation: Optional[FunderOrganisation] = None, db: Session = None) -> dict[str, Any]:
    return {"id": row.id, "programmeId": row.programme_id, "programmeName": programme.programme_name if programme else "Unknown programme", "organisationName": organisation.organisation_name if organisation else None, "analysis": (json.loads(db.scalar(select(BusinessProfile.analysis_result).where(BusinessProfile.user_id == row.entrepreneur_id)) or "null")), "entrepreneurId": entrepreneur.id if entrepreneur else row.entrepreneur_id, "entrepreneurName": entrepreneur.name if entrepreneur else "Unknown entrepreneur", "entrepreneurEmail": entrepreneur.email if entrepreneur else None, "proposal": row.proposal, "status": row.status, "createdAt": row.created_at}


@app.get("/api/funder/entrepreneur-profiles")
def entrepreneur_profiles_for_funders(user: User = Depends(require_role("FUNDER")), db: Session = Depends(db_session)):
    profiles = db.scalars(select(BusinessProfile).join(User, BusinessProfile.user_id == User.id).order_by(BusinessProfile.updated_at.desc())).all()
    return [{**profile_response(profile), "entrepreneurId": profile.user_id, "entrepreneurName": db.get(User, profile.user_id).name, "entrepreneurEmail": db.get(User, profile.user_id).email} for profile in profiles]


@app.get("/api/funder/applications")
def funder_applications(user: User = Depends(require_role("FUNDER")), db: Session = Depends(db_session)):
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id))
    if not organisation: raise HTTPException(status_code=404, detail="Organisation profile not found")
    rows = db.scalars(select(FundingApplication).join(FundingProgramme, FundingApplication.programme_id == FundingProgramme.id).where(FundingProgramme.organisation_id == organisation.id).order_by(FundingApplication.created_at.desc())).all()
    return [application_response(row, db.get(FundingProgramme, row.programme_id), db.get(User, row.entrepreneur_id), organisation, db) for row in rows]


@app.patch("/api/funder/applications/{application_id}")
def update_application_status(application_id: int, request: ApplicationStatusRequest, user: User = Depends(require_role("FUNDER")), db: Session = Depends(db_session)):
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id)); row = db.get(FundingApplication, application_id); programme = db.get(FundingProgramme, row.programme_id) if row else None
    new_status = request.status.strip().upper()
    if not row or not programme or not organisation or programme.organisation_id != organisation.id: raise HTTPException(status_code=404, detail="Application not found")
    if new_status not in {"SUBMITTED", "REVIEWING", "ACCEPTED", "DECLINED"}: raise HTTPException(status_code=400, detail="Invalid application status")
    row.status = new_status; db.commit()
    return application_response(row, programme, db.get(User, row.entrepreneur_id), organisation, db)


def conversation_response(row: ChatConversation, current_user_id: int, db: Session) -> dict[str, Any]:
    entrepreneur = db.get(User, row.entrepreneur_id); funder = db.get(User, row.funder_id); programme = db.get(FundingProgramme, row.programme_id) if row.programme_id else None
    entrepreneur_profile = db.scalar(select(UserProfile).where(UserProfile.user_id == row.entrepreneur_id)); funder_profile = db.scalar(select(UserProfile).where(UserProfile.user_id == row.funder_id))
    last = db.scalar(select(ChatMessage).where(ChatMessage.conversation_id == row.id).order_by(ChatMessage.created_at.desc()))
    return {"id": row.id, "entrepreneurId": row.entrepreneur_id, "entrepreneurName": entrepreneur.name if entrepreneur else "Entrepreneur", "entrepreneurAvatar": entrepreneur_profile.avatar if entrepreneur_profile else None, "funderId": row.funder_id, "funderName": funder.name if funder else "Funder", "funderAvatar": funder_profile.avatar if funder_profile else None, "programmeId": row.programme_id, "programmeName": programme.programme_name if programme else None, "lastMessage": last.content if last else None, "lastMessageAt": last.created_at if last else None, "createdAt": row.created_at}


def can_access_conversation(row: ChatConversation, user: User) -> bool:
    return user.id in {row.entrepreneur_id, row.funder_id}


@app.get("/api/chat/conversations")
def chat_conversations(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.scalars(select(ChatConversation).where((ChatConversation.entrepreneur_id == user.id) | (ChatConversation.funder_id == user.id)).order_by(ChatConversation.updated_at.desc())).all()
    unique = {}
    for row in rows:
        unique.setdefault((row.entrepreneur_id, row.funder_id), row)
    return [conversation_response(row, user.id, db) for row in unique.values()]


@app.post("/api/chat/conversations", status_code=201)
def create_conversation(request: ConversationRequest, user: User = Depends(current_user), db: Session = Depends(db_session)):
    entrepreneur_id = request.entrepreneurId if user.role == "FUNDER" else user.id
    funder_id = request.funderId if user.role == "ENTREPRENEUR" else user.id
    if user.role not in {"ENTREPRENEUR", "FUNDER"} or not entrepreneur_id or not funder_id or entrepreneur_id == funder_id:
        raise HTTPException(status_code=400, detail="Choose a valid entrepreneur and funder conversation")
    entrepreneur = db.get(User, entrepreneur_id); funder = db.get(User, funder_id)
    if not entrepreneur or entrepreneur.role != "ENTREPRENEUR" or not funder or funder.role != "FUNDER": raise HTTPException(status_code=404, detail="User not found")
    if request.programmeId:
        programme = db.get(FundingProgramme, request.programmeId)
        if not programme: raise HTTPException(status_code=404, detail="Programme not found")
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == funder_id))
    connected = db.scalar(select(FundingApplication).join(FundingProgramme, FundingApplication.programme_id == FundingProgramme.id).where(FundingApplication.entrepreneur_id == entrepreneur_id, FundingProgramme.organisation_id == organisation.id)) if organisation else None
    has_profile = db.scalar(select(BusinessProfile).where(BusinessProfile.user_id == entrepreneur_id))
    if not connected and not has_profile:
        raise HTTPException(status_code=403, detail="Conversation is only available after a proposal or application connection")
    row = db.scalar(select(ChatConversation).where(ChatConversation.entrepreneur_id == entrepreneur_id, ChatConversation.funder_id == funder_id).order_by(ChatConversation.updated_at.desc()))
    if not row:
        row = ChatConversation(entrepreneur_id=entrepreneur_id, funder_id=funder_id, programme_id=request.programmeId)
        db.add(row)
    elif request.programmeId:
        row.programme_id = request.programmeId
    row.updated_at = datetime.utcnow()
    db.commit(); db.refresh(row)
    return conversation_response(row, user.id, db)


@app.delete("/api/chat/conversations/{conversation_id}")
def delete_chat_conversation(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    conversation = db.get(ChatConversation, conversation_id)
    if not conversation or not can_access_conversation(conversation, user):
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.execute(text("DELETE FROM chat_messages WHERE conversation_id = :conversation_id"), {"conversation_id": conversation_id})
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted", "conversationId": conversation_id}


@app.get("/api/chat/conversations/{conversation_id}/messages")
def chat_messages(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    conversation = db.get(ChatConversation, conversation_id)
    if not conversation or not can_access_conversation(conversation, user): raise HTTPException(status_code=404, detail="Conversation not found")
    rows = db.scalars(select(ChatMessage).where(ChatMessage.conversation_id == conversation_id).order_by(ChatMessage.created_at.asc())).all()
    return [{"id": row.id, "senderId": row.sender_id, "content": row.content, "createdAt": row.created_at} for row in rows]


@app.post("/api/chat/conversations/{conversation_id}/messages", status_code=201)
def send_chat_message(conversation_id: int, request: MessageRequest, background_tasks: BackgroundTasks, user: User = Depends(current_user), db: Session = Depends(db_session)):
    conversation = db.get(ChatConversation, conversation_id)
    if not conversation or not can_access_conversation(conversation, user): raise HTTPException(status_code=404, detail="Conversation not found")
    first_message = db.scalar(select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)) is None
    row = ChatMessage(conversation_id=conversation_id, sender_id=user.id, content=request.content.strip()); db.add(row); conversation.updated_at = datetime.utcnow(); db.commit(); db.refresh(row)
    if first_message:
        recipient_id = conversation.funder_id if user.id == conversation.entrepreneur_id else conversation.entrepreneur_id
        recipient = db.get(User, recipient_id)
        programme = db.get(FundingProgramme, conversation.programme_id) if conversation.programme_id else None
        if recipient:
            context = programme.programme_name if programme else "a FundBridge conversation"
            background_tasks.add_task(send_email, recipient.email, "New FundBridge message", f"{user.name} sent you a new message in {context}. Log in to reply.")
    return {"id": row.id, "senderId": row.sender_id, "content": row.content, "createdAt": row.created_at}


@app.post("/api/funder/organisation")
def create_organisation(request: OrganisationRequest, user: User = Depends(require_role("FUNDER")), db: Session = Depends(db_session)):
    if db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id)): raise HTTPException(status_code=400, detail="Organisation profile already exists")
    row = FunderOrganisation(user_id=user.id, organisation_name=request.organisationName, organisation_type=request.organisationType, description=request.description, website=request.website, phone=request.phone, location=request.location)
    db.add(row); db.commit(); db.refresh(row)
    return organisation_response(row)


def organisation_response(row: FunderOrganisation) -> dict[str, Any]:
    return {"id": row.id, "organisationName": row.organisation_name, "organisationType": row.organisation_type, "description": row.description, "website": row.website, "phone": row.phone, "location": row.location, "createdAt": row.created_at}


@app.get("/api/funder/organisation")
def get_organisation(user: User = Depends(require_role("FUNDER")), db: Session = Depends(db_session)):
    row = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id))
    if not row: raise HTTPException(status_code=404, detail="Organisation profile not found")
    return organisation_response(row)


@app.post("/api/funder/programmes", status_code=201)
def create_programme(request: ProgrammeRequest, user: User = Depends(require_role("FUNDER")), db: Session = Depends(db_session)):
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id))
    if not organisation: raise HTTPException(status_code=404, detail="Please create an organisation profile first")
    row = FundingProgramme(organisation_id=organisation.id, programme_name=request.programmeName, funding_type=request.fundingType, minimum_funding=request.minimumFunding, maximum_funding=request.maximumFunding, industry=request.industry, business_stage=request.businessStage, location=request.location, description=request.description, requirements=request.requirements, application_deadline=request.applicationDeadline, active=True)
    db.add(row); db.commit(); db.refresh(row)
    return programme_response(row, organisation.organisation_name)


@app.put("/api/funder/programmes/{programme_id}")
def edit_programme(programme_id: int, request: ProgrammeRequest, user: User = Depends(require_role("FUNDER")), db: Session = Depends(db_session)):
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id))
    programme = db.get(FundingProgramme, programme_id)
    if not programme or not organisation or programme.organisation_id != organisation.id:
        raise HTTPException(status_code=404, detail="Programme not found")
    for key, value in {"programme_name": request.programmeName, "funding_type": request.fundingType, "minimum_funding": request.minimumFunding, "maximum_funding": request.maximumFunding, "industry": request.industry, "business_stage": request.businessStage, "location": request.location, "description": request.description, "requirements": request.requirements, "application_deadline": request.applicationDeadline}.items(): setattr(programme, key, value)
    db.commit(); db.refresh(programme)
    return programme_response(programme, organisation.organisation_name)


@app.delete("/api/funder/programmes/{programme_id}", status_code=204)
def delete_programme(programme_id: int, user: User = Depends(require_role("FUNDER")), db: Session = Depends(db_session)):
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id)); programme = db.get(FundingProgramme, programme_id)
    if not programme or not organisation or programme.organisation_id != organisation.id: raise HTTPException(status_code=404, detail="Programme not found")
    programme.active = False; db.commit(); return None


@app.get("/api/funder/programmes")
def my_programmes(user: User = Depends(require_role("FUNDER")), db: Session = Depends(db_session)):
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id))
    if not organisation: raise HTTPException(status_code=404, detail="Organisation profile not found")
    rows = db.scalars(select(FundingProgramme).where(FundingProgramme.organisation_id == organisation.id)).all()
    return [programme_response(row, organisation.organisation_name) for row in rows]


@app.get("/api/test/protected")
def protected_test(user: User = Depends(current_user)):
    return f"Authenticated successfully as: {user.email}"


@app.get("/api/admin/users")
def admin_users(user: User = Depends(require_role("ADMIN")), db: Session = Depends(db_session)):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [{"id": item.id, "name": item.name, "email": item.email, "role": item.role, "createdAt": item.created_at} for item in users]


@app.get("/api/admin/programmes")
def admin_programmes(user: User = Depends(require_role("ADMIN")), db: Session = Depends(db_session)):
    rows = db.scalars(select(FundingProgramme).order_by(FundingProgramme.created_at.desc())).all()
    return [programme_response(row, (db.scalar(select(FunderOrganisation.organisation_name).where(FunderOrganisation.id == row.organisation_id)) or "Organisation")) for row in rows]


@app.delete("/api/admin/programmes/{programme_id}")
def admin_delete_programme(programme_id: int, user: User = Depends(require_role("ADMIN")), db: Session = Depends(db_session)):
    programme = db.get(FundingProgramme, programme_id)
    if not programme:
        raise HTTPException(status_code=404, detail="Programme not found")
    conversations = db.scalars(select(ChatConversation).where(ChatConversation.programme_id == programme_id)).all()
    conversation_ids = [item.id for item in conversations]
    for item in db.scalars(select(ChatMessage).where(ChatMessage.conversation_id.in_(conversation_ids))).all(): db.delete(item)
    for item in conversations: db.delete(item)
    for item in db.scalars(select(FundingApplication).where(FundingApplication.programme_id == programme_id)).all(): db.delete(item)
    db.delete(programme)
    db.commit()
    return {"message": "Programme and associated applications deleted", "programmeId": programme_id}


@app.delete("/api/admin/applications/{application_id}")
def admin_delete_application(application_id: int, user: User = Depends(require_role("ADMIN")), db: Session = Depends(db_session)):
    row = db.get(FundingApplication, application_id)
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(row)
    db.commit()
    return {"message": "Application deleted", "applicationId": application_id}


@app.get("/api/admin/applications")
def admin_applications(user: User = Depends(require_role("ADMIN")), db: Session = Depends(db_session)):
    rows = db.scalars(select(FundingApplication).order_by(FundingApplication.created_at.desc())).all(); result = []
    for row in rows:
        programme = db.get(FundingProgramme, row.programme_id); organisation = db.get(FunderOrganisation, programme.organisation_id) if programme else None
        result.append(application_response(row, programme, db.get(User, row.entrepreneur_id), organisation, db))
    return result


@app.get("/api/admin/organisations/pending")
def pending_organisations(user: User = Depends(require_role("ADMIN")), db: Session = Depends(db_session)):
    rows = db.scalars(select(FunderOrganisation).join(User, FunderOrganisation.user_id == User.id).where(FunderOrganisation.approval_status == "PENDING").order_by(FunderOrganisation.created_at.desc())).all()
    result = []
    for row in rows:
        applicant = db.get(User, row.user_id)
        result.append({"userId": applicant.id, "name": applicant.name, "email": applicant.email, "organisation": organisation_response(row)})
    return result


@app.post("/api/admin/organisations/{user_id}/approve")
def approve_organisation(user_id: int, user: User = Depends(require_role("ADMIN")), db: Session = Depends(db_session)):
    applicant = db.get(User, user_id)
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user_id))
    if not applicant or applicant.role != "FUNDER" or not organisation or organisation.approval_status != "PENDING":
        raise HTTPException(status_code=404, detail="Pending organisation not found")
    organisation.approval_status = "APPROVED"
    db.commit()
    return {"message": "Organisation approved", "user": user_response(applicant)}


@app.post("/api/admin/organisations/{user_id}/reject")
def reject_organisation(user_id: int, user: User = Depends(require_role("ADMIN")), db: Session = Depends(db_session)):
    applicant = db.get(User, user_id)
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user_id))
    if not applicant or applicant.role != "FUNDER" or not organisation or organisation.approval_status != "PENDING":
        raise HTTPException(status_code=404, detail="Pending organisation not found")
    organisation.approval_status = "REJECTED"
    db.commit()
    return {"message": "Organisation rejected"}








@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: int, user: User = Depends(require_role("ADMIN")), db: Session = Depends(db_session)):
    if user.id == user_id:
        raise HTTPException(status_code=400, detail="The administrator account cannot delete itself")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user_id))
    programme_ids = [item.id for item in db.scalars(select(FundingProgramme).where(FundingProgramme.organisation_id == organisation.id)).all()] if organisation else []
    applications = db.scalars(select(FundingApplication).where((FundingApplication.entrepreneur_id == user_id) | FundingApplication.programme_id.in_(programme_ids))).all()
    conversations = db.scalars(select(ChatConversation).where((ChatConversation.entrepreneur_id == user_id) | (ChatConversation.funder_id == user_id) | ChatConversation.programme_id.in_(programme_ids))).all()
    conversation_ids = {item.id for item in conversations}
    sent_messages = db.scalars(select(ChatMessage).where(ChatMessage.sender_id == user_id)).all()
    conversation_ids.update(item.conversation_id for item in sent_messages)
    all_messages = db.scalars(select(ChatMessage).where(ChatMessage.conversation_id.in_(conversation_ids))).all()
    for item in all_messages: db.delete(item)
    conversations = db.scalars(select(ChatConversation).where(ChatConversation.id.in_(conversation_ids))).all()
    for item in conversations: db.delete(item)
    for item in applications: db.delete(item)
    for item in db.scalars(select(BusinessProfile).where(BusinessProfile.user_id == user_id)).all(): db.delete(item)
    for item in db.scalars(select(PasswordReset).where(PasswordReset.email == target.email)).all(): db.delete(item)
    for item in db.scalars(select(EmailVerification).where(EmailVerification.email == target.email)).all(): db.delete(item)
    for item in db.scalars(select(FundingProgramme).where(FundingProgramme.id.in_(programme_ids))).all(): db.delete(item)
    if organisation: db.delete(organisation)
    db.delete(target)
    db.commit()
    return {"message": "User and all associated data deleted", "userId": user_id}



