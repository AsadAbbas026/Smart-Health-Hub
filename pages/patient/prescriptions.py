# pages/patient/prescriptions.py
import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import datetime, timezone
from database.connection import SessionLocal
from database.queries.prescription_queries import get_prescriptions_for_patient


def show_prescriptions():
    user = st.session_state.get("user", None)

    # --- Access Control ---
    if not user or user.get("role") != "patient":
        st.error("Please log in as a patient to access this page.")
        st.session_state.page = "auth"
        st.rerun()
        return

    st.header("Prescriptions", divider="gray")

    # --- Fetch Prescriptions ---
    with SessionLocal() as session:
        prescriptions = get_prescriptions_for_patient(session, user["email"])

        if not prescriptions:
            st.info("No prescriptions found.")
            return

        df = pd.DataFrame([
            {
                "Prescription ID": p.prescription_id,
                "Medication": p.medication_name,
                "Dosage": p.dosage,
                "Duration (days)": p.duration,
                "Created At": p.created_at,
                "Doctor": p.doctor.name if p.doctor else "Unknown",
            }
            for p in prescriptions
        ])

        # --- Convert datetime safely ---
        df["Created At"] = pd.to_datetime(df["Created At"], errors="coerce")

        # --- Define status function ---
        def get_status(row):
            created_at = row["Created At"]
            if pd.isnull(created_at):
                return "Unknown"

            # Normalize timezone to UTC and make both aware for fair comparison
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            try:
                duration_days = int(row["Duration (days)"]) if pd.notnull(row["Duration (days)"]) else 30
            except ValueError:
                duration_days = 30

            expiry_date = created_at + pd.Timedelta(days=duration_days)
            now_utc = datetime.now(timezone.utc)

            return "Active" if expiry_date > now_utc else "Expired"

        # --- Compute status and dates ---
        df["Status"] = df.apply(get_status, axis=1)
        df["Created Date"] = df["Created At"].dt.date

        # --- Visualization Section ---
        cols = st.columns(4)

        with cols[0]:
            med_counts = df["Medication"].value_counts().reset_index()
            med_counts.columns = ["Medication", "Count"]
            st.plotly_chart(
                px.pie(
                    med_counts,
                    names="Medication",
                    values="Count",
                    title="Medication Distribution",
                    color_discrete_sequence=["#3d3693"],
                ),
                use_container_width=True,
            )

        with cols[1]:
            doctor_counts = df["Doctor"].value_counts().reset_index()
            doctor_counts.columns = ["Doctor", "Count"]
            st.plotly_chart(
                px.bar(
                    doctor_counts,
                    x="Doctor",
                    y="Count",
                    title="Prescriptions by Doctor",
                    color_discrete_sequence=["#3d3693"],
                ),
                use_container_width=True,
            )

        with cols[2]:
            date_counts = df["Created Date"].value_counts().reset_index()
            date_counts.columns = ["Date", "Count"]
            st.plotly_chart(
                px.line(
                    date_counts.sort_values("Date"),
                    x="Date",
                    y="Count",
                    title="Prescriptions Over Time",
                    color_discrete_sequence=["#3d3693"],
                ),
                use_container_width=True,
            )

        with cols[3]:
            status_counts = df["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            st.plotly_chart(
                px.pie(
                    status_counts,
                    names="Status",
                    values="Count",
                    title="Prescription Status",
                    color_discrete_sequence=["#3d3693"],
                ),
                use_container_width=True,
            )

        # --- Data Grid ---
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_grid_options(rowHeight=60)
        gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=False)
        gb.configure_column("Created Date", hide=True)
        gb.configure_side_bar()
        grid_options = gb.build()

        AgGrid(df, gridOptions=grid_options, height=700, fit_columns_on_grid_load=True)
