# pages/patient/your_appointments.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from database.connection import SessionLocal
from database.queries.appointment_queries import (
    get_patient_appointments,
    cancel_appointment,
    reschedule_appointment,
    get_available_slots
)
from notifications import trigger_notification
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
import json

def render_aggrid_with_chat_button(df):
    # Add a new column for the action button
    df["Action"] = "💬 Chat"

    # --- Define a custom JavaScript cell renderer ---
    chat_button_renderer = JsCode("""
        class BtnCellRenderer {
            init(params) {
                this.params = params;
                this.eGui = document.createElement('div');
                this.eGui.innerHTML = `
                    <button style="
                        background-color:#28a745;
                        color:white;
                        border:none;
                        border-radius:6px;
                        padding:4px 10px;
                        cursor:pointer;
                        font-size:14px;">
                        💬 Chat
                    </button>
                `;
                this.eGui.querySelector('button').addEventListener('click', () => {
                    const payload = {
                        doctor_id: params.data["Doctor ID"],
                        patient_id: params.data["Patient ID"]
                    };
                    console.log("💬 Chat button clicked:", payload);
                    window.top.postMessage({ type: "chat_open", detail: payload }, "*");
                });
            }
            getGui() { return this.eGui; }
        }
    """)


    # --- Configure AgGrid ---
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, cellStyle={'fontSize': '16px'})
    gb.configure_column("Action", cellRenderer=chat_button_renderer)
    grid_options = gb.build()

    # --- Render AgGrid ---
    AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=420,
    )

    # --- JS → Streamlit bridge (handles button click) ---
    js_bridge_script = """
    <script>
    (function() {
        console.log("✅ Streamlit Chat Bridge Loaded");

        const topWindow = window.top;

        if (!topWindow.hasChatBridgeListener) {
            topWindow.hasChatBridgeListener = true;

            topWindow.addEventListener("message", (e) => {
                if (e.data && e.data.type === "chat_open") {
                    const detail = e.data.detail;
                    console.log("📩 Opening chat with:", detail);

                    const params = new URLSearchParams(topWindow.location.search);
                    params.set("chat_open", JSON.stringify(detail));
                    const newUrl = topWindow.location.pathname + '?' + params.toString();
                    topWindow.history.replaceState({}, '', newUrl);

                    // Trigger Streamlit rerun
                    topWindow.dispatchEvent(new Event('popstate'));
                }
            });
        }
    })();
    </script>
    """
    st.components.v1.html(js_bridge_script, height=0)

    # --- Handle query param event in Streamlit ---
    query = st.query_params
    js_event = query.get("chat_open")

    if js_event:
        try:
            data = json.loads(js_event)
            print("💬 Initializing chat with data:", data)
            if data:
                st.session_state["chat_data"] = {
                    "doctor_id": data["doctor_id"],
                    "patient_id": data["patient_id"]
                }
                # Create Firebase reference format for later use
                st.session_state["chat_ref"] = f"{data['patient_id']}/{data['doctor_id']}"
                
                st.success("Chat session initialized!")
                del query["chat_open"]
                st.query_params = query
                st.session_state.page = "chat_dashboard"
                st.rerun()
        except Exception as e:
            st.error(f"Error loading chat: {e}")

# ---------------------- Helper for Reminder Message ----------------------
def generate_appointment_message(row):
    """Generate a personalized reminder message."""
    appointment_date = datetime.strptime(row["Appointment Date"], "%Y-%m-%d %H:%M")
    now = datetime.now()
    delta_days = (appointment_date.date() - now.date()).days

    if delta_days < 0:
        return None  # Past appointment
    elif delta_days == 0:
        timing = "today"
    elif delta_days == 1:
        timing = "tomorrow"
    else:
        return None  # Only send for today/tomorrow

    return (
        f"📅 Reminder: You have an appointment with Dr. {row['Doctor Name']} "
        f"{timing} ({row['Day']}) at {row['Time Slot']} for {row['Treatment Name']}."
    )

def send_daily_appointment_reminders(df):
    """Send one daily reminder for appointments within the next 5 days."""
    now = datetime.now()

    for _, row in df.iterrows():
        appointment_date = datetime.strptime(row["Appointment Date"], "%Y-%m-%d %H:%M")
        delta_days = (appointment_date.date() - now.date()).days

        # Send only if appointment is within the next 5 days and not past
        if 0 <= delta_days <= 5:
            key = f"last_notif_{row['Appointment ID']}"
            last_sent = st.session_state.get(key)

            # If not sent today, send it now
            if not last_sent or last_sent.date() < now.date():
                message = (
                    f"📅 Reminder: Your appointment with Dr. {row['Doctor Name']} "
                    f"is in {delta_days} day{'s' if delta_days != 1 else ''} "
                    f"({row['Day']}) at {row['Time Slot']} for {row['Treatment Name']}."
                )
                trigger_notification("Daily Appointment Reminder", message)
                st.session_state[key] = now  # Mark as sent today

def show_your_appointments():
    user = st.session_state.get("user", None)
    if not user or user["role"] != "patient":
        st.error("Please log in as a patient.")
        return

    st.header("Your Appointments", divider="gray")

    db = SessionLocal()
    try:
        appointments = get_patient_appointments(user["email"])
        if appointments.empty:
            st.info("No appointments found.")
            return

        # ---------------------- ✅ Daily Notifications ----------------------
        send_daily_appointment_reminders(appointments)

        # ---------------------- 📊 Charts ----------------------
        cols = st.columns(4)
        with cols[0]:
            st.plotly_chart(
                px.pie(appointments, names="Status", title="Appointment Status"),
                use_container_width=True
            )

        with cols[3]:
            df_counts = appointments["Doctor Name"].value_counts().reset_index()
            df_counts.columns = ["Doctor", "Count"]
            fig = px.bar(df_counts, x="Doctor", y="Count", title="Appointments by Doctor")
            st.plotly_chart(fig, use_container_width=True)

        # ---------------------- 📋 Table ----------------------
        gb = GridOptionsBuilder.from_dataframe(appointments)
        gb.configure_pagination(enabled=True, paginationPageSize=5)
        render_aggrid_with_chat_button(appointments)


        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cancel Appointment"):
                appointment_id = st.selectbox("Select Appointment ID", appointments["Appointment ID"])
                if st.button("Confirm Cancel"):
                    cancel_appointment(db, appointment_id, appointments[0].patient_id)
                    st.success("Appointment cancelled successfully!")
                    st.rerun()

        with col2:
            if st.button("Reschedule Appointment"):
                appointment_id = st.selectbox("Select Appointment to Reschedule", appointments["Appointment ID"])
                new_date = st.date_input("New Date", min_value=datetime.now().date())
                available = get_available_slots(db, appointments[0].doctor_id, new_date)
                new_time = st.selectbox("Select Time Slot", available)
                if st.button("Confirm Reschedule"):
                    reschedule_appointment(db, appointment_id, appointments[0].patient_id, new_date, new_time)
                    st.success("Appointment rescheduled successfully!")
                    st.rerun()
    finally:
        db.close()
