from sqlalchemy.orm import Session
from database.models.Treatment import Treatment
from database.models.Doctor import Doctor
from database.models.User import User

# --- CREATE ---
def add_treatment(session: Session, doctor_id: int, name: str, description: str, cost: float):
    treatment = Treatment(
        doctor_id=doctor_id,
        treatment_name=name,
        description=description,
        cost=cost
    )
    session.add(treatment)
    session.commit()
    session.refresh(treatment)
    return treatment


# --- READ ---
def get_treatments_by_doctor(session: Session, doctor_id: int):
    return session.query(Treatment).filter_by(doctor_id=doctor_id).all()


# --- UPDATE ---
def update_treatment(session: Session, treatment_id: int, doctor_id: int, name: str, description: str, cost: float):
    treatment = session.query(Treatment).filter_by(treatment_id=treatment_id, doctor_id=doctor_id).first()
    if not treatment:
        return None
    treatment.treatment_name = name
    treatment.description = description
    treatment.cost = cost
    session.commit()
    session.refresh(treatment)
    return treatment


# --- DELETE ---
def delete_treatments(session: Session, doctor_id: int, treatment_ids: list[int]):
    session.query(Treatment).filter(
        Treatment.treatment_id.in_(treatment_ids),
        Treatment.doctor_id == doctor_id
    ).delete(synchronize_session=False)
    session.commit()
