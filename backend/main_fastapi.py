from __future__ import annotations

import os
import json
import httpx
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Optional

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, Query, status
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


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="ENTREPRENEUR")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


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
def register(request: RegisterRequest, db: Session = Depends(db_session)):
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
    response = user_response(user)
    if account_type == "ORGANISATION":
        response["message"] = "Organisation registration submitted. An administrator must approve it before login."
        response["pendingApproval"] = True
    return response


@app.post("/api/auth/login")
def login(request: LoginRequest, db: Session = Depends(db_session)):
    user = db.scalar(select(User).where(User.email == request.email.strip().lower()))
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.role == "FUNDER":
        organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id))
        if organisation and organisation.approval_status != "APPROVED":
            detail = "Organisation registration was not approved" if organisation.approval_status == "REJECTED" else "Organisation account is waiting for administrator approval"
            raise HTTPException(status_code=403, detail=detail)
    return {"token": make_token(user), **user_response(user)}

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
    if min(request.startupCosts, request.monthlyRevenue, request.monthlyExpenses) < 0: raise HTTPException(status_code=400, detail="Financial values cannot be negative.")
    profit = request.monthlyRevenue - request.monthlyExpenses
    break_even = int((request.startupCosts / profit).to_integral_value(rounding="ROUND_CEILING")) if profit > 0 else None
    outlook = "Potentially profitable" if profit > 0 else "Break-even only" if profit == 0 else "Needs improvement"
    summary = "Your projected revenue is higher than your projected monthly expenses." if profit > 0 else "Your current projection covers operating costs but does not recover startup costs." if profit == 0 else "Your projected monthly expenses are higher than your projected revenue."
    result = {"outlook": outlook, "summary": summary, "estimatedBreakEvenMonths": break_even, "estimatedMonthlyProfit": profit, "estimatedAnnualProfit": profit * 12, "monthlyExpenses": request.monthlyExpenses, "confidence": "Medium" if profit > 0 else "Low", "disclaimer": "This is an advisory estimate based only on the figures you entered. It is not a funding or profit guarantee."}
    result["aiAssessment"] = await grok_assessment(request, result)
    result["aiProvider"] = "grok" if result["aiAssessment"] else "deterministic-fallback"
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.id == request.profileId, BusinessProfile.user_id == user.id)) if request.profileId else db.scalar(select(BusinessProfile).where(BusinessProfile.user_id == user.id).order_by(BusinessProfile.updated_at.desc()))
    if profile:
        profile.analysis_result = json.dumps(result, default=str)
        db.commit()
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
    if row.status in {"ACCEPTED", "DECLINED"}: raise HTTPException(status_code=409, detail="This application can no longer be deleted")
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
    last = db.scalar(select(ChatMessage).where(ChatMessage.conversation_id == row.id).order_by(ChatMessage.created_at.desc()))
    return {"id": row.id, "entrepreneurId": row.entrepreneur_id, "entrepreneurName": entrepreneur.name if entrepreneur else "Entrepreneur", "funderId": row.funder_id, "funderName": funder.name if funder else "Funder", "programmeId": row.programme_id, "programmeName": programme.programme_name if programme else None, "lastMessage": last.content if last else None, "lastMessageAt": last.created_at if last else None, "createdAt": row.created_at}


def can_access_conversation(row: ChatConversation, user: User) -> bool:
    return user.id in {row.entrepreneur_id, row.funder_id}


@app.get("/api/chat/conversations")
def chat_conversations(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.scalars(select(ChatConversation).where((ChatConversation.entrepreneur_id == user.id) | (ChatConversation.funder_id == user.id)).order_by(ChatConversation.updated_at.desc())).all()
    return [conversation_response(row, user.id, db) for row in rows]


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
    row = db.scalar(select(ChatConversation).where(ChatConversation.entrepreneur_id == entrepreneur_id, ChatConversation.funder_id == funder_id, ChatConversation.programme_id == request.programmeId))
    if not row:
        row = ChatConversation(entrepreneur_id=entrepreneur_id, funder_id=funder_id, programme_id=request.programmeId); db.add(row); db.commit(); db.refresh(row)
    return conversation_response(row, user.id, db)


@app.get("/api/chat/conversations/{conversation_id}/messages")
def chat_messages(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    conversation = db.get(ChatConversation, conversation_id)
    if not conversation or not can_access_conversation(conversation, user): raise HTTPException(status_code=404, detail="Conversation not found")
    rows = db.scalars(select(ChatMessage).where(ChatMessage.conversation_id == conversation_id).order_by(ChatMessage.created_at.asc())).all()
    return [{"id": row.id, "senderId": row.sender_id, "content": row.content, "createdAt": row.created_at} for row in rows]


@app.post("/api/chat/conversations/{conversation_id}/messages", status_code=201)
def send_chat_message(conversation_id: int, request: MessageRequest, user: User = Depends(current_user), db: Session = Depends(db_session)):
    conversation = db.get(ChatConversation, conversation_id)
    if not conversation or not can_access_conversation(conversation, user): raise HTTPException(status_code=404, detail="Conversation not found")
    row = ChatMessage(conversation_id=conversation_id, sender_id=user.id, content=request.content.strip()); db.add(row); conversation.updated_at = datetime.utcnow(); db.commit(); db.refresh(row)
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
