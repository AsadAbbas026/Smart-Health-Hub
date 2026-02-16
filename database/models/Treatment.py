from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database.connection import Base

class Treatment(Base):
    __tablename__ = "treatments"

    treatment_id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    treatment_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cost = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    doctor = relationship("Doctor", back_populates="treatments")
    appointments = relationship("Appointment", back_populates="treatment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Treatment(id={self.treatment_id}, name={self.treatment_name}, doctor_id={self.doctor_id})>"
