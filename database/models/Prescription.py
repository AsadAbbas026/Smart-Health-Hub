# models/prescription.py
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database.connection import Base


class Prescription(Base):
    __tablename__ = "prescriptions"

    prescription_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id", ondelete="SET NULL"))
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id", ondelete="SET NULL"))
    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=False)
    duration = Column(String(100))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")
