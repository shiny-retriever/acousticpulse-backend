from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from database import engine, Base, SessionLocal
from auth import hash_password, verify_password, create_access_token, get_current_user_email
import models

app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(email: str = Depends(get_current_user_email), db: Session = Depends(get_db)) -> models.User:
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ---- AUTH ----
class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    new_user = models.User(email=data.email, hashed_password=hash_password(data.password))
    db.add(new_user)
    db.commit()
    return {"status": "account created"}

@app.post("/auth/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# ---- MACHINES ----
class MachineRequest(BaseModel):
    client_machine_id: int
    name: str
    location: str
    machine_type: str

@app.post("/machines")
def create_machine(data: MachineRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    existing = db.query(models.Machine).filter(
        models.Machine.user_id == user.id,
        models.Machine.client_machine_id == data.client_machine_id
    ).first()
    if existing:
        return {"machine_id": existing.id, "status": "already exists"}

    new_machine = models.Machine(
        user_id=user.id,
        client_machine_id=data.client_machine_id,
        name=data.name,
        location=data.location,
        machine_type=data.machine_type
    )
    db.add(new_machine)
    db.commit()
    db.refresh(new_machine)
    return {"machine_id": new_machine.id, "status": "created"}

@app.get("/machines")
def get_machines(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    machines = db.query(models.Machine).filter(models.Machine.user_id == user.id).all()
    return [
        {
            "id": m.id,
            "client_machine_id": m.client_machine_id,
            "name": m.name,
            "location": m.location,
            "machine_type": m.machine_type
        }
        for m in machines
    ]

# ---- CALIBRATE ----
class CalibrateRequest(BaseModel):
    machine_id: int
    label: str
    spectrum_json: str

@app.post("/calibrate")
def calibrate(data: CalibrateRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    new_baseline = models.Baseline(
        user_id=user.id,
        machine_id=data.machine_id,
        label=data.label,
        spectrum_json=data.spectrum_json
    )
    db.add(new_baseline)
    db.commit()
    db.refresh(new_baseline)
    return {"baseline_id": new_baseline.id, "status": "stored"}

@app.get("/calibrate")
def get_baselines(machine_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    baselines = db.query(models.Baseline).filter(
        models.Baseline.machine_id == machine_id,
        models.Baseline.user_id == user.id
    ).all()
    return [
        {"id": b.id, "machine_id": b.machine_id, "label": b.label, "spectrum_json": b.spectrum_json}
        for b in baselines
    ]

# ---- DIAGNOSE (batch sync) ----
class ScanEntry(BaseModel):
    client_scan_id: str
    machine_id: int
    baseline_id: int
    anomaly_score: float
    anomaly_label: str
    rms_energy: float
    dominant_frequency_hz: float

class DiagnoseSyncRequest(BaseModel):
    entries: List[ScanEntry]

@app.post("/diagnose")
def sync_scans(data: DiagnoseSyncRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    accepted = 0
    duplicates = 0
    for entry in data.entries:
        new_scan = models.ScanLog(
            client_scan_id=entry.client_scan_id,
            user_id=user.id,
            machine_id=entry.machine_id,
            baseline_id=entry.baseline_id,
            anomaly_score=entry.anomaly_score,
            anomaly_label=entry.anomaly_label,
            rms_energy=entry.rms_energy,
            dominant_frequency_hz=entry.dominant_frequency_hz
        )
        db.add(new_scan)
        try:
            db.commit()
            accepted += 1
        except IntegrityError:
            db.rollback()
            duplicates += 1
    return {"accepted": accepted, "duplicates_skipped": duplicates}

@app.get("/diagnose")
def get_scans(machine_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    scans = db.query(models.ScanLog).filter(
        models.ScanLog.machine_id == machine_id,
        models.ScanLog.user_id == user.id
    ).all()
    return [
        {
            "client_scan_id": s.client_scan_id,
            "machine_id": s.machine_id,
            "baseline_id": s.baseline_id,
            "anomaly_score": s.anomaly_score,
            "anomaly_label": s.anomaly_label,
            "rms_energy": s.rms_energy,
            "dominant_frequency_hz": s.dominant_frequency_hz
        }
        for s in scans
    ]