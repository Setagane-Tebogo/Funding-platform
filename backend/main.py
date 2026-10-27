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
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/funding_platform"
    jwt_secret: str = "change-this-production-secret-to-a-long-random-value"
    frontend_url: str = "http://localhost:5173"
    xai_model: str = "grok-4"
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
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    business_stage: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    funding_needed: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    intended_use_of_funds: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FunderOrganisation(Base):
    __tablename__ = "funder_organisations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    organisation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organisation_type: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(100))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


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


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=8)
    role: Optional[str] = None


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


class AnalysisRequest(BaseModel):
    startupCosts: Decimal
    monthlyRevenue: Decimal
    monthlyExpenses: Decimal
    monthlyGrowthPercent: Decimal = Decimal("0")


class ApplicationRequest(BaseModel):
    programmeId: int
    proposal: str


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
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:5174"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/", include_in_schema=False)
def root():
    return {"name": "FundBridge API", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/register")
def register(request: RegisterRequest, db: Session = Depends(db_session)):
    email = request.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(name=request.name.strip(), email=email, password=hash_password(request.password), role="ENTREPRENEUR")
    db.add(user); db.commit(); db.refresh(user)
    return user_response(user)


@app.post("/api/auth/login")
def login(request: LoginRequest, db: Session = Depends(db_session)):
    user = db.scalar(select(User).where(User.email == request.email.strip().lower()))
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": make_token(user), **user_response(user)}


@app.get("/api/entrepreneur/dashboard")
def entrepreneur_dashboard(user: User = Depends(require_role("ENTREPRENEUR"))):
    return f"Welcome to the Entrepreneur Dashboard, {user.email}"


@app.post("/api/entrepreneur/business-profile", status_code=201)
def create_profile(request: ProfileRequest, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    if db.scalar(select(BusinessProfile).where(BusinessProfile.user_id == user.id)):
        raise HTTPException(status_code=400, detail="Business profile already exists")
    profile = BusinessProfile(user_id=user.id, business_name=request.businessName, industry=request.industry, business_stage=request.businessStage, description=request.description, location=request.location, funding_needed=request.fundingNeeded, intended_use_of_funds=request.intendedUseOfFunds)
    db.add(profile); db.commit(); db.refresh(profile)
    return profile_response(profile)


@app.get("/api/entrepreneur/business-profile")
def get_profile(user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.user_id == user.id))
    if not profile: raise HTTPException(status_code=404, detail="Business profile not found")
    return profile_response(profile)


@app.put("/api/entrepreneur/business-profile")
def update_profile(request: ProfileRequest, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.user_id == user.id))
    if not profile: raise HTTPException(status_code=404, detail="Business profile not found")
    for key, value in {"business_name": request.businessName, "industry": request.industry, "business_stage": request.businessStage, "description": request.description, "location": request.location, "funding_needed": request.fundingNeeded, "intended_use_of_funds": request.intendedUseOfFunds}.items(): setattr(profile, key, value)
    db.commit(); db.refresh(profile)
    return profile_response(profile)


def profile_response(profile: BusinessProfile) -> dict[str, Any]:
    return {"id": profile.id, "businessName": profile.business_name, "industry": profile.industry, "businessStage": profile.business_stage, "description": profile.description, "location": profile.location, "fundingNeeded": profile.funding_needed, "intendedUseOfFunds": profile.intended_use_of_funds, "createdAt": profile.created_at, "updatedAt": profile.updated_at}


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
async def analyse(request: AnalysisRequest, user: User = Depends(require_role("ENTREPRENEUR"))):
    if min(request.startupCosts, request.monthlyRevenue, request.monthlyExpenses) < 0: raise HTTPException(status_code=400, detail="Financial values cannot be negative.")
    profit = request.monthlyRevenue - request.monthlyExpenses
    break_even = int((request.startupCosts / profit).to_integral_value(rounding="ROUND_CEILING")) if profit > 0 else None
    outlook = "Potentially profitable" if profit > 0 else "Break-even only" if profit == 0 else "Needs improvement"
    summary = "Your projected revenue is higher than your projected monthly expenses." if profit > 0 else "Your current projection covers operating costs but does not recover startup costs." if profit == 0 else "Your projected monthly expenses are higher than your projected revenue."
    result = {"outlook": outlook, "summary": summary, "estimatedBreakEvenMonths": break_even, "estimatedMonthlyProfit": profit, "estimatedAnnualProfit": profit * 12, "monthlyExpenses": request.monthlyExpenses, "confidence": "Medium" if profit > 0 else "Low", "disclaimer": "This is an advisory estimate based only on the figures you entered. It is not a funding or profit guarantee."}
    result["aiAssessment"] = await grok_assessment(request, result)
    result["aiProvider"] = "grok" if result["aiAssessment"] else "deterministic-fallback"
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
        result.append({"id": row.id, "programmeName": programme.programme_name if programme else "Unknown programme", "proposal": row.proposal, "status": row.status, "createdAt": row.created_at})
    return result


@app.post("/api/entrepreneur/applications", status_code=201)
def submit_application(request: ApplicationRequest, user: User = Depends(require_role("ENTREPRENEUR")), db: Session = Depends(db_session)):
    programme = db.scalar(select(FundingProgramme).where(FundingProgramme.id == request.programmeId, FundingProgramme.active.is_(True)))
    if not programme: raise HTTPException(status_code=404, detail="Active funding programme not found.")
    row = FundingApplication(entrepreneur_id=user.id, programme_id=programme.id, proposal=request.proposal.strip(), status="SUBMITTED")
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "programmeName": programme.programme_name, "proposal": row.proposal, "status": row.status, "createdAt": row.created_at}


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


@app.get("/api/funder/programmes")
def my_programmes(user: User = Depends(require_role("FUNDER")), db: Session = Depends(db_session)):
    organisation = db.scalar(select(FunderOrganisation).where(FunderOrganisation.user_id == user.id))
    if not organisation: raise HTTPException(status_code=404, detail="Organisation profile not found")
    rows = db.scalars(select(FundingProgramme).where(FundingProgramme.organisation_id == organisation.id)).all()
    return [programme_response(row, organisation.organisation_name) for row in rows]


@app.get("/api/test/protected")
def protected_test(user: User = Depends(current_user)):
    return f"Authenticated successfully as: {user.email}"

