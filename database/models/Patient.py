from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.connection import Base

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")

    # ✅ keep only this one
    medical_documents = relationship("MedicalDocument", back_populates="patient", cascade="all, delete-orphan")

    # ✅ shared documents for sharing with doctors
    shared_documents = relationship("SharedDocument", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient {self.name}>"
