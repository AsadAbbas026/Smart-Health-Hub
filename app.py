import streamlit as st
from streamlit_cookies_manager import encrypted_cookie_manager
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

from pages.util.menu import patient_sidebar, doctor_sidebar
from database.create_tables import create_tables

load_dotenv()
st.set_page_config(page_title="Smart Health Hub", layout="wide")

# -----------------------------
# Initialize cookies
# -----------------------------
cookies = encrypted_cookie_manager.EncryptedCookieManager(
    prefix="smart_health_hub_",
    password=os.getenv("ENCRYPTED_COOKIE_KEY", "default_key")
)
if not cookies.ready():
    st.stop()

# -----------------------------
# Initialize database
# -----------------------------
@st.cache_resource
def initialize_database():
    create_tables()
initialize_database()

# -----------------------------
# Logout function
# -----------------------------
def handle_logout():
    # Clear all relevant session keys
    keys_to_clear = [
        "user",
        "page",
        "page_override",
        "auth_tab",
        "last_selected",
        "page_index",
        "patient_sidebar_widget",
        "doctor_sidebar_widget"
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)

    # Clear cookies
    for key in cookies.keys():
        del cookies[key]
    cookies.save()

    # Clear query params
    st.query_params.clear()

    # Force the app to auth page
    st.session_state.user = None
    st.session_state.page = "auth"
    st.rerun()


# -----------------------------
# Helper to update last page
# -----------------------------
def update_last_page(page_key):
    st.session_state.page = page_key
    if st.session_state.user:
        cookies["last_page"] = page_key


# -----------------------------
# Auth screens
# -----------------------------
def show_auth_screens():
    col1, _, col3 = st.columns([0.45, 0.05, 0.50])
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

        if "auth_tab" not in st.session_state:
            st.session_state.auth_tab = "Login"

        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab:
            show_login(cookies)
        with register_tab:
            show_register()


# -----------------------------
# Patient pages
# -----------------------------
def show_patient_pages():
    selected_label = patient_sidebar() if st.session_state.user else None
    if selected_label == "Logout":
        handle_logout()
        return

    page_map = {
        "Chats": "chat_dashboard",
        "Dashboard": "patient_dashboard",
        "Book Appointment": "book_appointment",
        "Your Appointments": "your_appointments",
        "Health Records": "health_records",
        "Prescriptions": "prescriptions",
        "Profile": "profile"
    }

    page_to_render = page_map.get(selected_label, st.session_state.page)
    st.session_state.page = page_to_render  # update session
    update_last_page(page_to_render)        # save last page

    pages = {
        "chat_dashboard": "pages.patient.chat_dashboard.show_chat_dashboard",
        "patient_dashboard": "pages.patient.dashboard.show_dashboard",
        "book_appointment": "pages.patient.book_appointment.show_book_appointment",
        "your_appointments": "pages.patient.your_appointment.show_your_appointments",
        "health_records": "pages.patient.documents.show_documents",
        "prescriptions": "pages.patient.prescriptions.show_prescriptions",
        "profile": "pages.patient.profile.show_patient_profile"
    }

    if page_to_render == "chat_dashboard":
        user = st.session_state.get("user")
        if user:
            uid = user["uid"]
            role = user["role"]

            if role == "patient":
                from pages.patient.chat_dashboard import fetch_recent_chats
                if "recent_chats" not in st.session_state:
                    st.session_state.recent_chats = fetch_recent_chats(uid)

    if page_to_render in pages:
        module_path, func_name = pages[page_to_render].rsplit(".", 1)
        mod = __import__(module_path, fromlist=[func_name])
        getattr(mod, func_name)()

# -----------------------------
# Doctor pages
# -----------------------------
def show_doctor_pages():
    selected_label = doctor_sidebar() if st.session_state.user else None
    if selected_label == "Logout":
        handle_logout()
        return

    page_map = {
        "Chats": "chat_dashboard",
        "Dashboard": "doctor_dashboard",
        "Schedule": "schedule",
        "Appointments": "appointments",
        "Treatments": "treatments",
        "Shared Documents": "shared_documents",
        "Prescriptions": "prescriptions",
        "Profile": "profile"
    }

    page_to_render = page_map.get(selected_label, st.session_state.page)
    st.session_state.page = page_to_render  # update session
    update_last_page(page_to_render)        # save last page

    pages = {
        "chat_dashboard": "pages.doctor.chat_dashboard.show_chat_dashboard",
        "doctor_dashboard": "pages.doctor.dashboard.show_doctor_dashboard",
        "schedule": "pages.doctor.schedule.show_schedule",
        "appointments": "pages.doctor.appointments.show_appointments",
        "treatments": "pages.doctor.treatment.show_treatments",
        "shared_documents": "pages.doctor.share_documents.show_shared_documents",
        "prescriptions": "pages.doctor.prescriptions.show_prescriptions",
        "profile": "pages.doctor.profile.show_profile"
    }

    if page_to_render == "chat_dashboard":
        user = st.session_state.get("user")
        if user:
            uid = user["uid"]
            role = user["role"]

            if role == "doctor":
                from pages.doctor.chat_dashboard import fetch_recent_chats
                if "recent_chats" not in st.session_state:
                    st.session_state.recent_chats = fetch_recent_chats(uid)

    if page_to_render in pages:
        module_path, func_name = pages[page_to_render].rsplit(".", 1)
        mod = __import__(module_path, fromlist=[func_name])
        getattr(mod, func_name)()


# -----------------------------
# Main app
# -----------------------------
def main():
    # --- Load user and last page from cookie first ---
    user_cookie = cookies.get("user")
    last_page_cookie = cookies.get("last_page")

    if user_cookie:
        try:
            st.session_state.user = json.loads(user_cookie)
        except:
            st.session_state.user = None
    else:
        st.session_state.user = None

    # --- Set initial page ---
    if "page" not in st.session_state:
        if st.session_state.user:
            role = st.session_state.user["role"]
            if role == "patient":
                st.session_state.page = last_page_cookie or "patient_dashboard"
            elif role == "doctor":
                st.session_state.page = last_page_cookie or "doctor_dashboard"
            else:
                st.session_state.page = "auth"
        else:
            st.session_state.page = "auth"

    user = st.session_state.get("user", None)

    # --- Render auth or dashboards ---
    if not user or st.session_state.page == "auth":
        show_auth_screens()
    elif user["role"] == "patient":
        show_patient_pages()
    elif user["role"] == "doctor":
        show_doctor_pages()
    else:
        st.error("Invalid role")
        st.session_state.page = "auth"
        st.query_params.clear()
        st.rerun()

    # -----------------------------
    # Save cookies ONCE at the very end
    # -----------------------------
    if st.session_state.user:
        cookies.save()


if __name__ == "__main__":
    main()
