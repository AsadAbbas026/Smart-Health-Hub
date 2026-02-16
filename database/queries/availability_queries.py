from database.connection import SessionLocal
from sqlalchemy import and_
from database.models.Doctor import Doctor, DoctorAvailability  # Assuming ORM models are defined here
from database.models.User import User

def get_doctor_id_by_email(email):
    session = SessionLocal()
    try:
        doctor = (
            session.query(Doctor)
            .join(User, Doctor.user_id == User.user_id)
            .filter(User.email == email)
            .first()
        )
        return doctor.doctor_id if doctor else None
    except Exception as e:
        print(f"[ORM ERROR] get_doctor_id_by_email: {e}")
        return None
    finally:
        session.close()


def get_doctor_slots(doctor_id):
    session = SessionLocal()
    try:
        slots = (
            session.query(DoctorAvailability)
            .filter(DoctorAvailability.doctor_id == doctor_id)
            .all()
        )
        return [
            (
                s.availability_id,
                s.day_of_week,
                s.start_time.strftime("%I:%M %p") if s.start_time else None,
                s.end_time.strftime("%I:%M %p") if s.end_time else None
            )
            for s in slots
        ]

    except Exception as e:
        print(f"[ORM ERROR] get_doctor_slots: {e}")
        return []
    finally:
        session.close()


def add_doctor_availability(doctor_id, days, start_time, end_time):
    session = SessionLocal()
    try:
        for day in days:
            slot = DoctorAvailability(
                doctor_id=doctor_id,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time
            )
            session.add(slot)
        session.commit()
        return True, "Availability slots added successfully!"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def update_doctor_availability(doctor_id, availability_id, days, start_time, end_time):
    session = SessionLocal()
    try:
        session.query(DoctorAvailability).filter(
            and_(
                DoctorAvailability.availability_id == availability_id,
                DoctorAvailability.doctor_id == doctor_id
            )
        ).delete()

        for day in days:
            new_slot = DoctorAvailability(
                doctor_id=doctor_id,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time
            )
            session.add(new_slot)

        session.commit()
        return True, "Availability slot updated successfully!"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def delete_doctor_availability(doctor_id, availability_ids):
    session = SessionLocal()
    try:
        session.query(DoctorAvailability).filter(
            and_(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.availability_id.in_(availability_ids)
            )
        ).delete(synchronize_session=False)
        session.commit()
        return True, "Availability slots deleted successfully!"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()
