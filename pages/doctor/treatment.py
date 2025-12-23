import streamlit as st
import pandas as pd
from sqlalchemy import text
from st_aggrid import AgGrid, GridOptionsBuilder
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from pages.util.menu import doctor_sidebar
from database.queries.treatment_queries import (
    add_treatment, get_treatments_by_doctor,
    update_treatment, delete_treatments
)

# --- Dialog: Add Treatment ---
def add_treatment_dialog(doctor_id):
    @st.dialog("Add New Treatment")
    def form():
        with st.form("add_treatment", border=False):
            name = st.text_input("Treatment Name")
            description = st.text_area("Description")
            cost = st.number_input("Cost (PKR)", min_value=0.0, step=100.0)
            if st.form_submit_button("Add"):
                if name and cost > 0:
                    with SessionLocal() as session:
                        add_treatment(session, doctor_id, name, description, cost)
                    st.success(f"✅ Treatment '{name}' added successfully!")
                    st.rerun()
                else:
                    st.error("Treatment name and valid cost required.")
    form()


# --- Dialog: Update Treatment ---
def update_treatment_dialog(doctor_id, treatments):
    @st.dialog("Update Treatment")
    def form():
        options = {t.treatment_name: t for t in treatments}
        selected_name = st.selectbox("Select Treatment", options=list(options.keys()))
        t = options[selected_name]

        with st.form("update_treatment", border=False):
            name = st.text_input("Treatment Name", value=t.treatment_name)
            description = st.text_area("Description", value=t.description or "")
            cost = st.number_input("Cost (PKR)", min_value=0.0, step=100.0, value=float(t.cost))
            if st.form_submit_button("Update"):
                with SessionLocal() as session:
                    updated = update_treatment(session, t.treatment_id, doctor_id, name, description, cost)
                if updated:
                    st.success(f"✅ Treatment '{name}' updated successfully!")
                    st.rerun()
                else:
                    st.error("Treatment not found or update failed.")
    form()


# --- Dialog: Delete Treatments ---
def delete_treatment_dialog(doctor_id, treatments):
    @st.dialog("Delete Treatments")
    def form():
        options = {t.treatment_name: t.treatment_id for t in treatments}
        selected_names = st.multiselect("Select Treatments to Delete", options=list(options.keys()))
        if selected_names:
            st.warning(f"Confirm deletion of: {', '.join(selected_names)}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Delete", key="confirm_delete"):
                    ids = [options[name] for name in selected_names]
                    with SessionLocal() as session:
                        delete_treatments(session, doctor_id, ids)
                    st.success("✅ Treatment(s) deleted successfully!")
                    st.rerun()
            with col2:
                if st.button("Cancel", key="cancel_delete"):
                    st.rerun()
        else:
            st.info("Please select at least one treatment.")
    form()


# --- Main Page ---
def show_treatments():
    user = st.session_state.get("user", None)
    
    if not user or user["role"] != "doctor":
        st.error("Please log in as a doctor to access this page.")
        st.session_state.page = "auth"
        st.rerun()

    st.header("🩺 Manage Treatments", divider="grey")

    with SessionLocal() as session:
        # Get doctor's ID
        doctor_id = session.execute(
            text("SELECT doctor_id FROM doctors WHERE user_id = :user_id"),
            {"user_id": user['uid']}
        ).scalar()

        treatments = get_treatments_by_doctor(session, doctor_id)

        col1, col2, col3 = st.columns([1.8, 0.5, 0.5])
        with col1:
            if st.button("Add New Treatment", type="primary"):
                add_treatment_dialog(doctor_id)
        with col2:
            if treatments and st.button("Update Treatment", type="secondary"):
                update_treatment_dialog(doctor_id, treatments)
        with col3:
            if treatments and st.button("Delete Treatments", type="secondary"):
                delete_treatment_dialog(doctor_id, treatments)

        if treatments:
            df = pd.DataFrame(
                [(t.treatment_id, t.treatment_name, t.description, float(t.cost)) for t in treatments],
                columns=["Treatment ID", "Name", "Description", "Cost (PKR)"]
            )

            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(enabled=True, paginationPageSize=5)
            gb.configure_side_bar(filters_panel=True)
            gb.configure_default_column(editable=False, wrapText=True, autoHeight=True)
            grid_options = gb.build()

            AgGrid(df, gridOptions=grid_options, height=600, fit_columns_on_grid_load=True)
        else:
            st.info("No treatments found.")
