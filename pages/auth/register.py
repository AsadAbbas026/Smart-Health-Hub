import streamlit as st
from streamlit_autorefresh import st_autorefresh
import datetime
import time
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
    print("\n[DEBUG] show_register() called")
    print("[DEBUG] Current Step:", st.session_state.get("step"))

    # Initialize session state
    if "step" not in st.session_state:
        st.session_state.step = 1
        print("[DEBUG] Initialized step = 1")

    if "otp_sent" not in st.session_state:
        st.session_state.otp_sent = False
        print("[DEBUG] Initialized otp_sent = False")

    if "otp_inputs" not in st.session_state:
        st.session_state.otp_inputs = [""] * 6
        print("[DEBUG] Initialized otp_inputs")

    # ---------------- Step 1: Registration Form ----------------
    if st.session_state.step == 1:
        print("[DEBUG] Rendering Step 1: Registration Form")

        st.write("### Register")
        role = st.radio("Role", ["Patient", "Doctor"], horizontal=True, key="register_role")
        name = st.text_input("Full Name", key="register_name")
        email = st.text_input("Email Address", key="register_email")
        phone = st.text_input("Phone Number (e.g. +923001234567)", key="register_phone")
        gender = st.radio("Gender", ["Male", "Female", "Other"], horizontal=True, key="register_gender")

        dob = None
        if role == "Patient":
            dob = st.date_input(
                "Date of Birth",
                min_value=datetime.date(1900, 1, 1),
                max_value=datetime.date.today(),
                key="register_dob"
            )

        department = specialization = license_number = None
        if role == "Doctor":
            department = st.selectbox(
                "Department",
                ["Select Department"] + list(DEPARTMENT_SPECIALIZATIONS.keys()),
                key="department_specialization"
            )
            if department != "Select Department":
                specialization = st.selectbox(
                    "Specialization",
                    DEPARTMENT_SPECIALIZATIONS[department],
                    key="doctor_specialization"
                )
            license_number = st.text_input("License Number", key="license_number")

        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")

        if st.button("Register", key="register_submit"):
            print("[DEBUG] Register button clicked")
            print(f"[DEBUG] Role: {role}, Email: {email}, Phone: {phone}")

            # Validation
            if not name or not email or not phone or not password or not confirm_password:
                print("[DEBUG] Validation failed: Missing required fields")
                st.error("⚠️ Please fill in all required fields.")
                return

            if password != confirm_password:
                print("[DEBUG] Validation failed: Password mismatch")
                st.error("Passwords do not match.")
                return

            if not validate_email(email):
                print("[DEBUG] Validation failed: Invalid email")
                st.error("Invalid email format.")
                return

            if not validate_password(password):
                print("[DEBUG] Validation failed: Weak password")
                st.error("Password must be at least 8 characters and contain letters and numbers.")
                return

            if not validate_phone_number(phone):
                print("[DEBUG] Validation failed: Invalid phone")
                st.error("Phone number must contain only digits (and may start with '+').")
                return

            if role == "Doctor":
                if department == "Select Department" or specialization is None:
                    print("[DEBUG] Validation failed: Department/Specialization missing")
                    st.error("Please select both Department and Specialization.")
                    return
                if not license_number:
                    print("[DEBUG] Validation failed: License number missing")
                    st.error("License number is required for doctors.")
                    return

            if st.session_state.get("otp_sent"):
                print("[DEBUG] OTP already sent")
                st.info("OTP already sent! Please check your email.")
                return

            # Generate OTP
            otp = generate_otp()
            print(f"[DEBUG] OTP Generated: {otp}")  # ⚠️ REMOVE IN PRODUCTION

            st.session_state.otp = otp
            st.session_state.otp_timestamp = datetime.datetime.now()
            st.session_state.otp_expiry_seconds = 120

            reg_data = {
                "email": email,
                "password": password,
                "role": role.lower(),
                "name": name,
                "phone": phone,
                "gender": gender
            }

            if role == "Patient":
                reg_data["dob"] = str(dob)
            else:
                reg_data.update({
                    "department": department,
                    "specialization": specialization,
                    "license_number": license_number
                })

            print("[DEBUG] Registration Data Prepared (without password):")
            print({k: v for k, v in reg_data.items() if k != "password"})

            st.session_state.reg_data = reg_data

            print("[DEBUG] Sending OTP email...")
            send_otp_email(email, name, otp)

            st.session_state.otp_sent = True
            st.session_state.step = 2

            print("[DEBUG] Moving to Step 2 (OTP Verification)")
            st.rerun()

    # ---------------- Step 2: OTP Verification ----------------
    elif st.session_state.step == 2:
        print("[DEBUG] Rendering Step 2: OTP Verification")

        expiry_time = st.session_state.otp_timestamp + datetime.timedelta(
            seconds=st.session_state.otp_expiry_seconds
        )
        remaining_time = (expiry_time - datetime.datetime.now()).total_seconds()

        if st.button("Submit OTP"):
            print("[DEBUG] Submit OTP clicked")

            otp_input = "".join(
                [st.session_state.get(f"otp_digit_{i}", "") for i in range(6)]
            )

            print(f"[DEBUG] Entered OTP: {otp_input}")
            print(f"[DEBUG] Actual OTP: {st.session_state.otp}")

            if remaining_time <= 0:
                print("[DEBUG] OTP expired")
                st.error("OTP has expired. Please request a new one.")

            elif otp_input == st.session_state.otp:
                print("[DEBUG] OTP matched successfully")

                st.session_state.reg_data["is_verified"] = True

                print("[DEBUG] Calling register_user()")
                success = register_user(st.session_state.reg_data)
                print(f"[DEBUG] register_user() returned: {success}")

                if success:
                    print("[DEBUG] Sending welcome email...")
                    send_welcome_email(
                        st.session_state.reg_data['email'],
                        st.session_state.reg_data['name']
                    )

                    st.session_state.step = 3
                    print("[DEBUG] Moving to Step 3 (Success)")
                    st.rerun()
                else:
                    print("[DEBUG] Registration failed in DB layer")
                    st.error("Registration failed. Email may already exist.")
            else:
                print("[DEBUG] OTP mismatch")
                st.error("Invalid OTP. Please try again.")

    # ---------------- Step 3: Success ----------------
    elif st.session_state.step == 3:
        print("[DEBUG] Rendering Step 3: Registration Success")

        st.success("🎉 Registration successful! You can now login.")
        st.balloons()

        print("[DEBUG] Resetting session state to default")

        st.session_state.step = 1
        st.session_state.otp_sent = False
        st.session_state.otp_inputs = [""] * 6
        st.session_state.reg_data = {}

        st.rerun()
