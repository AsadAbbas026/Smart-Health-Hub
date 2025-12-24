import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv

load_dotenv()

def init_firebase():
    if firebase_admin._apps:
        return

    cred_path = os.getenv(
        "FIREBASE_CREDENTIALS_PATH",
        "/etc/secrets/firebase-service-account.json"
    )

    cred = credentials.Certificate(cred_path)

    firebase_admin.initialize_app(cred, {
        "databaseURL": os.getenv("DATABASE_URL")
    })

def get_chat_ref(patient_id, doctor_id):
    return db.reference(f"chats/{patient_id}/{doctor_id}/messages")
