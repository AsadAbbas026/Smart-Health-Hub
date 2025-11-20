import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
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
    # Ensure IDs exist
    if "Doctor ID" not in df.columns:
        df["Doctor ID"] = df["doctor_id"]
    if "Patient ID" not in df.columns:
        df["Patient ID"] = df["patient_id"]
    if "Doctor Name" not in df.columns:
        df["Doctor Name"] = df["doctor_name"]

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
                        patient_id: params.data["Patient ID"],
                        doctor_name: params.data["Doctor Name"]
                    };
                    window.top.postMessage({ type: "chat_open", detail: payload }, "*");
                });
            }
            getGui() { return this.eGui; }
        }
    """)

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, cellStyle={'fontSize': '16px'})
    gb.configure_column("Doctor ID", hide=True)
    gb.configure_column("Patient ID", hide=True)
    gb.configure_column("Action", cellRenderer=chat_button_renderer)
    grid_options = gb.build()

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
        const topWindow = window.top;
        if (!topWindow.hasChatBridgeListener) {
            topWindow.hasChatBridgeListener = true;
            topWindow.addEventListener("message", (e) => {
                console.log("This is the JS and Python Bridge");
                if (e.data && e.data.type === "chat_open") {
                    const detail = e.data.detail;
                    const params = new URLSearchParams(topWindow.location.search);
                    params.set("chat_open", JSON.stringify(detail));
                    const newUrl = topWindow.location.pathname + '?' + params.toString();
                    topWindow.history.replaceState({}, '', newUrl);
                    topWindow.dispatchEvent(new Event('popstate'));
                }
            });
        }
    })();
    </script>
    """
    st.components.v1.html(js_bridge_script, height=0)

    # --- Handle chat_open param ---
    query_params = st.query_params
    js_event = query_params.get("chat_open")

    if js_event:
        print(f"JS event available {js_event}")
        try:
            data = json.loads(js_event)
            if data:
                print(f"Data to send on the chat dashboard is: {data}")
                st.session_state["chat_data"] = {
                    "doctor_id": data["doctor_id"],
                    "patient_id": data["patient_id"],
                    "doctor_name": data.get("doctor_name", "Doctor")
                }
                st.session_state["chat_ref"] = f"{data['patient_id']}/{data['doctor_id']}"
                st.session_state.page = "chat_dashboard"

                # ✅ Clear query param safely
                query_params.pop("chat_open", None)
                st.query_params = query_params

                st.rerun()
        except Exception as e:
            st.error(f"Error opening chat: {e}")


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

        cols = st.columns(4)
        with cols[0]:
            st.plotly_chart(
                px.pie(appointments, names="Status", title="Appointment Status"),
                use_container_width=True
            )

        with cols[3]:
            df_counts = appointments["Doctor Name"].value_counts().reset_index()
            df_counts.columns = ["Doctor", "Count"]
            st.plotly_chart(px.bar(df_counts, x="Doctor", y="Count", title="Appointments by Doctor"), use_container_width=True)

        # ✅ Renders the grid with chat button
        render_aggrid_with_chat_button(appointments)

    finally:
        db.close()
