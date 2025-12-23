import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
from pages.util.menu import doctor_sidebar
from database.connection import SessionLocal
from database.queries.prescription_queries import get_prescriptions_for_doctor, create_prescription, get_valid_appointments_for_doctor
from database.models.Doctor import Doctor

def clear_inputs():
    # Only clear if they exist to be safe, although in this context they should
    if "medication_input" in st.session_state:
        st.session_state.medication_input = ""
    if "dosage_input" in st.session_state:
        st.session_state.dosage_input = ""
    if "duration_input" in st.session_state:
        st.session_state.duration_input = ""

# New function to handle the 'Add More' logic
def add_medication():
    medication = st.session_state.medication_input
    dosage = st.session_state.dosage_input
    duration = st.session_state.duration_input
    
    if medication and dosage and duration:
        st.session_state.medications.append({
            "medication": medication,
            "dosage": dosage,
            "duration": duration
        })
        # Clear the inputs via the function
        st.success("Medication added!")
        clear_inputs()

def show_prescriptions():
    """Doctor prescription dashboard page"""
    user = st.session_state.get("user")
    if not user or user.get("role") != "doctor":
        st.error("Please log in as a doctor to access this page.")
        st.session_state.page = "auth"
        st.rerun()
        return

    st.header("Prescriptions", divider="gray")

    with SessionLocal() as session:
        doctor = session.query(Doctor).filter(Doctor.user.has(email=user["email"])).first()
        if not doctor:
            st.error("Doctor profile not found.")
            return

        # Fetch prescriptions
        prescriptions = get_prescriptions_for_doctor(session, user["email"])
        if prescriptions:
            df = pd.DataFrame(
                [
                    {
                        "Prescription ID": p.prescription_id,
                        "Medication": p.medication_name,
                        "Dosage": p.dosage,
                        "Duration": p.duration,
                        "Created At": p.created_at,
                        "Patient": p.patient.name if p.patient else "N/A",
                    }
                    for p in prescriptions
                ]
            )

            cols = st.columns(3)
            with cols[0]:
                patient_counts = df["Patient"].value_counts().reset_index()
                patient_counts.columns = ["Patient", "Count"]
                st.plotly_chart(px.bar(patient_counts, x="Patient", y="Count", title="Prescriptions by Patient"), use_container_width=True)

            with cols[1]:
                df["Created Date"] = pd.to_datetime(df["Created At"]).dt.date
                date_counts = df["Created Date"].value_counts().reset_index()
                date_counts.columns = ["Date", "Count"]
                st.plotly_chart(px.line(date_counts, x="Date", y="Count", title="Prescriptions Over Time"), use_container_width=True)

            with cols[2]:
                df["Status"] = df["Created At"].apply(
                    lambda x: "Active" if (x.tz_localize(None) + pd.Timedelta(days=30)) > datetime.now() else "Expired"
                )
                status_counts = df["Status"].value_counts().reset_index()
                status_counts.columns = ["Status", "Count"]
                st.plotly_chart(px.pie(status_counts, names="Status", values="Count", title="Prescription Status"), use_container_width=True)

            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
            gb.configure_default_column(groupable=True, value=True, enableRowGroup=True)
            grid_options = gb.build()
            AgGrid(df, gridOptions=grid_options, height=700, width='100%', fit_columns_on_grid_load=True)
        else:
            st.info("No prescriptions found.")

        st.divider()
        if st.button("Generate New Prescription"):
            st.session_state.show_prescription_form = not st.session_state.get("show_prescription_form", False)
            st.rerun()

        if st.session_state.get("show_prescription_form"):
            appointments = get_valid_appointments_for_doctor(session, doctor.doctor_id)
            if appointments:
                mr_map = {a.reference_number: a for a in appointments}

                cols = st.columns(2)
                with cols[0]:
                    selected_mr = st.selectbox("Select MR Number", options=list(mr_map.keys()))
                with cols[1]:
                    patient_name = mr_map[selected_mr].patient.name if selected_mr else ""
                    st.text_input("Patient Name", value=patient_name, disabled=True)

                # Initialize session state for medications and input fields
                st.session_state.setdefault("medications", [])
                if "medication_input" not in st.session_state:
                    st.session_state["medication_input"] = ""
                st.session_state.setdefault("dosage_input", "")
                st.session_state.setdefault("duration_input", "")

                # Show current medications
                if st.session_state.medications:
                    table_cols = st.columns([1, 3, 2, 2])
                    table_cols[0].write("Medication No.")
                    table_cols[1].write("Medication")
                    table_cols[2].write("Dosage")
                    table_cols[3].write("Duration")
                    for idx, med in enumerate(st.session_state.medications):
                        table_cols[0].write(f"Medication {idx+1}")
                        table_cols[1].write(med['medication'])
                        table_cols[2].write(med['dosage'])
                        table_cols[3].write(med['duration'])
                    st.write("---")

                # Add new medication
                with st.expander("Add Medication"):
                    medication = st.text_input("Medication Name", key="medication_input")
                    dosage = st.text_input("Dosage", key="dosage_input")
                    duration = st.text_input("Duration (e.g. 7 days)", key="duration_input")

                    st.button(
                        "Add More", 
                        on_click=add_medication, 
                        # Add a key here to ensure the button has a unique identity if needed
                        key="add_med_button" 
                    )
                if st.button("Submit"):
                    if st.session_state.medications:
                        for med in st.session_state.medications:
                            create_prescription(
                                session,
                                mr_map[selected_mr].appointment_id,
                                doctor.doctor_id,
                                med["medication"],
                                med["dosage"],
                                med["duration"]
                            )
                        st.success("Prescription(s) generated successfully!")
                        st.session_state.show_prescription_form = False
                        st.session_state.medications = []
                        st.rerun()

                if st.button("Close"):
                    st.session_state.show_prescription_form = False
                    st.session_state.medications = []
                    st.rerun()
