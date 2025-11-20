import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from database.firebase_config import init_firebase, get_chat_ref, db
from database.queries.doctor_queries import get_doctor_name_by_user_id
import functools

init_firebase()

# ---------- Helpers ----------
def fetch_messages(patient_id, doctor_id):
    if not patient_id or not doctor_id:
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

def fetch_recent_chats(patient_id):
    base_ref = db.reference(f"chats/{patient_id}")
    all_chats = base_ref.get() or {}
    recent = []
    for doctor_id, messages_dict in all_chats.items():
        if not isinstance(messages_dict, dict) or not messages_dict:
            continue
        last_msg = max(messages_dict.values(), key=lambda x: x.get("send_time", ""))
        doctor_name = get_doctor_name_by_user_id(doctor_id)
        recent.append({
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "last_message": str(last_msg.get("message", "")),
            "time": last_msg.get("send_time", "")
        })
    recent.sort(key=lambda x: x.get("time", ""), reverse=True)
    return recent

def send_message(doctor_id):
    text = st.session_state.get("chat_input", "")
    if not text or not doctor_id:
        return
    patient_id = st.session_state.get("user")["uid"]
    msg = {
        "sender_id": patient_id,
        "receiver_id": doctor_id,
        "message": text.strip(),
        "send_time": datetime.utcnow().isoformat(),
        "status": "sent",
    }
    get_chat_ref(patient_id, doctor_id).push(msg)
    st.session_state["chat_input"] = ""
    st.session_state["chat_messages"] = fetch_messages(patient_id, doctor_id)

def select_chat(doctor_id, doctor_name):
    st.session_state["chat_data"] = {"doctor_id": doctor_id, "doctor_name": doctor_name}
    st.session_state["selected_chat"] = doctor_id
    st.session_state["chat_input"] = ""
    patient_id = st.session_state.get("user")["uid"]
    st.session_state["chat_messages"] = fetch_messages(patient_id, doctor_id)

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

    patient_id = st.session_state.get("user")["uid"]
    chat_data = st.session_state.get("chat_data", {})
    doctor_id = chat_data.get("doctor_id")
    doctor_name = chat_data.get("doctor_name")

    recent_chats = st.session_state.get("recent_chats", [])
    messages = st.session_state.get("chat_messages", [])

    # CSS
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

    with left_col:
        st.markdown("### Recent Chats")
        if not recent_chats:
            st.info("No recent chats yet.")
        else:
            for chat in recent_chats:
                did = chat["doctor_id"]
                dname = chat["doctor_name"]
                preview = chat.get("last_message", "")
                last_msg_preview = preview[:25] + ("..." if len(preview) > 25 else "")
                label = f"🧑‍⚕️ {dname} – {last_msg_preview or 'No messages'}"
                st.button(label, key=f"chat_{did}", on_click=select_chat, args=(did, dname))

    with right_col:
        if doctor_id:
            st.markdown(f"### 💬 Chat with 🧑‍⚕️ {doctor_name}")
            chat_html = "<div class='chat-box'>"
            for msg in messages:
                sender_side = "right" if msg.get("sender_id") == patient_id else "left"
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
                    st.form_submit_button("Send 📤", on_click=lambda: send_message(doctor_id))

            st_autorefresh(interval=5000, key=f"chat_refresh_{doctor_id}",
                           on_refresh=lambda: st.session_state.update(
                               {"chat_messages": fetch_messages(patient_id, doctor_id)}
                           ))

        else:
            st.markdown("### 💬 No chat selected")
            st.info("Select a doctor from the left panel to start chatting 💬")
