import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

from database.connection import SessionLocal
from utils.email_utils import send_cancellation_email, send_reschedule_email, send_cancellation_email_doctor
from database.models.Appointment import Appointment
from database.models.Patient import Patient
from database.models.Doctor import Doctor, DoctorAvailability
from database.models.User import User
from database.models.Treatment import Treatment


# ✅ Get all appointments for a specific patient (properly scoped)
def get_patient_appointments(email: str):
    """Fetch all appointments for a specific patient with full details — safely scoped to that patient only."""
    with SessionLocal() as session:
        # Query appointments linked to the logged-in patient's email only
        appointments = (
            session.query(
                Appointment.patient_appointment_no,
                Appointment.appointment_date,
                Appointment.time_slot,
                Appointment.status,
                Appointment.reference_number,
                Doctor.name.label("doctor_name"),
                Doctor.email.label("doctor_email"),
                Doctor.user_id.label("doctor_id"),
                Patient.user_id.label("patient_id"),
                Treatment.treatment_name.label("treatment_name"),
            )
            .join(Patient, Appointment.patient_id == Patient.patient_id)
            .join(User, Patient.user_id == User.user_id)
            .join(Doctor, Appointment.doctor_id == Doctor.doctor_id)
            .join(Treatment, Appointment.treatment_id == Treatment.treatment_id)
            .filter(User.email == email)
            .order_by(Appointment.appointment_date.asc())
            .all()
        )
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "Appointment ID": appt.patient_appointment_no,
                "Appointment Date": appt.appointment_date.strftime("%Y-%m-%d %H:%M"),
                "Day": appt.appointment_date.strftime("%A"),
                "Time Slot": appt.time_slot,
                "Doctor Name": appt.doctor_name,
                "Doctor ID": appt.doctor_id,
                "Patient ID": appt.patient_id,
                "Status": appt.status,
                "Reference #": appt.reference_number,
                "Treatment Name": appt.treatment_name,
                "Doctor Email": appt.doctor_email,
            }
            for appt in appointments
        ])

        return df

def get_appointments_for_doctor(email: str):
    """Fetch all appointments for a doctor with patient & treatment info (fixed)."""
    with SessionLocal() as session:
        appointments = (
            session.query(Appointment)
            .join(Doctor)
            .join(User)
            .options(
                joinedload(Appointment.patient).joinedload(Patient.user),
                joinedload(Appointment.patient),     # ✅ Preload patient relationship
                joinedload(Appointment.treatment)    # ✅ Preload treatment relationship
            )
            .filter(User.email == email)
            .distinct(Appointment.appointment_id)
            .order_by(Appointment.appointment_id, Appointment.appointment_date)
            .all()
        )
        return appointments

# ✅ Appointment counts summary for doctor dashboard
def get_appointment_counts(doctor_id: int):
    with SessionLocal() as session:
        total = session.query(Appointment).filter(Appointment.doctor_id == doctor_id).count()
        scheduled = session.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "scheduled"
        ).count()
        cancelled = session.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "cancelled"
        ).count()
        return {"total": total, "scheduled": scheduled, "cancelled": cancelled}


# ✅ Appointments grouped by department (for analytics)
def get_appointments_by_department(doctor_id: int):
    with SessionLocal() as session:
        results = (
            session.query(Doctor.department, func.count(Appointment.appointment_id))
            .join(Appointment, Appointment.doctor_id == Doctor.doctor_id)
            .filter(Doctor.doctor_id == doctor_id)
            .group_by(Doctor.department)
            .all()
        )
        return results

