import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit.components.v1 import html as st_html
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from database.firebase_config import init_firebase, get_chat_ref, db
from database.queries.doctor_queries import get_doctor_name_by_user_id
from streamlit_webrtc import webrtc_streamer, WebRtcMode

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

def fetch_recent_chats_for_patient(patient_id):
    base_ref = db.reference(f"chats/{patient_id}")
    all_chats = base_ref.get() or {}
    recent = []

    for doctor_id, doctor_node in all_chats.items():
        if not isinstance(doctor_node, dict):
            continue
        messages_dict = doctor_node.get("messages", {})
        if not messages_dict:
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
    st_autorefresh(interval=5000, key=f"chat_refresh_{doctor_id}")
    st.session_state["chat_messages"] = fetch_messages(patient_id, doctor_id)

def select_chat(doctor_id, doctor_name):
    st.session_state["chat_data"] = {"doctor_id": doctor_id, "doctor_name": doctor_name}
    st.session_state["selected_chat"] = doctor_id
    st.session_state["chat_input"] = ""
    patient_id = st.session_state.get("user")["uid"]
    st.session_state["chat_messages"] = fetch_messages(patient_id, doctor_id)

def navigate_back():
    for k in ("chat_data", "selected_chat", "chat_messages", "chat_input"):
        st.session_state.pop(k, None)
    role = st.session_state.get("user", {}).get("role")
    st.session_state.page = "doctor_dashboard" if role=="doctor" else "patient_dashboard" if role=="patient" else "auth"

# ---------- Call Helpers ----------
def generate_call_key(doctor_id, patient_id):
    return f"call_{doctor_id}_{patient_id}"

def start_call(doctor_id):
    patient_id = st.session_state["user"]["uid"]
    st.session_state["call_key"] = generate_call_key(doctor_id, patient_id)
    st.session_state["call_active"] = True
    st.session_state["call_start_time"] = datetime.utcnow()
    st.session_state["call_duration"] = "00:00"

def end_call():
    st.session_state["call_active"] = False
    st.session_state["call_start_time"] = None
    st.session_state["call_duration"] = "00:00"
    if "call_key" in st.session_state:
        del st.session_state["call_key"]

def update_call_timer():
    if st.session_state.get("call_start_time"):
        delta = datetime.utcnow() - st.session_state["call_start_time"]
        minutes, seconds = divmod(int(delta.total_seconds()), 60)
        st.session_state["call_duration"] = f"{minutes:02d}:{seconds:02d}"
    else:
        st.session_state["call_duration"] = "00:00"

def audio_frame_debug_callback(frame):
    print("Got audio frame:", frame.shape, frame.samples)
    return frame


def render_custom_webrtc():
    call_key = st.session_state.get("call_key")
    if not call_key:
        return
    backend_url = "http://192.168.1.6:8000"  # adjust
    # read html template from file or format string
    with open("embed_webrtc.html", "r") as f:
        html = f.read()
    html = html.replace("__CALL_KEY__", call_key).replace("http://localhost:8000", backend_url)
    # set a height that fits your UI
    st_html(html, height=260, scrolling=False)

def render_call_ui(doctor_name, doctor_id):
    if doctor_id:
        if st.session_state.get("call_active"):
            st.markdown(f"### 📞 Call with Dr. {doctor_name}")
            update_call_timer()
            st.metric("Call Duration", st.session_state.get("call_duration", "00:00"))
            #st_autorefresh(interval=1000, key="call_timer_refresh")

            render_custom_webrtc()

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔇 Mute"):
                    st.info("Mute toggled")
            with col2:
                if st.button("🔊 Speaker"):
                    st.info("Speaker toggled")

            if st.button("📴 Hang Up"):
                end_call()
                st.success("Call ended.")
        else:
            if st.button("📞 Start Call"):
                start_call(doctor_id)
                st.success("Call initiated...")

