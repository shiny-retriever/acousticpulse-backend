from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    client_machine_id = Column(Integer, index=True)  # the local Room ID, for matching during sync
    name = Column(String)
    location = Column(String)
    machine_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Baseline(Base):
    __tablename__ = "baselines"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), index=True)
    label = Column(String)
    spectrum_json = Column(Text)  # full FloatArray as JSON, matches Android's format
    created_at = Column(DateTime, default=datetime.utcnow)

class ScanLog(Base):
    __tablename__ = "scan_logs"
    id = Column(Integer, primary_key=True, index=True)
    client_scan_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), index=True)
    baseline_id = Column(Integer, ForeignKey("baselines.id"))
    anomaly_score = Column(Float)
    anomaly_label = Column(String)
    rms_energy = Column(Float)
    dominant_frequency_hz = Column(Float)
    scanned_at = Column(DateTime, default=datetime.utcnow)