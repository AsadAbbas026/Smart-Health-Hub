import streamlit as st
from pages.util.menu import doctor_sidebar
from database.connection import SessionLocal
from database.queries.appointment_queries import get_appointments_for_doctor, cancel_appointment
from utils.email_utils import send_cancellation_email_doctor
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

def show_appointments():
    user = st.session_state.get("user", None)
    if not user or user["role"] != "doctor":
        st.error("Please log in as a doctor.")
        st.session_state.page = "auth"
        st.rerun()
        return

    st.header("Appointments", divider="gray")

    with SessionLocal() as session:
        appointments = get_appointments_for_doctor(user["email"])

        if not appointments:
            st.info("No appointments found.")
            return

        df = pd.DataFrame([{
            "Appointment ID": appt.appointment_id,
            "Date": appt.appointment_date,
            "Time Slot": appt.time_slot,
            "Patient": appt.patient.name,
            "Status": appt.status,
            "Reference Number": appt.reference_number,
            "Treatment": appt.treatment.treatment_name if appt.treatment else "",
            "Patient Email": appt.patient.user.email
        } for appt in appointments])

        # AgGrid table
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationPageSize=10)
        gb.configure_default_column(editable=True, groupable=True)
        gb.configure_side_bar()
        grid_options = gb.build()

        AgGrid(df, gridOptions=grid_options, height=500, fit_columns_on_grid_load=True)

        # Cancel appointment
        valid_appointments = [
            a for a in appointments
            if a.status not in ["cancelled", "completed"]
        ]

        if not valid_appointments:
            st.info("No active appointments to cancel.")
        else:
            cancel_appointment_id = st.selectbox(
                "Select Appointment to Cancel",
                [a.appointment_id for a in valid_appointments],
                format_func=lambda x: f"Appointment #{x}"
            )

            if st.button("Cancel Appointment"):
                patient_email, ref_num = cancel_appointment(cancel_appointment_id)
                if patient_email:
                    send_cancellation_email_doctor(patient_email, ref_num)
                    st.success(f"Appointment cancelled and notification sent to {patient_email}")
                    st.rerun()  # ✅ modern replacement for st.experimental_rerun()
                else:
                    st.error("Failed to cancel appointment.")