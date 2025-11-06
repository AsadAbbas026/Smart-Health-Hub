# pages/patient/dashboard.py
import streamlit as st
from pages.util.menu import patient_sidebar
import plotly.express as px
from database.queries.patient_queries import get_patient_profile
from database.queries.appointment_queries import get_patient_appointments
import pandas as pd

def show_dashboard():

    """Patient dashboard UI."""
    user = st.session_state.get("user", None)
    if not user or user["role"] != "patient":
        st.error("Please log in as a patient to access this page.")
        st.session_state.page = "auth"
        st.rerun()
        return

    st.header("Patient Dashboard", divider="grey")
    # --- Profile ---
    profile = get_patient_profile(user["email"])
    with st.container():
        st.subheader("Profile Overview")
        cols = st.columns(3)
        if profile:
            cols[0].metric("Name", profile["name"])
            cols[1].metric("Phone", profile["phone"] or "Not provided")
            cols[2].metric("Date of Birth", profile["dob"].strftime("%Y-%m-%d") if profile["dob"] else "Not provided")
        else:
            st.warning("Profile details not found. Please update your profile.")
    
    st.divider()
    # --- Appointments ---  

    df = get_patient_appointments(user["email"])
    
    if not df.empty:
        st.subheader("Appointment Overview")
        total_appointments = len(df)
        scheduled = len(df[df["Status"]=="scheduled"])
        cancelled = len(df[df["Status"]=="cancelled"])

        cols = st.columns(4)
        cols[0].metric("Total Appointments", total_appointments)
        cols[1].metric("Scheduled", scheduled)
        cols[2].metric("Completed", total_appointments - scheduled - cancelled)
        cols[3].metric("Cancelled", cancelled)

        st.divider()
        
        # Timeline chart
        df["Start"] = pd.to_datetime(df["Appointment Date"])
        df["End"] = df["Start"] + pd.Timedelta(hours=1)  # fake 1-hour duration

        fig_timeline = px.timeline(
            df,
            x_start="Start",
            x_end="End",
            y="Doctor Name",
            color="Status",
            color_discrete_map={"scheduled": "#3d3693", "cancelled": "#EF553B"},
            title="Appointment Schedule"
        )
        fig_timeline.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig_timeline)

        # Pie chart for status
        status_counts = df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_pie = px.pie(
            status_counts,
            names="Status",
            values="Count",
            title="Appointment Status",
            color_discrete_sequence=["#3d3693"]
        )
        st.plotly_chart(fig_pie)

        # Appointments by day
        if "Appointment Date" in df.columns:
            df["Day"] = pd.to_datetime(df["Appointment Date"]).dt.day_name()
        else:
            st.error("Column 'Appointment Date' not found in DataFrame.")
            st.stop()

        day_counts = df["Day"].value_counts().reset_index()
        day_counts.columns = ["Day", "Count"]
        fig_bar = px.bar(
            day_counts,
            x="Day",
            y="Count",
            title="Appointments by Day",
            color_discrete_sequence=["#3d3693"]
        )
        st.plotly_chart(fig_bar)

