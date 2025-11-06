# services/document_utils.py
import os
from datetime import datetime

UPLOAD_DIR = "Uploads"

def save_uploaded_file(patient_id, document_name, uploaded_file):
    """Save uploaded file to the Uploads directory and return the file path."""
    ext = uploaded_file.name.split(".")[-1]
    file_path = os.path.join(UPLOAD_DIR, str(patient_id), f"{document_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path
