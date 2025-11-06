import streamlit as st
import datetime
from utils.auth_utils import register_user
from utils.validators import validate_email, validate_password, validate_phone_number
from utils.email_utils import send_welcome_email, send_otp_email
from utils.otp_utils import generate_otp

DEPARTMENT_SPECIALIZATIONS = {
    "Cardiology": ["Interventional Cardiology", "Electrophysiology", "Heart Failure", "Pediatric Cardiology"],
    "Neurology": ["Stroke", "Epilepsy", "Neuromuscular", "Pediatric Neurology"],
    "Orthopedics": ["Joint Replacement", "Sports Medicine", "Spine Surgery", "Pediatric Orthopedics"],
    "Pediatrics": ["Neonatology", "Pediatric Oncology", "Pediatric Cardiology", "Developmental Pediatrics"],
    "General Surgery": ["Trauma Surgery", "Laparoscopic Surgery", "Colorectal Surgery", "Vascular Surgery"],
    "Oncology": ["Medical Oncology", "Surgical Oncology", "Radiation Oncology", "Pediatric Oncology"],
    "Gastroenterology": ["Hepatology", "Endoscopy", "Pediatric Gastroenterology"],
    "Pulmonology": ["Asthma", "Critical Care", "Sleep Medicine", "Pediatric Pulmonology"],
    "Endocrinology": ["Diabetes", "Thyroid Disorders", "Pediatric Endocrinology"],
    "Nephrology": ["Dialysis", "Transplant Nephrology", "Pediatric Nephrology"],
    "Urology": ["Urologic Oncology", "Pediatric Urology", "Endourology"],
    "Ophthalmology": ["Cataract Surgery", "Retina", "Glaucoma", "Pediatric Ophthalmology"],
    "Otolaryngology": ["Head and Neck Surgery", "Otology", "Rhinology"],
    "Dermatology": ["Cosmetic Dermatology", "Pediatric Dermatology", "Mohs Surgery"],
    "Psychiatry": ["Child Psychiatry", "Addiction Psychiatry", "Geriatric Psychiatry"],
    "Anesthesiology": ["Pain Management", "Cardiac Anesthesia", "Pediatric Anesthesia"],
    "Radiology": ["Diagnostic Radiology", "Interventional Radiology", "Nuclear Medicine"],
    "Pathology": ["Clinical Pathology", "Anatomic Pathology", "Forensic Pathology"],
    "Emergency Medicine": ["Trauma", "Pediatric Emergency Medicine"],
    "Obstetrics and Gynecology": ["Maternal-Fetal Medicine", "Gynecologic Oncology", "Reproductive Endocrinology"],
    "Infectious Disease": ["HIV/AIDS", "Tropical Medicine", "Pediatric Infectious Disease"],
    "Rheumatology": ["Autoimmune Diseases", "Pediatric Rheumatology"],
    "Physical Medicine and Rehabilitation": ["Sports Rehabilitation", "Spinal Cord Injury"],
    "Hematology": ["Hemophilia", "Bone Marrow Transplant", "Pediatric Hematology"],
    "Allergy and Immunology": ["Pediatric Allergy", "Immunodeficiency"]
}


def show_register():
    if "step" not in st.session_state: st.session_state.step = 1
    if st.session_state.step == 1:
        st.write("### Register")

        role = st.radio("Role", ["Patient", "Doctor"], horizontal=True, key="register_role")
        name = st.text_input("Full Name", key="register_name")
        email = st.text_input("Email Address", key="register_email")
        phone = st.text_input("Phone Number (e.g. +923001234567)", key="register_phone")
        gender = st.radio("Gender", ["Male", "Female", "Other"], horizontal=True, key="register_gender")

        # Patient fields
        if role == "Patient":
            dob = st.date_input(
                "Date of Birth",
                key="register_dob",
                min_value=datetime.date(1900, 1, 1),
                max_value=datetime.date.today()
            )

        # Doctor fields
        else:
            department = st.selectbox("Department", ["Select Department"] + list(DEPARTMENT_SPECIALIZATIONS.keys()), key="department_specialization")
            specialization = None
            if department != "Select Department":
                specialization = st.selectbox("Specialization", DEPARTMENT_SPECIALIZATIONS[department], key="doctor_specialization")
            license_number = st.text_input("License Number", key="license_number")

        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")

        if st.button("Register", key="register_submit", icon="🤵"):
            # 1️⃣ Validate required fields
            if not name or not email or not phone or not password or not confirm_password:
                st.error("⚠️ Please fill in all required fields.")
                return

            # 2️⃣ Validate password match
            if password != confirm_password:
                st.error("Passwords do not match.")
                return

            # 3️⃣ Validate email
            if not validate_email(email):
                st.error("Invalid email format.")
                return

            # 4️⃣ Validate password strength
            if not validate_password(password):
                st.error("Password must be at least 8 characters and contain both letters and numbers.")
                return

            # 5️⃣ Validate phone number
            if not validate_phone_number(phone):
                st.error("Phone number must contain only digits (and may start with '+').")
                return
            otp = generate_otp()
            st.session_state.otp = otp
            st.session_state.reg_data = {
                "name": name,
                "email": email,
                "password": password,
                "role": role.lower()
            }
            # 6️⃣ For doctors: ensure department & specialization are selected
            if role == "Doctor":
                if department == "Select Department" or specialization is None:
                    st.error("Please select both Department and Specialization.")
                    return
                if not license_number:
                    st.error("License number is required for doctors.")
                    return

            # 7️⃣ Prepare data for registration
            data = {
                "email": email,
                "password": password,
                "role": role.lower(),
                "name": name,
                "phone": phone,
                "gender": gender
            }

            if role == "Patient":
                data.update({"dob": str(dob)})
            else:
                data.update({
                    "department": department,
                    "specialization": specialization,
                    "license_number": license_number
                })

            send_otp_email(email, name, otp)
            st.session_state.otp_sent = True
            st.session_state.step = 2

    elif st.session_state.step == 2:
        st.header("Enter OTP")
        st.write(f"An OTP has been sent to {st.session_state.reg_data['email']}")

        # Initialize OTP input state
        if "otp_inputs" not in st.session_state:
            st.session_state.otp_inputs = [""] * 6

        # 6 boxes for OTP
        cols = st.columns(6)
        for i, col in enumerate(cols):
            st.session_state.otp_inputs[i] = col.text_input(
                "", value=st.session_state.otp_inputs[i], max_chars=1, key=f"otp_{i}"
            )

        otp_input = "".join(st.session_state.otp_inputs)

        # "Not your email?" clickable text
        if st.button("Not your email?", key="not_your_email_btn"):
            # Reset OTP step
            st.session_state.otp_sent = False
            st.session_state.otp = ""
            st.session_state.reg_data = {}
            st.session_state.otp_inputs = [""] * 6
            st.session_state.step = 1

        if st.button("Submit OTP"):
            if otp_input == st.session_state.otp:
                # ✅ OTP verified, now register user
                data = st.session_state.reg_data
                data.update({"is_verified": True})
                if register_user(data):
                    st.success("✅ Registration Successful! You can now login.")
                else:
                    st.error("Registration failed. Email may already exist.")
                # Reset session state
                st.session_state.otp_sent = False
                st.session_state.otp = ""
                st.session_state.reg_data = {}
                st.session_state.otp_inputs = [""] * 6
                st.session_state.step = 1
            else:
                st.error("Invalid OTP. Please try again.")

