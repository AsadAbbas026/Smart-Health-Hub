# database/queries/patients_queries.py
from database.connection import SessionLocal
from database.models.Patient import Patient
from database.models.User import User
from utils.hash_utils import hash_password
from datetime import datetime

def insert_patient_local(uid, name, phone=None, dob=None, gender=None):
    session = SessionLocal()
    try:
        patient = Patient(
            user_id=uid,
            name=name,
            phone_number=phone,
            date_of_birth=dob,
            gender=gender
        )
        session.add(patient)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error inserting patient locally: {e}")
        return False
    finally:
        session.close()

def get_patient_by_user_id(user_id: str):
    session = SessionLocal()
    try:
        patient = session.query(Patient).filter(Patient.user_id == user_id).first()
        return patient
    except Exception as e:
        print(f"❌ Error fetching patient by user_id: {e}")
        return None
    finally:
        session.close()

def get_patient_profile(email: str):
    session = SessionLocal()
    try:
        patient = session.query(Patient).join(User).filter(User.email == email).first()
        if patient:
            return {"name": patient.name, "phone": patient.phone_number, "dob": patient.date_of_birth}
        return None
    finally:
        session.close()

# ✅ Patient utilities
def get_patient_by_email(email: str):
    with SessionLocal() as session:
        patient = (
            session.query(Patient)
            .join(User, Patient.user_id == User.user_id)
            .filter(User.email == email)
            .first()
        )
        return patient

def update_patient_profile(name, phone, dob, email, password=None):
        session = SessionLocal()
        try:
            # Step 1: Fetch the User and related Patient record
            user = session.query(User).filter(User.email == email).first()
            if not user:
                raise Exception("User not found.")
            
            patient = session.query(Patient).filter(Patient.user_id == user.user_id).first()
            if not patient:
                raise Exception("Patient profile not found.")
            
            # Step 2: Update fields
            patient.name = name
            patient.phone_number = phone
            patient.date_of_birth = dob
            session.add(patient)

            # Step 3: Update password if provided
            if password:

                user.password_hash = hash_password(password)
                session.add(user)

            # Step 4: Commit transaction
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()