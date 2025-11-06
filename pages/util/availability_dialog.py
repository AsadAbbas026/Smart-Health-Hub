import streamlit as st
from datetime import time
from database.queries.availability_queries import (
    add_doctor_availability,
    update_doctor_availability,
    delete_doctor_availability
)

def add_availability_dialog(doctor_id):
    @st.dialog("Add Availability Slot")
    def form():
        days = st.multiselect(
            "Select Days",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        )
        start_time = st.time_input("Start Time", value=time(9, 0))
        end_time = st.time_input("End Time", value=time(17, 0))

        if st.button("Add Slot"):
            if not days or start_time >= end_time:
                st.error("Select valid days and time range.")
            else:
                success, msg = add_doctor_availability(doctor_id, days, start_time, end_time)
                st.success(msg) if success else st.error(msg)
                st.rerun()

    form()


def update_availability_dialog(doctor_id, slots):
    @st.dialog("Update Availability Slot")
    def form():
        slot_map = {
            f"{s[1]}: {s[2].strftime('%I:%M %p')} - {s[3].strftime('%I:%M %p')}": s
            for s in slots
        }
        selected = st.selectbox("Select Slot", options=list(slot_map.keys()))
        s_id, day, s_time, e_time = slot_map[selected]

        days = st.multiselect(
            "Select Days",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            default=[day]
        )
        start_time = st.time_input("Start Time", value=s_time)
        end_time = st.time_input("End Time", value=e_time)

        if st.button("Update Slot"):
            success, msg = update_doctor_availability(doctor_id, s_id, days, start_time, end_time)
            st.success(msg) if success else st.error(msg)
            st.rerun()

    form()


def delete_availability_dialog(doctor_id, slots):
    @st.dialog("Delete Availability Slot")
    def form():
        slot_map = {
            f"{s[1]}: {s[2].strftime('%I:%M %p')} - {s[3].strftime('%I:%M %p')}": s[0]
            for s in slots
        }
        selected = st.multiselect("Select Slots", list(slot_map.keys()))

        if selected and st.button("Confirm Delete"):
            success, msg = delete_doctor_availability(doctor_id, [slot_map[s] for s in selected])
            st.success(msg) if success else st.error(msg)
            st.rerun()

    form()
