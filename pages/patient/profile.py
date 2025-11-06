# pages/patient_profile.py
import streamlit as st
from utils.validators import validate_password
from database.queries.patient_queries import get_patient_profile,  update_patient_profile

def show_patient_profile():
    """UI for managing patient profile."""
    user = st.session_state.get('user', None)
    if not user or user["role"] != "patient":
        st.error("Please log in as a patient to access this page.")
        st.session_state.page = "auth"
        st.rerun()
        return

    st.header("Manage Profile", divider="gray")

    try:
        patient = get_patient_profile(user["email"])
        print(patient)
    except Exception as e:
        st.error(f"Error fetching profile: {e}")
        return

    with st.container(border=True):
        st.write("##### Update Profile")
        with st.form("patient_profile_form", border=False):
            name = st.text_input("Name", value=patient["name"] if patient else "")
            phone = st.text_input("Phone Number", value=patient["phone"] if patient else "")
            dob = st.date_input("Date of Birth", value=patient["dob"] if patient else None)
            email = st.text_input("Email", value=user["email"], disabled=True)
            password = st.text_input("New Password (leave blank to keep current)", type="password")
            submit = st.form_submit_button("Update Profile")

            if submit:
                if not name:
                    st.error("Name is required.")
                elif password and not validate_password(password):
                    st.error("Password must be at least 8 characters with a letter, number, and special character.")
                else:
                    try:
                        update_patient_profile(name, phone, dob, user["email"], password or None)
                        st.success("Profile updated successfully!")
                    except Exception as e:
                        st.error(f"Error updating profile: {e}")

