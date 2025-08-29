from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    vin = Column(String(32), unique=True, index=True, nullable=False)
    model = Column(String(64), nullable=False)
    docs = relationship("QualityDoc", back_populates="vehicle")

class DPCRecord(Base):
    __tablename__ = "dpc_records"
    id = Column(Integer, primary_key=True)
    vin = Column(String(32), index=True, nullable=False)
    model = Column(String(64), nullable=False)
    date = Column(Date, index=True, nullable=False)
    dpc_target = Column(Float, nullable=False)
    dpc_actual = Column(Float, nullable=False)

class RSPRecord(Base):
    __tablename__ = "rsp_records"
    id = Column(Integer, primary_key=True)
    date = Column(Date, index=True, nullable=False)
    target = Column(Float, nullable=False)
    actual = Column(Float, nullable=False)

class QualityDoc(Base):
    __tablename__ = "quality_docs"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    title = Column(String(128), nullable=False)
    type = Column(String(32), nullable=False)
    path = Column(Text, nullable=False)  # relative to data/docs
    uploaded_at = Column(DateTime)
    vehicle = relationship("Vehicle", back_populates="docs")
