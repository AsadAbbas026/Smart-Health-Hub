from sqlalchemy.orm import Session
from datetime import datetime
from database.models.MedicalDocument import MedicalDocument
from database.models.Patient import Patient
from database.models.User import User


def get_patient_id_by_email(session: Session, email: str):
    """Return the patient_id for a given user's email."""
    result = (
        session.query(Patient.patient_id)
        .join(User, User.user_id == Patient.user_id)
        .filter(User.email == email)
        .first()
    )
    return result[0] if result else None


def fetch_documents_by_patient(session, patient_id):
    """Fetch all document records for a patient in a tuple-friendly format."""
    records = (
        session.query(
            MedicalDocument.document_id,
            MedicalDocument.document_name,
            MedicalDocument.document_type,
            MedicalDocument.description,
            MedicalDocument.uploaded_at,
            MedicalDocument.category_name,
            MedicalDocument.file_path,
        )
        .filter(MedicalDocument.patient_id == patient_id)
        .order_by(MedicalDocument.uploaded_at.desc())
        .all()
    )
    return records

def insert_document(session: Session, patient_id: int, name: str, doc_type: str, category: str, file_path: str, description: str):
    """Insert a new document for a patient."""
    new_doc = MedicalDocument(
        patient_id=patient_id,
        document_name=name,
        document_type=doc_type,
        category_name=category,
        file_path=file_path,
        description=description,
        uploaded_at=datetime.utcnow()
    )
    session.add(new_doc)
    session.commit()
    return new_doc


def update_document(session: Session, patient_id: int, document_id: int, name: str, doc_type: str, category: str, description: str, file_path: str):
    """Update an existing patient document."""
    doc = (
        session.query(MedicalDocument)
        .filter(
            MedicalDocument.document_id == document_id,
            MedicalDocument.patient_id == patient_id
        )
        .first()
    )

    if not doc:
        return None

    doc.document_name = name
    doc.document_type = doc_type
    doc.category_name = category
    doc.description = description
    doc.file_path = file_path
    doc.uploaded_at = datetime.utcnow()

    session.commit()
    return doc


def delete_documents(session: Session, patient_id: int, document_ids: list[int]):
    """Delete selected documents for a specific patient."""
    (
        session.query(MedicalDocument)
        .filter(
            MedicalDocument.patient_id == patient_id,
            MedicalDocument.document_id.in_(document_ids)
        )
        .delete(synchronize_session=False)
    )
    session.commit()
