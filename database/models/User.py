# database/models/users.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from datetime import datetime
from database.connection import Base
import enum
from sqlalchemy.orm import relationship

class UserRole(enum.Enum):
    patient = "patient"
    doctor = "doctor"

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(255), primary_key=True, unique=True, nullable=False)
    name = Column(String(255), unique=False, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

     # ✅ Add this relationship for doctors
    doctor = relationship("Doctor", back_populates="user", uselist=False)

    # ✅ And optionally for patients too
    patient = relationship("Patient", backref="user", uselist=False)

    def __repr__(self):
        return f"<User {self.email}>"
