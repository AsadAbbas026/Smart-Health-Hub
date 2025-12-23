# database/queries/shared_documents_queries.py
from database.models import SharedDocument
from database.models import MedicalDocument
from database.models import Patient
from database.models import Appointment
from datetime import datetime

from database.connection import SessionLocal

def share_documents_with_doctor(appointment_id: int, patient_id: int, doctor_id: int):
    """Share all patient's documents with the selected doctor for this appointment."""
    from database.models import MedicalDocument
    db = SessionLocal()
    documents = db.query(MedicalDocument).filter(MedicalDocument.patient_id == patient_id).all()

    for doc in documents:
        shared = SharedDocument(
            appointment_id=appointment_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            document_id=doc.document_id,
            shared_on=datetime.utcnow()
        )
        db.add(shared)
    db.commit()


def get_shared_documents_for_doctor(doctor_id: int):
    """Fetch all documents shared with a particular doctor, including appointment reference numbers."""
    db = SessionLocal()
    result = (
        db.query(
            SharedDocument.id.label("shared_id"),
            Patient.name.label("patient_name"),
            MedicalDocument.document_name,
            MedicalDocument.document_type,
            MedicalDocument.category_name,
            MedicalDocument.description,
            MedicalDocument.file_path,
            SharedDocument.doctor_id,
            Appointment.reference_number  # <-- include reference number
        )
        .join(MedicalDocument, SharedDocument.document_id == MedicalDocument.document_id)
        .join(Patient, SharedDocument.patient_id == Patient.patient_id)
        .join(Appointment, SharedDocument.appointment_id == Appointment.appointment_id)  # <-- join
        .filter(SharedDocument.doctor_id == doctor_id)
        .all()
    )
    db.close()
    return result

