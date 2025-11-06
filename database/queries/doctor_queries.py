from database.connection import SessionLocal
from database.models.Doctor import Doctor  # adjust the import path as per your structure
from database.models.User import User
from database.models.Treatment import Treatment
from utils.hash_utils import hash_password

def insert_doctor_local(uid, name, email, phone=None, department=None, specialization=None, license_no=None, gender=None):
    """Insert a new doctor into the local database."""
    session = SessionLocal()
    try:
        doctor = Doctor(
            user_id=uid,
            name=name,
            phone_number=phone,
            email=email,
            department=department,
            specialization=specialization,
            license_number=license_no,
            gender=gender
        )
        session.add(doctor)
        session.commit()
        print(f"✅ Doctor {name} successfully added.")
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error inserting doctor locally: {e}")
        return False
    finally:
        session.close()

def get_doctor_by_email(email: str):
    session = SessionLocal()
    try:
        doctor = (
            session.query(Doctor)
            .join(User, Doctor.user_id == User.user_id)
            .filter(User.email == email)
            .first()
        )
        return doctor
    finally:
        session.close()

# ✅ Doctor utilities
def get_doctors(specialization: str = None):
    with SessionLocal() as session:
        query = session.query(Doctor)
        if specialization:
            query = query.filter(Doctor.specialization == specialization)
        return query.all()


# ✅ Get treatments by doctor
def get_treatments_by_doctor(doctor_id: int):
    with SessionLocal() as session:
        return (
            session.query(Treatment)
            .filter(Treatment.doctor_id == doctor_id)
            .all()
        )


# ✅ Get doctor email by ID
def get_doctor_email(doctor_id: int):
    with SessionLocal() as session:
        doctor = (
            session.query(User.email)
            .join(Doctor, Doctor.user_id == User.user_id)
            .filter(Doctor.doctor_id == doctor_id)
            .first()
        )
        return doctor.email if doctor else None

def get_doctor_profile(email: str):
    """Fetch a doctor's profile based on their email (using ORM)."""
    session = SessionLocal()
    try:
        doctor = (
            session.query(Doctor)
            .join(User)
            .filter(User.email == email)
            .first()
        )
        if doctor:
            return {
                "name": doctor.name,
                "phone": doctor.phone_number,
                "department": doctor.department,
                "specialization": doctor.specialization,
                "license": doctor.license_number,
            }
        return None
    finally:
        session.close()


def update_doctor_profile(email: str, name: str, phone: str, department: str, specialization: str, license_number: str, password: str = None):
    """Update doctor profile information (using ORM)."""
    session = SessionLocal()
    try:
        doctor = (
            session.query(Doctor)
            .join(User)
            .filter(User.email == email)
            .first()
        )
        if not doctor:
            raise ValueError("Doctor not found.")

        # Update profile fields
        doctor.name = name
        doctor.phone_number = phone
        doctor.department = department
        doctor.specialization = specialization
        doctor.license_number = license_number

        # Optional password update
        if password:
            doctor.user.password_hash = hash_password(password)

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()