# ✅ Create appointment safely
def create_appointment(patient_id: int, doctor_id: int, treatment_id: int,
                       appointment_date: datetime, time_slot: str,
                       reference_number: str = None):
    with SessionLocal() as session:
        try:
            # Validate patient, doctor, and treatment
            patient = session.query(Patient).filter_by(patient_id=patient_id).first()
            doctor = session.query(Doctor).filter_by(doctor_id=doctor_id).first()
            treatment = session.query(Treatment).filter_by(treatment_id=treatment_id).first()

            if not patient:
                return None, "❌ Patient not found."
            if not doctor:
                return None, "❌ Doctor not found."
            if not treatment:
                return None, "❌ Treatment not found."

            # --- 🔹 Determine the next patient appointment number ---
            last_no = (
                session.query(func.max(Appointment.patient_appointment_no))
                .filter(Appointment.patient_id == patient_id)
                .scalar()
            )
            next_no = 1 if last_no is None else last_no + 1

            # --- 🔹 Create the appointment ---
            new_appointment = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                treatment_id=treatment_id,
                appointment_date=appointment_date,
                time_slot=time_slot,
                reference_number=reference_number,
                status="scheduled",
                patient_appointment_no=next_no
            )

            session.add(new_appointment)
            session.commit()
            session.refresh(new_appointment)
            session.close()
            return new_appointment

        except Exception as e:
            session.rollback()
            return f"❌ Error creating appointment: {e}"

def get_available_slots(doctor_id: int, appointment_date: datetime, day_name: str):
    with SessionLocal() as session:
        availabilities = session.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.day_of_week == day_name
        ).all()

        if not availabilities:
            return []  # Doctor not available

        # Generate 30-min slots
        slot_duration = timedelta(minutes=30)
        all_slots = []

        for availability in availabilities:
            start_time = datetime.combine(appointment_date, availability.start_time)
            end_time = datetime.combine(appointment_date, availability.end_time)

            current_start = start_time
            while current_start + slot_duration <= end_time:
                slot_str = f"{current_start.strftime('%H:%M')} - {(current_start + slot_duration).strftime('%H:%M')}"
                all_slots.append(slot_str)
                current_start += slot_duration

        # Fetch already booked slots
        booked_slots = [
            s[0] for s in session.query(Appointment.time_slot)
            .filter(
                Appointment.doctor_id == doctor_id,
                func.date(Appointment.appointment_date) == appointment_date
            ).all()
        ]

        # Return available slots after removing booked ones
        return [slot for slot in all_slots if slot not in booked_slots]


def cancel_appointment(appointment_id: int, patient_id: int):
    """Cancel a patient's appointment and notify the doctor."""
    with SessionLocal() as session:
        appointment = (
            session.query(Appointment)
            .filter(
                Appointment.appointment_id == appointment_id,
                Appointment.patient_id == patient_id
            )
            .first()
        )

        if not appointment:
            return False

        appointment.status = "cancelled"
        session.commit()

        # Optional safety: try sending email but don’t crash system if it fails
        try:
            send_cancellation_email(appointment.doctor.user.email, appointment.appointment_id)
        except Exception as e:
            print(f"[WARN] Failed to send cancellation email: {e}")

        return True
    
def cancel_appointment_doctor(appointment_id: int, patient_id: int = None):
    """Cancel an appointment. If patient_id provided, ensure patient owns it."""
    with SessionLocal() as session:
        query = session.query(Appointment).filter(Appointment.appointment_id == appointment_id)
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        appointment = query.first()

        if not appointment:
            return False

        appointment.status = "cancelled"
        session.commit()

        # send email to patient
        try:
            send_cancellation_email_doctor(appointment.patient.user.email, appointment.reference_number)
        except Exception as e:
            print(f"[WARN] Failed to send cancellation email: {e}")

        return True

def reschedule_appointment(appointment_id: int, patient_id: int, new_date, new_time):
    """Reschedule a patient's appointment and notify the doctor."""
    with SessionLocal() as session:
        appointment = (
            session.query(Appointment)
            .filter(
                Appointment.appointment_id == appointment_id,
                Appointment.patient_id == patient_id
            )
            .first()
        )

        if not appointment:
            return False

        appointment.appointment_date = new_date
        appointment.time_slot = new_time
        appointment.status = "scheduled"
        session.commit()

        # Notify doctor safely
        try:
            send_reschedule_email(
                appointment.doctor.user.email,
                appointment.appointment_id,
                new_date,
                new_time
            )
        except Exception as e:
            print(f"[WARN] Failed to send reschedule email: {e}")

        return True