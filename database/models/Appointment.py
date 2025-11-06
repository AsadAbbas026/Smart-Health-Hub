from sqlalchemy import Column, Integer, String, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from database.connection import Base

class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id = Column(Integer, primary_key=True, autoincrement=True)  # Global unique ID
    patient_id = Column(Integer, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    treatment_id = Column(Integer, ForeignKey("treatments.treatment_id", ondelete="SET NULL"))

    patient_appointment_no = Column(Integer, nullable=False)

    appointment_date = Column(TIMESTAMP, nullable=False)
    time_slot = Column(String(50), nullable=False)
    reference_number = Column(String(50), unique=True, nullable=False)
    status = Column(String(50), default="scheduled")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        UniqueConstraint("doctor_id", "appointment_date", "time_slot", name="unique_doctor_timeslot"),
        UniqueConstraint("patient_id", "patient_appointment_no", name="unique_patient_appointment_no"),
    )

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    treatment = relationship("Treatment", back_populates="appointments")
    shared_documents = relationship("SharedDocument", back_populates="appointment")

    def __repr__(self):
        return f"<Appointment(global_id={self.appointment_id}, local_no={self.patient_appointment_no}, patient={self.patient_id}, doctor={self.doctor_id}, date={self.appointment_date}, time={self.time_slot})>"
