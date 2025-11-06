# database/models/shared_documents.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database.connection import Base

class SharedDocument(Base):
    __tablename__ = "shared_documents"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.appointment_id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id"), nullable=False)
    document_id = Column(Integer, ForeignKey("medical_documents.document_id"), nullable=False)
    shared_on = Column(DateTime, default=datetime.utcnow)

    # Relationships (optional, for joined queries)
    appointment = relationship("Appointment", back_populates="shared_documents")
    patient = relationship("Patient", back_populates="shared_documents")
    doctor = relationship("Doctor", back_populates="shared_documents")
    document = relationship("MedicalDocument", back_populates="shared_documents")