# ---------- Dashboard UI ----------
def show_chat_dashboard():
    st.session_state.setdefault("selected_chat", None)
    st.session_state.setdefault("chat_data", {})
    st.session_state.setdefault("user", {"uid": "patient_123", "role": "patient"})

    patient_id = st.session_state["user"]["uid"]
    chat_data = st.session_state.get("chat_data", {})
    doctor_id = chat_data.get("doctor_id")
    doctor_name = chat_data.get("doctor_name")

    recent_chats = st.session_state.get("recent_chats", []) or fetch_recent_chats_for_patient(patient_id)
    st.session_state["recent_chats"] = recent_chats
    messages = st.session_state.get("chat_messages", [])

    # ---------- Call UI ----------
    if st.session_state.get("call_active") and doctor_id:
        render_call_ui(doctor_name, doctor_id)
        return

    # ---------- CSS ----------
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;}
    div.block-container {padding-top: 0.2rem !important;}
    .chat-box { background-color: #f1f3f6; border-radius: 10px; padding: 15px; height: 500px; overflow-y: auto; }
    .chat-bubble-left { text-align: left; margin-bottom: 12px; }
    .chat-bubble-left div { display: inline-block; background-color: white; color: black; padding: 8px 12px; border-radius: 10px; max-width: 60%; }
    .chat-bubble-right { text-align: right; margin-bottom: 12px; }
    .chat-bubble-right div { display: inline-block; background-color: #007bff; color: white; padding: 8px 12px; border-radius: 10px; max-width: 60%; }
    div.stButton > button {
        height: 48px !important;
        padding-top: 8px !important;
        padding-bottom: 8px !important;
        margin-top: 4px !important;
    }
    input[type=text] { height: 48px !important; }
    </style>
    """, unsafe_allow_html=True)

    st.button("🔙 Return to Smart Health Hub", on_click=navigate_back)
    left_col, right_col = st.columns([1.2, 2.8])

    with left_col:
        # ---------- Search Doctors ----------
        search_doctor = st.text_input(
            "",
            placeholder="Search doctor by name...",
            key="search_doctor_input"
        )

        # Filter recent chats if a search term is entered
        filtered_chats = recent_chats
        if search_doctor:
            filtered_chats = [
                chat for chat in recent_chats
                if search_doctor.strip().lower() in chat.get("doctor_name", "").lower()
            ]

        if not filtered_chats:
            st.info("No recent chats match your search.")
        else:
            for chat in filtered_chats:
                did = chat.get("doctor_id")
                dname = chat.get("doctor_name", "Unknown")
                preview = chat.get("last_message", "")
                last_msg_preview = preview[:25] + ("..." if len(preview) > 25 else "")
                st.button(
                    f"🧑‍⚕️ {dname} – {last_msg_preview or 'No messages'}",
                    key=f"chat_{did}",
                    on_click=select_chat,
                    args=(did, dname)
                )

    with right_col:
        if doctor_id:
            header_col, call_col = st.columns([6, 1])
            with header_col:
                st.markdown(f"### 💬 Chat with 👤 {doctor_name}")
            with call_col:
                if st.button("📞 Call", key="call_btn"):
                    start_call(doctor_id)
                    st.success("Call initiated...")

            chat_html = "<div class='chat-box'>"
            for msg in messages:
                sender_side = "right" if msg.get("sender_id") == doctor_id else "left"
                safe_text = (msg.get("message") or "").replace("\n", "<br>")
                chat_html += f"<div class='chat-bubble-{sender_side}'><div>{safe_text}</div></div>"
            chat_html += "</div>"
            st.markdown(chat_html, unsafe_allow_html=True)

            add_vertical_space(1)
            with st.form(key="chat_form", clear_on_submit=False):
                msg_col, send_col = st.columns([13, 2])
                with msg_col:
                    st.text_input("Type a message...", key="chat_input", label_visibility="collapsed")
                with send_col:
                    st.form_submit_button("Send", key="send_btn", on_click=lambda: send_message(doctor_id))
            st_autorefresh(interval=5000, key=f"chat_refresh_{doctor_id}")
        else:
            st.markdown("### 💬 No chat selected")
            st.info("Select a doctor from the left panel to start chatting 💬")
