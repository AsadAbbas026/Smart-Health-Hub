import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder

from pages.util.menu import doctor_sidebar
from utils.time_utils import parse_time_slot_duration
from database.queries.doctor_queries import get_doctor_by_email
from database.queries.appointment_queries import get_appointments_for_doctor
#from database.queries.appointment_queries import get_department_appointment_stats

def show_doctor_dashboard():
    user = st.session_state.get("user", None)
    if not user or user["role"] != "doctor":
        st.error("Please log in as a doctor to access this page.")
        st.session_state.page = "auth"
        st.rerun()
        return

    st.header("Doctor Dashboard", divider="gray")

    doctor= get_doctor_by_email(user["email"])
    print(doctor)

    if not doctor:
        st.warning("Profile not found.")
        return

    with st.container(border=True):
        st.write("### Profile Overview")
        cols = st.columns(4)
        cols[0].metric("Name", doctor.name)
        cols[1].metric("Department", doctor.department or "N/A")
        cols[2].metric("Specialization", doctor.specialization or "N/A")
        cols[3].metric("License Number", doctor.license_number or "N/A")

    appointments = get_appointments_for_doctor(user["email"])
    print(appointments)
    if not appointments:
        st.info("No appointments found.")
        return

    appointment_data = [
        {
            "Appointment ID": appt.appointment_id,
            "Date": appt.appointment_date.strftime("%Y-%m-%d %H:%M"),
            "Patient": appt.patient.name if appt.patient else "N/A",
            "Status": appt.status,
            "Date of Birth": appt.patient.date_of_birth.strftime("%Y-%m-%d") if appt.patient and appt.patient.date_of_birth else "N/A",
            "Gender": appt.patient.gender if appt.patient else "N/A",
            "Treatment": appt.treatment.treatment_name if appt.treatment else "N/A",
            "Time Slot": appt.time_slot,
            "Duration": parse_time_slot_duration(appt.time_slot),
        }
        for appt in appointments
    ]

    df = pd.DataFrame(appointment_data)
    st.write("### Appointments Overview")
    # --- Summary Metrics ---
    total_appointments = len(df)
    scheduled = len(df[df["Status"] == "scheduled"])
    cancelled = len(df[df["Status"] == "cancelled"])
    cols = st.columns(4)
    cols[0].metric("Total Appointments", total_appointments)
    cols[1].metric("Scheduled", scheduled)
    cols[2].metric("Completed", total_appointments - scheduled - cancelled)
    cols[3].metric("Cancelled", cancelled)

    # --- Appointment Table ---
    st.write("### Scheduled Appointments")
    scheduled_df = df[df["Status"] == "scheduled"]
    if not scheduled_df.empty:
        gb = GridOptionsBuilder.from_dataframe(scheduled_df)
        gb.configure_default_column(groupable=True, value=True)
        grid_options = gb.build()
        AgGrid(scheduled_df, gridOptions=grid_options, height=200, fit_columns_on_grid_load=True)
    else:
        st.info("No scheduled appointments.")

    # --- Analytics Section ---
    with st.expander("📊 View Analytics", expanded=True):
        col1, col2, col3 = st.columns(3)

        # --- Pie Chart: Appointment Status ---
        with col1:
            status_counts = df["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig_pie = px.pie(status_counts, names="Status", values="Count", title="Appointment Status")
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- Bar Chart: Appointments by Day ---
        with col2:
            df["Day"] = pd.to_datetime(df["Date"]).dt.day_name()
            day_counts = df["Day"].value_counts().reset_index()
            day_counts.columns = ["Day", "Count"]
            fig_bar = px.bar(day_counts, x="Day", y="Count", title="Appointments by Day")
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- Histogram: Patient Age Distribution ---
        with col3:
            # ✅ Convert DOB strings to datetime first
            df["Date of Birth"] = pd.to_datetime(df["Date of Birth"], errors="coerce")

            # ✅ Now safely calculate age
            df["Age"] = df["Date of Birth"].apply(
                lambda x: (datetime.now().date() - x.date()).days // 365 if pd.notnull(x) else None
            )

            fig_age = px.histogram(df, x="Age", nbins=10, title="Patient Age Distribution")
            st.plotly_chart(fig_age, use_container_width=True)