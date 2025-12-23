import firebase_admin
from firebase_admin import credentials, db, storage
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(os.path.join("config", "smart-health-hub-93ab1-firebase-adminsdk-fbsvc-7bec0b6390.json"))
        firebase_admin.initialize_app(cred, {
            "databaseURL": os.getenv("DATABASE_URL")
        })

def get_chat_ref(patient_id, doctor_id):
    return db.reference(f"chats/{patient_id}/{doctor_id}/messages")

