import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import os
import json
from dotenv import load_dotenv

from pages.auth.login import show_login
from pages.auth.register import show_register

from pages.doctor.dashboard import show_doctor_dashboard
from pages.doctor.schedule import show_schedule
from pages.doctor.treatment import show_treatments
from pages.doctor.appointments import show_appointments
from pages.doctor.profile import show_profile
from pages.doctor.share_documents import show_shared_documents

from database.create_tables import create_tables
from pages.util.menu import patient_sidebar, doctor_sidebar

import notifications

load_dotenv()

st.set_page_config(page_title="Smart Health Hub", layout="wide")

# -------------------------------------------------
# Setup and initial configs
# -------------------------------------------------
st.markdown(
    """
    <script>
    window.uploadBaseURL = "http://localhost:8501/Uploads/";
    </script>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
        .st-emotion-cache-6awftf {display: none;}
        .st-emotion-cache-gi0tri {display: none;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

cookies = EncryptedCookieManager(
    prefix="smart_health_hub_",
    password=os.getenv("ENCRYPTED_COOKIE_KEY", "default_key")  # store safely, don’t hardcode in production
)
if not cookies.ready():
    st.stop()

create_tables()

# -------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------
def main():
    # --- Initialize session state ---
    if "page" not in st.session_state:
        st.session_state.page = "auth"
        st.session_state.user = None
        st.session_state.registration_success = False
        st.session_state.last_selected = None

    # --- Load user from cookie if session is empty ---
    if not st.session_state.user:
        user_cookie = cookies.get("user")
        last_page_cookie = cookies.get("last_page")
        if user_cookie:
            try:
                st.session_state.user = json.loads(user_cookie)
                # Restore last page if available
                if last_page_cookie:
                    st.session_state.page = last_page_cookie
            except Exception:
                st.session_state.user = None

    user = st.session_state.get("user", None)

    # --- Handle logout ---
    if st.session_state.page == "logout":
        st.session_state.user = None
        st.session_state.page = "auth"
        st.session_state.registration_success = False
        st.query_params.clear()
        if "last_page" in cookies:
            cookies.delete("last_page")
        st.rerun()

    # --- Sync query params if provided in URL ---
    query_page = st.query_params.get("page", [None])[0]
    if query_page and query_page != st.session_state.page:
        st.session_state.page = query_page

    # -------------------------------------------------
    # AUTH SCREENS
    # -------------------------------------------------
    if not user or st.session_state.page == "auth":
        col1, col2, col3 = st.columns([0.45, 0.05, 0.50])
        with col1:
            st.image(
                "assets/images/healthy-people-carrying-different-icons_53876-66139.png",
                width=700
            )
        with col3:
            st.markdown(
                "<h1 style='font-size: 3rem; margin-bottom: -10px;'>Smart Health Hub 🧑‍⚕️</h1>",
                unsafe_allow_html=True
            )
            login_tab, register_tab = st.tabs(["Login", "Register"])
            with login_tab:
                show_login(cookies)
            with register_tab:
                show_register()
                if st.session_state.get("registration_success", False):
                    st.session_state.page = "auth"
                    st.session_state.registration_success = False
                    st.rerun()
        return

    # -------------------------------------------------
    # DASHBOARDS
    # -------------------------------------------------
    role = user["role"].lower()

    # Helper to update last page in cookies
    def update_last_page(page_key):
        st.session_state.page = page_key
        if user:
            cookies["last_page"] = page_key

    # -------------------------------------------------
    # PATIENT ROUTES
    # -------------------------------------------------
    if role == "patient":
        selected = patient_sidebar()
        page_map = {
            "Chats": "chat_dashboard",
            "Dashboard": "patient_dashboard",
            "Book Appointment": "book_appointment",
            "Your Appointments": "your_appointments",
            "Health Records": "health_records",
            "Prescriptions": "prescriptions",
            "Profile": "profile",
            "Logout": "logout",
        }

        selected_page = page_map.get(selected, st.session_state.page)
        if st.session_state.page != selected_page:
            update_last_page(selected_page)

        # Render patient page
        if st.session_state.page == "chat_dashboard":
            from pages.patient.chat_dashboard import show_chat_dashboard
            show_chat_dashboard()
        elif st.session_state.page == "patient_dashboard":
            from pages.patient.dashboard import show_dashboard
            show_dashboard()
        elif st.session_state.page == "book_appointment":
            from pages.patient.book_appointment import show_book_appointment
            show_book_appointment()
        elif st.session_state.page == "your_appointments":
            from pages.patient.your_appointment import show_your_appointments
            show_your_appointments()
        elif st.session_state.page == "health_records":
            from pages.patient.documents import show_documents
            show_documents()
        elif st.session_state.page == "prescriptions":
            from pages.patient.prescriptions import show_prescriptions
            show_prescriptions()
        elif st.session_state.page == "profile":
            from pages.patient.profile import show_patient_profile
            show_patient_profile()
        elif st.session_state.page == "logout":
            update_last_page("auth")
            st.session_state.user = None
            st.query_params.clear()
            st.rerun()

    # -------------------------------------------------
    # DOCTOR ROUTES
    # -------------------------------------------------
    elif role == "doctor":
        selected = doctor_sidebar()
        page_map = {
            "Chats": "chat_dashboard",
            "Dashboard": "doctor_dashboard",
            "Schedule": "schedule",
            "Appointments": "appointments",
            "Treatments": "treatments",
            "Shared Documents": "shared_documents",
            "Prescriptions": "prescriptions",
            "Profile": "profile",
            "Logout": "logout",
        }

        selected_page = page_map.get(selected, st.session_state.page)
        if st.session_state.page != selected_page:
            update_last_page(selected_page)

        # Render doctor page
        if st.session_state.page == "chat_dashboard":
            from pages.doctor.chat_dashboard import show_chat_dashboard
            show_chat_dashboard()
        elif st.session_state.page == "doctor_dashboard":
            show_doctor_dashboard()
        elif st.session_state.page == "schedule":
            show_schedule()
        elif st.session_state.page == "appointments":
            show_appointments()
        elif st.session_state.page == "treatments":
            show_treatments()
        elif st.session_state.page == "shared_documents":
            show_shared_documents()
        elif st.session_state.page == "prescriptions":
            from pages.doctor.prescriptions import show_prescriptions
            show_prescriptions()
        elif st.session_state.page == "profile":
            show_profile()
        elif st.session_state.page == "logout":
            update_last_page("auth")
            st.session_state.user = None
            st.query_params.clear()
            st.rerun()

    # -------------------------------------------------
    # INVALID ROLE
    # -------------------------------------------------
    else:
        st.error("Invalid user role.")
        update_last_page("auth")
        st.query_params.clear()
        st.rerun()
    
    if user:
        cookies.save()

if __name__ == "__main__":
    main()
