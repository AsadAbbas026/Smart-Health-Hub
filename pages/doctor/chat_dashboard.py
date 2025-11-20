import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from database.firebase_config import init_firebase, get_chat_ref, db
from database.queries.patient_queries import get_patient_by_user_id

init_firebase()

# ---------- Helpers ----------
def fetch_messages(doctor_id, patient_id):
    if not patient_id:
        return []
    chat_ref = get_chat_ref(patient_id, doctor_id)
    data = chat_ref.get() or {}
    messages = [
        {
            "sender_id": v.get("sender_id"),
            "receiver_id": v.get("receiver_id"),
            "message": v.get("message", ""),
            "send_time": v.get("send_time", ""),
            "status": v.get("status", "sent"),
        }
        for _, v in data.items()
    ]
    messages.sort(key=lambda x: x.get("send_time", ""))
    return messages

def fetch_recent_chats(doctor_id):
    recent = []
    base_ref = db.reference("chats")
    all_chats = base_ref.get() or {}

    if "cached_patients" not in st.session_state:
        st.session_state["cached_patients"] = {}
    cached_patients = st.session_state["cached_patients"]

    for patient_id, patient_data in all_chats.items():
        if not isinstance(patient_data, dict):
            continue
        doctor_node = patient_data.get(doctor_id)
        if not doctor_node:
            continue
        messages = doctor_node or {}
        if not messages:
            continue

        last_msg = max(messages.values(), key=lambda x: x.get("send_time", ""))

        if patient_id in cached_patients:
            patient_name = cached_patients[patient_id]
        else:
            patient_obj = get_patient_by_user_id(patient_id)
            patient_name = getattr(patient_obj, "name", "Unknown") if patient_obj else "Unknown"
            cached_patients[patient_id] = patient_name

        recent.append({
            "patient_id": patient_id,
            "patient_name": patient_name,
            "last_message": str(last_msg.get("message", "")),
            "time": last_msg.get("send_time", "")
        })

    recent.sort(key=lambda x: x.get("time", ""), reverse=True)
    return recent

def send_message(patient_id):
    text = st.session_state.get("chat_input", "")
    if not text or not patient_id:
        return
    doctor_id = st.session_state.get("user", {"uid": "doctor_123"})["uid"]
    msg = {
        "sender_id": doctor_id,
        "receiver_id": patient_id,
        "message": text.strip(),
        "send_time": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    get_chat_ref(patient_id, doctor_id).push(msg)
    st.session_state["chat_input"] = ""
    # refresh messages immediately
    st.session_state["chat_messages"] = fetch_messages(doctor_id, patient_id)

def select_chat(patient_id, patient_name):
    st.session_state["chat_data"] = {"patient_id": patient_id, "patient_name": patient_name}
    st.session_state["selected_chat"] = patient_id
    st.session_state["chat_input"] = ""
    doctor_id = st.session_state.get("user")["uid"]
    st.session_state["chat_messages"] = fetch_messages(doctor_id, patient_id)

def navigate_back():
    role = st.session_state.get("user", {}).get("role")

    if role == "doctor":
        st.session_state.page = "doctor_dashboard"
    elif role == "patient":
        st.session_state.page = "patient_dashboard"
    else:
        st.session_state.page = "auth"

    # Clear chat states
    for k in ("chat_data", "selected_chat", "chat_messages", "chat_input"):
        st.session_state.pop(k, None)

    st.rerun()

# ---------- UI ----------
def show_chat_dashboard():
    st.session_state.setdefault("selected_chat", None)
    st.session_state.setdefault("chat_data", {})
    st.session_state.setdefault("page", "chat_dashboard")

    user = st.session_state.get("user", {"uid": "doctor_123"})
    doctor_id = user["uid"]
    
    recent_chats = fetch_recent_chats(doctor_id)
    st.session_state["recent_chats"] = recent_chats
    
    chat_data = st.session_state.get("chat_data", {})
    patient_id = chat_data.get("patient_id")
    patient_name = chat_data.get("patient_name")

    recent_chats = st.session_state.get("recent_chats", [])
    messages = st.session_state.get("chat_messages", [])

    # --- CSS ---
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;}
    div.block-container {padding-top: 0.2rem !important;}
    .chat-box { background-color: #f1f3f6; border-radius: 10px; padding: 15px; height: 500px; overflow-y: auto; }
    .chat-bubble-left { text-align: left; margin-bottom: 12px; }
    .chat-bubble-left div { display: inline-block; background-color: white; color: black; padding: 8px 12px; border-radius: 10px; max-width: 60%; }
    .chat-bubble-right { text-align: right; margin-bottom: 12px; }
    .chat-bubble-right div { display: inline-block; background-color: #007bff; color: white; padding: 8px 12px; border-radius: 10px; max-width: 60%; }
    </style>
    """, unsafe_allow_html=True)

    st.button("🔙 Return to Smart Health Hub", on_click=navigate_back)


    left_col, right_col = st.columns([1.2, 2.8])

    # --- Recent chats ---
    with left_col:
        st.markdown("### Recent Chats")
        if not recent_chats:
            st.info("No recent chats yet.")
        else:
            for chat in recent_chats:
                pid = chat["patient_id"]
                pname = chat["patient_name"]
                preview = chat.get("last_message", "")
                last_msg_preview = preview[:25] + ("..." if len(preview) > 25 else "")
                label = f"👤 {pname} – {last_msg_preview or 'No messages'}"
                st.button(label, key=f"chat_{pid}", on_click=select_chat, args=(pid, pname))

    # --- Chat area ---
    with right_col:
        if patient_id:
            st.markdown(f"### 💬 Chat with 👤 {patient_name}")
            chat_html = "<div class='chat-box'>"
            for msg in messages:
                sender_side = "right" if msg.get("sender_id") == doctor_id else "left"
                safe_text = (msg.get("message") or "").replace("\n", "<br>")
                chat_html += f"<div class='chat-bubble-{sender_side}'><div>{safe_text}</div></div>"
            chat_html += "</div>"
            st.markdown(chat_html, unsafe_allow_html=True)

            add_vertical_space(1)
            with st.form("chat_form", clear_on_submit=False):
                msg_col1, msg_col2 = st.columns([5, 1])
                with msg_col1:
                    st.text_input("Type a message...", key="chat_input", label_visibility="collapsed", placeholder="Type a message...")
                with msg_col2:
                    st.form_submit_button("Send 📤", on_click=lambda: send_message(patient_id))


            # Autorefresh every 5 seconds and manually fetch messages if a chat is selected
            refresh_count = st_autorefresh(interval=5000, key=f"chat_refresh_{patient_id}")

            if patient_id:
                # Only fetch messages when autorefresh triggers
                st.session_state["chat_messages"] = fetch_messages(doctor_id, patient_id)

        else:
            st.markdown("### 💬 No chat selected")
            st.info("Select a patient from the left panel to start chatting 💬")
