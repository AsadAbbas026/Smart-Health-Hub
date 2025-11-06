from sqlalchemy.orm import Session, joinedload
from database.models.Prescription import Prescription
from database.models.Patient import Patient
from database.models.Doctor import Doctor
from database.models.User import User
from database.models.Appointment import Appointment
from datetime import datetime


# -------------------------------
# 🧠 PATIENT QUERIES
# -------------------------------
def get_prescriptions_for_patient(session: Session, email: str):
    """
    Return all prescriptions for a given patient's email.
    Includes doctor and patient relationship data.
    """
    return (
        session.query(Prescription)
        .join(Prescription.patient)
        .join(Patient.user)
        .filter(User.email == email)
        .options(
            joinedload(Prescription.doctor),
            joinedload(Prescription.patient)
        )
        .order_by(Prescription.created_at.desc())
        .all()
    )


# -------------------------------
# 🧠 DOCTOR QUERIES
# -------------------------------
def get_prescriptions_for_doctor(session: Session, email: str):
    """
    Return all prescriptions created by a given doctor (via email).
    Includes patient and doctor relationship data.
    """
    return (
        session.query(Prescription)
        .join(Prescription.doctor)
        .join(Doctor.user)
        .filter(User.email == email)
        .options(
            joinedload(Prescription.doctor),
            joinedload(Prescription.patient)
        )
        .order_by(Prescription.created_at.desc())
        .all()
    )


# -------------------------------
# 💊 CREATE NEW PRESCRIPTION
# -------------------------------
def create_prescription(session: Session, appointment_id: int, doctor_id: int, medication_name: str, dosage: str, duration: str):
    """
    Create a new prescription based on an appointment and mark appointment as completed.
    """
    # Fetch appointment record
    appointment = session.query(Appointment).filter_by(appointment_id=appointment_id).first()
    if not appointment:
        raise ValueError("Appointment not found")

    # Create prescription record
    new_prescription = Prescription(
        patient_id=appointment.patient_id,
        doctor_id=doctor_id,
        medication_name=medication_name,
        dosage=dosage,
        duration=duration,
        created_at=datetime.now(),
    )

    # Add and commit
    session.add(new_prescription)
    appointment.status = "completed"
    session.commit()
    session.refresh(new_prescription)

    return new_prescription


# -------------------------------
# 📋 FETCH VALID APPOINTMENTS FOR PRESCRIPTION CREATION
# -------------------------------
def get_valid_appointments_for_doctor(session: Session, doctor_id: int):
    """
    Return all appointments for a doctor that are pending (not completed or cancelled).
    """
    return (
        session.query(Appointment)
        .join(Appointment.patient)
        .filter(Appointment.doctor_id == doctor_id)
        .filter(Appointment.status.notin_(["cancelled", "completed"]))
        .order_by(Appointment.appointment_date.asc())
        .all()
    )


# -------------------------------
# 🔍 FETCH SINGLE PRESCRIPTION BY ID
# -------------------------------
def get_prescription_by_id(session: Session, prescription_id: int):
    """
    Fetch a specific prescription record by ID.
    """
    return (
        session.query(Prescription)
        .options(
            joinedload(Prescription.doctor),
            joinedload(Prescription.patient)
        )
        .filter(Prescription.prescription_id == prescription_id)
        .first()
    )


# -------------------------------
# 🗑️ DELETE PRESCRIPTION (optional)
# -------------------------------
def delete_prescription(session: Session, prescription_id: int):
    """
    Delete a prescription record from the database.
    """
    prescription = session.query(Prescription).filter_by(prescription_id=prescription_id).first()
    if not prescription:
        raise ValueError("Prescription not found")

    session.delete(prescription)
    session.commit()
    return True
