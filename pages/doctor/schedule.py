import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from pages.util.menu import doctor_sidebar
from database.queries.availability_queries import get_doctor_id_by_email, get_doctor_slots
from pages.util.availability_dialog import add_availability_dialog, update_availability_dialog, delete_availability_dialog

def show_schedule():
    user = st.session_state.get("user", None)
    if not user or user["role"] != "doctor":
        st.error("Please log in as a doctor to access this page.")
        st.session_state.page = "auth"
        st.rerun()
        return
    
    st.header("Manage Schedule", divider="gray")

    doctor_id = get_doctor_id_by_email(user["email"])
    slots = get_doctor_slots(doctor_id)

    col1, col2, col3 = st.columns([0.8, 0.1, 0.15])
    with col1:
        if st.button("Add Schedule Slots", type="primary"):
            add_availability_dialog(doctor_id)
    with col2:
        if st.button("Update Schedule", type="tertiary") and slots:
            update_availability_dialog(doctor_id, slots)
    with col3:
        if st.button("Delete Schedules") and slots:
            delete_availability_dialog(doctor_id, slots)

    if slots:
        df = pd.DataFrame(slots, columns=["ID", "Day", "Start Time", "End Time"])
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(enabled=True, paginationPageSize=5)
        AgGrid(df, gridOptions=gb.build(), height=500, fit_columns_on_grid_load=True)
    else:
        st.info("No availability slots found.")
