import firebase_admin
from firebase_admin import credentials, auth, db
from dotenv import load_dotenv
import os
import datetime
import requests
from requests.exceptions import RequestException

from utils.hash_utils import hash_password, verify_password

from database.queries.user_queries import insert_user_local, get_user_by_email
from database.queries.patient_queries import insert_patient_local, get_patient_by_user_id
from database.queries.doctor_queries import insert_doctor_local

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

CONFIG_PATH = os.path.join("config", "smart-health-hub-93ab1-firebase-adminsdk-fbsvc-7bec0b6390.json")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

if firebase_admin._apps:
    for app in list(firebase_admin._apps.values()):
        firebase_admin.delete_app(app)

cred = credentials.Certificate(CONFIG_PATH)
firebase_admin.initialize_app(cred, {
    'databaseURL': DATABASE_URL
})

def register_user(data):
    try:
        user = auth.create_user(
            email=data["email"],
            password=data["password"],
            phone_number=f"+{data['phone']}" if data["phone"] else None
        )
        uid = user.uid

        user_data = {
            "uid": uid,
            "email": data["email"],
            "name": data["name"],
            "role": data["role"],
            "gender": data["gender"],
            "phone": data["phone"],
            "dob": str(data.get("dob", "")),
            "department": data.get("department", ""),
            "specialization": data.get("specialization", ""),
            "license_number": data.get("license_number", ""),
            "created_at": str(datetime.datetime.now())
        }

        db.reference(f"users/{uid}").set(user_data)

        insert_user_local(uid, data["email"], hash_password(data['password']), data['name'], data["role"])
        
        if data["role"] == "patient":
            insert_patient_local(
                uid,
                data["name"],
                phone=data.get("phone"),
                dob=data.get("dob"),
                gender=data.get("gender")
            )
        elif data["role"] == "doctor":
            insert_doctor_local(
                uid,
                data["name"],
                email=data["email"],
                phone=data.get("phone"),
                department=data.get("department"),
                specialization=data.get("specialization"),
                license_no=data.get("license_number"),
            )

        return True

    except Exception as e:
        print(f"❌ Error in register_user: {e}")
        return False

def authenticate_user(email, password):
    # --- Try Firebase first ---
    try:
        payload = {"email": email, "password": password, "returnSecureToken": True}
        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
            json=payload,
            timeout=3  # short timeout
        )
        response.raise_for_status()  # raise exception for HTTP errors

        user_info = response.json()
        uid = user_info.get("localId")
        print("✅ Firebase authentication successful for UID:", uid)
        user_data = db.reference(f"users/{uid}").get()
        return user_data

    except RequestException as e:  # catches connection errors, DNS errors, timeouts
        print("⚠️ Firebase offline or network error, falling back to local:", e)
    except Exception as e:
        print("⚠️ Firebase auth failed, falling back to local:", e)

    # --- Local PostgreSQL auth ---
    try:
        user = get_user_by_email(email)
        if not user:
            print("❌ User not found locally")
            return None

        if not verify_password(password, user.password_hash):
            print("❌ Invalid password locally")
            return None

        print("✅ Local authentication successful for UID:", user.user_id)

        patient_data = None
        if user.role.value == "patient":
            patient_data = get_patient_by_user_id(user.user_id)

        return {
            "uid": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "patient_data": patient_data
        }

    except Exception as e:
        print(f"❌ Error in local auth: {e}")
        return None