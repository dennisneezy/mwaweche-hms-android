"""Secure API foundation for Mwaeche HMS. Not yet a full HMS backend."""
import os, uuid, secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from sqlalchemy import create_engine, String, Integer, Boolean, DateTime, Text, select, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

JWT_SECRET = os.environ.get("MWAECHE_JWT_SECRET", "")
DATABASE_URL = os.environ.get("MWAECHE_DATABASE_URL", "")
SERVER_ID = os.environ.get("MWAECHE_SERVER_ID", "")
if len(JWT_SECRET) < 32:
    raise RuntimeError("Set MWAECHE_JWT_SECRET to a strong random secret of at least 32 characters")
if not DATABASE_URL.startswith("postgresql+psycopg://"):
    raise RuntimeError("Configure MWAECHE_DATABASE_URL with PostgreSQL; SQLite is not supported for this server")
if not SERVER_ID:
    SERVER_ID = str(uuid.uuid4())
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "api_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
class Patient(Base):
    __tablename__ = "api_patient_summaries"
    patient_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(250))
    patient_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
class ProcessedMutation(Base):
    __tablename__ = "processed_mutations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mutation_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(100))
    outcome: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
Base.metadata.create_all(engine)
app = FastAPI(title="Mwaeche HMS API", version="0.1.0")

class LoginIn(BaseModel): username: str = Field(min_length=1, max_length=100); password: str = Field(min_length=1, max_length=256)
class MutationIn(BaseModel):
    mutation_id: str
    entity_type: str
    entity_id: str
    operation: str
    payload: dict[str, str]
    base_version: int = Field(ge=0)

def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()
def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(db_session)) -> User:
    if not creds: raise HTTPException(401, "Authentication required")
    try:
        claims = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"], options={"require": ["sub", "exp"]})
        uid = int(claims["sub"])
    except Exception: raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, uid)
    if not user or not user.active: raise HTTPException(401, "Account disabled or not found")
    return user

def require_roles(*roles):
    def check(user: User = Depends(current_user)):
        if user.role not in roles: raise HTTPException(403, "Your account is not permitted to perform this action")
        return user
    return check

@app.get("/api/health")
def health():
    return {"application":"Mwaeche HMS", "server_id":SERVER_ID, "server_name":os.environ.get("MWAECHE_SERVER_NAME", "Mwaeche HMS Mother Server"), "status":"ready"}

@app.post("/api/auth/login")
def login(body: LoginIn, db: Session = Depends(db_session)):
    user = db.scalar(select(User).where(User.username == body.username))
    # Verify against a dummy hash on missing users to reduce username timing leaks.
    if not user or not user.active or not password_hash.verify(body.password, user.password_hash):
        raise HTTPException(401, "Invalid username or password")
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    token = jwt.encode({"sub":str(user.id), "role":user.role, "exp":exp, "jti":secrets.token_urlsafe(16)}, JWT_SECRET, algorithm="HS256")
    return {"access_token":token, "token_type":"Bearer", "expires_in":900, "role":user.role}

@app.get("/api/patients")
def patients(q: str = "", user: User = Depends(current_user), db: Session = Depends(db_session)):
    if user.role not in {"Administrator", "Doctor", "Nurse", "Receptionist", "Laboratory", "Pharmacist", "Accountant"}:
        raise HTTPException(403, "Role cannot access patient summaries")
    stmt = select(Patient).where(Patient.full_name.ilike(f"%{q}%")).limit(100)
    return [{"patient_id":p.patient_id,"full_name":p.full_name,"patient_type":p.patient_type,"version":p.version} for p in db.scalars(stmt)]

@app.post("/api/sync/mutations")
def sync_mutation(body: MutationIn, user: User = Depends(current_user), db: Session = Depends(db_session)):
    """Demo conflict-safe sync for patient demographics only. No clinical/financial offline writes."""
    if body.entity_type != "patient_demographics" or body.operation != "update":
        raise HTTPException(422, "This mutation type is not enabled for offline sync")
    if user.role not in {"Administrator", "Receptionist"}:
        raise HTTPException(403, "Role cannot update patient demographics")
    try: uuid.UUID(body.mutation_id)
    except ValueError: raise HTTPException(422, "mutation_id must be a UUID")
    prior = db.scalar(select(ProcessedMutation).where(ProcessedMutation.mutation_id == body.mutation_id))
    if prior: return {"mutation_id":body.mutation_id,"status":prior.outcome,"message":"Already processed; safe retry"}
    patient = db.get(Patient, body.entity_id)
    if not patient: raise HTTPException(404, "Patient not found")
    if patient.version != body.base_version:
        return {"mutation_id":body.mutation_id,"status":"conflict","server_version":patient.version,"message":"Record changed on server; review before retrying"}
    allowed = {"full_name", "patient_type"}
    if not body.payload or set(body.payload) - allowed:
        raise HTTPException(422, "Only full_name and patient_type may be changed by this offline demo")
    if "full_name" in body.payload: patient.full_name = body.payload["full_name"][:250]
    if "patient_type" in body.payload: patient.patient_type = body.payload["patient_type"][:50]
    patient.version += 1; patient.updated_at = datetime.now(timezone.utc)
    db.add(ProcessedMutation(mutation_id=body.mutation_id, entity_type=body.entity_type, entity_id=body.entity_id, outcome="applied"))
    db.commit()
    return {"mutation_id":body.mutation_id,"status":"applied","server_version":patient.version}

@app.get("/api/admin/status")
def admin_status(user: User = Depends(require_roles("Administrator"))):
    return {"status":"ok", "message":"Administrator authenticated"}
