from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Time, func
from sqlalchemy.orm import relationship
from database.connection import Base

class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    email = Column(String(255), unique=True, nullable=False)
    department = Column(String(100))
    specialization = Column(String(100))
    license_number = Column(String(50), unique=True, nullable=False)
    gender = Column(String(20))
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="doctor", uselist=False)
    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")
    treatments = relationship("Treatment", back_populates="doctor", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="doctor", cascade="all, delete-orphan")
    shared_documents = relationship("SharedDocument", back_populates="doctor")


    def __repr__(self):
        return f"<Doctor(name={self.name}, specialization={self.specialization}, license_number={self.license_number})>"

class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"
    availability_id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.doctor_id"), nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    doctor = relationship("Doctor", backref="availability")