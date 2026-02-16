# database/models/document_model.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database.connection import Base

class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    document_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), nullable=False)
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(100))
    category_name = Column(String(100))
    description = Column(Text)
    file_path = Column(String(500))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="medical_documents")

    # ✅ if shared with doctors, link via shared_documents table
    shared_documents = relationship("SharedDocument", back_populates="document")