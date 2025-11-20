import streamlit as st
from datetime import date, datetime
from utils.email_utils import send_appointment_confirmation
from utils.pdf_generator import generate_admit_card
from database.queries.appointment_queries import (
    create_appointment,
    get_available_slots
)
from database.queries.patient_queries import get_patient_by_email
from database.queries.doctor_queries import get_doctor_email, get_treatments_by_doctor, get_doctors
from database.queries.share_document_queries import share_documents_with_doctor

import uuid

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

def show_book_appointment():
    user = st.session_state.get("user", None)
    if not user or user["role"] != "patient":
        st.error("Please log in as a patient.")
        return

    st.header("Book Appointment", divider="gray")

    # Session setup
    if "step" not in st.session_state: st.session_state.step = 1
    if "form_data" not in st.session_state: st.session_state.form_data = {}

    steps = ["Select Specialization", "Select Doctor", "Select Date & Slot", "Select Treatment", "Confirm Appointment", "Admit Card"]

    # --- STEP 1: Select Specialization ---
    if st.session_state.step == 1:
        st.subheader(steps[0])
        specs = [s for dep in DEPARTMENT_SPECIALIZATIONS.values() for s in dep]
        specialization = st.selectbox("Select Specialization", specs)
        if st.button("Next"):
            st.session_state.form_data["specialization"] = specialization
            st.session_state.step = 2
            st.rerun()

    # --- STEP 2: Select Doctor ---
    elif st.session_state.step == 2:
        st.subheader(steps[1])
        specialization = st.session_state.form_data.get("specialization")
        doctors = get_doctors(specialization)
        doctor_map = {f"{d.name} - {d.specialization}": d.doctor_id for d in doctors}
        doctor = st.selectbox("Select Doctor", list(doctor_map.keys()))
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.step = 1
                st.rerun()
        with col2:
            if st.button("Next"):
                st.session_state.form_data.update({"doctor_name": doctor, "doctor_id": doctor_map[doctor]})
                st.session_state.step = 3
                st.rerun()

    # --- STEP 3: Select Date and Slot ---
    elif st.session_state.step == 3:
        st.subheader(steps[2])
        doctor_id = st.session_state.form_data.get("doctor_id")
        appt_date = st.date_input("Appointment Date", min_value=date.today())
        if appt_date:
            slots = get_available_slots(doctor_id, appt_date, appt_date.strftime("%A"))
            
            if slots and isinstance(slots[0], str):
                slot_options = slots
            else:
                slot_options = [
                    f"{s[1]} {s[2].strftime('%H:%M')} - {s[3].strftime('%H:%M')}"
                    for s in slots
                ]

            slot = st.selectbox("Select Time Slot", slot_options)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.step = 2
                st.rerun()
        with col2:
            if st.button("Next"):
                st.session_state.form_data.update({"appointment_date": appt_date, "slot": slot})
                st.session_state.step = 4
                st.rerun()

    # --- STEP 4: Select Treatment ---
    elif st.session_state.step == 4:
        st.subheader(steps[3])
        doctor_id = st.session_state.form_data.get("doctor_id")
        treatments = get_treatments_by_doctor(doctor_id)
        treatment_map = {t.treatment_name: t.treatment_id for t in treatments}
        treatment = st.selectbox("Select Treatment", list(treatment_map.keys()))

        details = next((t for t in treatments if t.treatment_name == treatment), None)

        if details:
            st.write(f"**Cost:** ${details.cost}  \n**Description:** {details.description}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Back"):
                st.session_state.step = 3
                st.rerun()
        with col2:
            if st.button("Next"):
                st.session_state.form_data.update({"treatment_name": treatment, "treatment_id": treatment_map[treatment]})
                st.session_state.step = 5
                st.rerun()

    # --- STEP 5: Confirm Details ---
    elif st.session_state.step == 5:
        st.subheader(steps[4])
        patient = get_patient_by_email(user["email"])
        patient_id, name, phone, dob, gender = patient.patient_id, patient.name, patient.phone_number, patient.date_of_birth, patient.gender
        
        st.write(f"**Doctor:** {st.session_state.form_data['doctor_name']}  \n**Treatment:** {st.session_state.form_data['treatment_name']}  \n**Date:** {st.session_state.form_data['appointment_date']}  \n**Slot:** {st.session_state.form_data['slot']}")
        if st.button("Book Appointment"):
            ref = str(uuid.uuid4())[:8]
            doctor_id = st.session_state.form_data["doctor_id"]
            treatment_id = st.session_state.form_data["treatment_id"]
            appointment_date = st.session_state.form_data["appointment_date"]
            slot = st.session_state.form_data["slot"]

            appointment = create_appointment(patient_id, doctor_id, treatment_id, appointment_date, slot, ref)
            print("Created Appointment:", appointment)
            # Share patient's documents with the doctor
            appointment_id = appointment.appointment_id
            print("Appointment ID:", appointment_id)

            # ✅ 2. Share patient's existing documents with the doctor
            share_documents_with_doctor(
                appointment_id=appointment_id,
                patient_id=patient_id,
                doctor_id=doctor_id
            )
            doctor_email = get_doctor_email(st.session_state.form_data["doctor_id"])
            if doctor_email:
                send_appointment_confirmation(
                    user["email"],
                    doctor_email,
                    name,
                    30,  # age placeholder
                    gender,
                    phone,
                    st.session_state.form_data["doctor_name"],
                    st.session_state.form_data["appointment_date"],
                    st.session_state.form_data["slot"],
                    ref,
                )
            else:
                st.warning("⚠️ Could not find doctor's email for notification.")

            st.session_state.form_data["reference_number"] = ref
            st.success(f"Appointment booked successfully! Reference No: {ref}")
            st.session_state.step = 6
            st.rerun()

    # --- STEP 6: Generate Admit Card ---
    elif st.session_state.step == 6:
        st.subheader(steps[5])
        pdf_path = generate_admit_card(st.session_state.form_data)
        with open(pdf_path, "rb") as f:
            st.download_button("Download Admit Card", f, file_name=pdf_path, mime="application/pdf")
        if st.button("Finish"):
            st.session_state.step = 1
            st.session_state.form_data = {}
            st.rerun()
