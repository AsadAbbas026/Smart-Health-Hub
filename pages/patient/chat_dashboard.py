import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from database.firebase_config import init_firebase, get_chat_ref, db
from database.queries.doctor_queries import get_doctor_name_by_user_id
import time

init_firebase()

def fetch_messages(patient_id, doctor_id):
    """Fetch messages between patient and doctor, sorted by time."""
    chat_ref = get_chat_ref(patient_id, doctor_id)
    data = chat_ref.get()

    messages = []
    if data:
        for key, value in data.items():
            messages.append({
                "sender_id": value.get("sender_id"),
                "receiver_id": value.get("receiver_id"),
                "message": value.get("message"),
                "send_time": value.get("send_time"),
                "status": value.get("status", "sent"),
            })

        # Sort messages by send_time
        messages.sort(key=lambda x: x["send_time"])

    return messages

def fetch_recent_chats(patient_id):
    """Return all doctor chat threads under the patient."""
    base_ref = db.reference(f"chats/{patient_id}")  # ✅ don't use get_chat_ref here
    all_chats = base_ref.get()
    recent = []

    if all_chats:
        for doctor_id, doc_data in all_chats.items():
            # each doctor node has a "messages" child
            doctor_name = get_doctor_name_by_user_id(doctor_id)
            messages = doc_data.get("messages", {})
            if not messages:
                continue

            # Get last message in that doctor’s thread
            last_msg = list(messages.values())[-1]
            recent.append({
                "doctor_id": doctor_id,
                "doctor_name": doctor_name,
                "last_message": last_msg.get("message", ""),
                "time": last_msg.get("send_time", ""),
            })

        # Sort by most recent time
        recent.sort(key=lambda x: x["time"], reverse=True)

    return recent

def send_message_callback(doctor_id):
    new_message = st.session_state.chat_input
    if not new_message.strip():
        return

    user = st.session_state.get("user", {"uid": "patient_123"})
    patient_id = user["uid"]

    msg_data = {
        "sender_id": patient_id,
        "receiver_id": doctor_id,
        "message": new_message.strip(),
        "send_time": datetime.utcnow().isoformat(),
        "status": "sent"
    }

    chat_ref = get_chat_ref(patient_id, doctor_id)
    chat_ref.push(msg_data)

    st.session_state.chat_input = ""

def navigate_back():
    # Only set override, let main handle rerun
    st.session_state["page_override"] = "patient_dashboard"
    st.session_state["page_index"] = 1  # Assuming Dashboard is index 1
    # Clear temporary chat state
    st.session_state.pop("chat_data", None)
    st.session_state.pop("selected_chat", None)
    st.session_state.pop("chat_messages", None)
    st.session_state.pop("chat_input", None)


def show_chat_dashboard():
    # Clean up chat state aggressively on entry if not on chat dashboard
    if st.session_state.page != "chat_dashboard":
         st.session_state.pop("chat_data", None)
         st.session_state.pop("selected_chat", None)
         st.session_state.pop("chat_messages", None)
         st.session_state.pop("chat_input", None)

    st.empty()
    st.set_page_config(page_title="Chat Dashboard", layout="wide")

    user = st.session_state.get("user", {"uid": "patient_123"})
    patient_id = user["uid"]

    # ✅ Reset chat if just entered the page fresh (keep original logic)
    if "page" in st.session_state and st.session_state.page == "chat_dashboard":
        if "chat_data" not in st.session_state:
            st.session_state["chat_data"] = None

    chat_data = st.session_state.get("chat_data", None)
    doctor_id = None
    doctor_name = None

    if chat_data:
        doctor_id = chat_data.get("doctor_id")
        doctor_name = chat_data.get("doctor_name", "Doctor")

    # Load recent chats always
    recent_chats = fetch_recent_chats(patient_id)

    # Load messages only if a chat is selected
    messages = fetch_messages(patient_id, doctor_id) if doctor_id else []
    st.session_state["chat_messages"] = messages

    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        div.block-container {padding-top: 0.2rem !important;}
        .chat-box {
            background-color: #f1f3f6;
            border-radius: 10px;
            padding: 15px;
            height: 500px;
            overflow-y: auto;
        }
        .chat-bubble-left {
            text-align: left;
            margin-bottom: 12px;
        }
        .chat-bubble-left div {
            display: inline-block;
            background-color: white;
            color: black;
            padding: 8px 12px;
            border-radius: 10px;
            max-width: 60%;
        }
        .chat-bubble-right {
            text-align: right;
            margin-bottom: 12px;
        }
        .chat-bubble-right div {
            display: inline-block;
            background-color: #007bff;
            color: white;
            padding: 8px 12px;
            border-radius: 10px;
            max-width: 60%;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Back button ---
    st.button(
        "🔙 Return to Smart Health Hub",
        on_click=lambda: navigate_back()
    )

    left_col, right_col = st.columns([1.2, 2.8])

    with left_col:
        st.markdown("### Recent Chats")
        if not recent_chats:
            st.info("No recent chats yet.")
        else:
            for chat in recent_chats:
                doctor_id_temp = chat["doctor_id"]
                doctor_name_temp = get_doctor_name_by_user_id(doctor_id_temp)
                last_msg_preview = chat["last_message"][:25] + ("..." if len(chat["last_message"]) > 25 else "")
                
                if st.button(f"🧑‍⚕️ {doctor_name_temp} – {last_msg_preview}", key=f"chat_{doctor_id_temp}"):
                    st.session_state["chat_data"] = {
                        "doctor_id": doctor_id_temp,
                        "doctor_name": doctor_name_temp,
                    }
                    st.session_state["selected_chat"] = doctor_id_temp
                    #st.rerun()

    # --- RIGHT SIDE: show chat only if selected ---
    if doctor_id:
        with right_col:
            st.markdown(f"### 💬 Chat with 🧑‍⚕️ {doctor_name}")

            # Chat UI
            chat_html = "<div class='chat-box'>"
            for msg in messages:
                sender_type = "right" if msg["sender_id"] == patient_id else "left"
                chat_html += f"<div class='chat-bubble-{sender_type}'><div>{msg['message']}</div></div>"
            chat_html += "</div>"
            st.markdown(chat_html, unsafe_allow_html=True)

            add_vertical_space(1)

            # Message input form
            with st.form(key='chat_form', clear_on_submit=False):
                msg_col1, msg_col2 = st.columns([5, 1])
                with msg_col1:
                    st.text_input(
                        "Type a message...",
                        key="chat_input",
                        label_visibility="collapsed",
                        placeholder="Type a message and press Enter..."
                    )
                with msg_col2:
                    st.form_submit_button(
                        "Send 📤",
                        on_click=lambda: send_message_callback(doctor_id),
                        type="primary",
                        use_container_width=True
                    )

            st_autorefresh(interval=5000, key="chat_refresh")

    else:
        # --- If no chat selected, show message centered under both columns ---
        with right_col:
            st.markdown("### 💬 No chat selected")
            st.info("Select a doctor from the left panel to start chatting 💬")