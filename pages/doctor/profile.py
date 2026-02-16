# pages/doctor/profile.py
import streamlit as st
from pages.util.menu import doctor_sidebar
from utils.validators import validate_password
from database.queries.doctor_queries import get_doctor_profile, update_doctor_profile

def show_profile():
    """Doctor Profile Page."""
    user = st.session_state.get("user", None)

    if not user or user["role"] != "doctor":
        st.error("Please log in as a doctor to access this page.")
        st.session_state.page = "auth"
        st.rerun()
        return

    # Fetch doctor data
    try:
        doctor = get_doctor_profile(user["email"])
    except Exception as e:
        st.error(f"Error fetching profile: {e}")
        return

    # --- UI ---
    st.header("Manage Profile", divider="gray")

    with st.container(border=True):
        st.write("##### Update Profile")
        with st.form("doctor_profile_form", border=False):
            name = st.text_input("Name", value=doctor["name"] if doctor else "")
            phone = st.text_input("Phone Number", value=doctor["phone"] if doctor else "")
            department = st.text_input("Department", value=doctor["department"] if doctor else "", disabled=True)
            specialization = st.text_input("Specialization", value=doctor["specialization"] if doctor else "", disabled=True)
            license_number = st.text_input("License Number", value=doctor["license"] if doctor else "", disabled=True)
            email = st.text_input("Email", value=user["email"], disabled=True)
            password = st.text_input("New Password (leave blank to keep current)", type="password")

            submit = st.form_submit_button("Update Profile")

            if submit:
                if not name or not license_number:
                    st.error("Name and License Number are required.")
                elif password and not validate_password(password):
                    st.error("Password must be at least 8 characters with a letter, number, and special character.")
                else:
                    try:
                        update_doctor_profile(
                            email=user["email"],
                            name=name,
                            phone=phone,
                            department=department,
                            specialization=specialization,
                            license_number=license_number,
                            password=password if password else None
                        )
                        st.success("Profile updated successfully!")
                    except Exception as e:
                        st.error(f"Error updating profile: {e}")
