import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit.components.v1 import html as st_html
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from database.firebase_config import init_firebase, get_chat_ref, db
from database.queries.patient_queries import get_patient_by_user_id
from streamlit_webrtc import webrtc_streamer, WebRtcMode

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

# ---------- Calling & WebRTC ----------
def generate_call_key(doctor_id, patient_id):
    return f"call_{doctor_id}_{patient_id}"

def start_call(patient_id):
    doctor_id = st.session_state["user"]["uid"]
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

def debug_audio(frame):
    print("Audio frame received:", frame.shape)
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

def render_call_ui(patient_name, patient_id):
    if patient_id:
        if st.session_state.get("call_active"):
            st.markdown(f"### 📞 Call with {patient_name}")
            update_call_timer()
            st.metric("Call Duration", st.session_state.get("call_duration", "00:00"))
           # st_autorefresh(interval=1000, key="call_timer_refresh")

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
                start_call(patient_id)
                st.success("Call initiated...")

# ---------- Recent Chats ----------
def fetch_recent_chats_for_doctor(doctor_id):
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
        messages = doctor_node.get("messages", {}) if isinstance(doctor_node, dict) else {}
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

# ---------- Messaging ----------
def send_message(patient_id):
    text = st.session_state.get("chat_input", "")
    if not text or not patient_id:
        return
    doctor_id = st.session_state["user"]["uid"]
    msg = {
        "sender_id": doctor_id,
        "receiver_id": patient_id,
        "message": text.strip(),
        "send_time": datetime.utcnow().isoformat(),
        "status": "sent"
    }
    get_chat_ref(patient_id, doctor_id).push(msg)
    st.session_state["chat_input"] = ""
    st_autorefresh(interval=5000, key=f"chat_refresh_{patient_id}")
    st.session_state["chat_messages"] = fetch_messages(doctor_id, patient_id)

def select_chat(patient_id, patient_name):
    st.session_state["chat_data"] = {"patient_id": patient_id, "patient_name": patient_name}
    st.session_state["selected_chat"] = patient_id
    st.session_state["chat_input"] = ""
    doctor_id = st.session_state["user"]["uid"]
    st.session_state["chat_messages"] = fetch_messages(doctor_id, patient_id)

def navigate_back():
    for k in ("chat_data", "selected_chat", "chat_messages", "chat_input"):
        st.session_state.pop(k, None)
    role = st.session_state.get("user", {}).get("role")
    st.session_state.page = "doctor_dashboard" if role=="doctor" else "patient_dashboard" if role=="patient" else "auth"

# ---------- Dashboard UI ----------
def show_chat_dashboard():
    st.session_state.setdefault("selected_chat", None)
    st.session_state.setdefault("chat_data", {})
    st.session_state.setdefault("user", {"uid": "doctor_123", "role": "doctor"})

    doctor_id = st.session_state["user"]["uid"]
    recent_chats = fetch_recent_chats_for_doctor(doctor_id)
    st.session_state["recent_chats"] = recent_chats

    chat_data = st.session_state.get("chat_data", {})
    patient_id = chat_data.get("patient_id")
    patient_name = chat_data.get("patient_name")
    messages = st.session_state.get("chat_messages", []) or (fetch_messages(doctor_id, patient_id) if patient_id else [])

    if st.session_state.get("call_active") and patient_id:
        render_call_ui(patient_name, patient_id)
        return

    # --- CSS & layout ---
    st.markdown("""
        <style>
        [data-testid="stSidebar"]{display:none;}
        div.block-container{padding-top:0.2rem !important;}
        .chat-box{background-color:#f1f3f6;border-radius:10px;padding:15px;height:500px;overflow-y:auto;}
        .chat-bubble-left{margin-bottom:12px;}
        .chat-bubble-left div{display:inline-block;background:white;color:black;padding:8px 12px;border-radius:10px;max-width:60%;}
        .chat-bubble-right{margin-bottom:12px;text-align:right;}
        .chat-bubble-right div{display:inline-block;background:#007bff;color:white;padding:8px 12px;border-radius:10px;max-width:60%;}
        div.stButton > button {height:48px !important;padding-top:8px !important;padding-bottom:8px !important;margin-top:4px !important;}
        input[type=text] {height:48px !important;}
        </style>
    """, unsafe_allow_html=True)

    st.button("🔙 Return to Smart Health Hub", on_click=navigate_back)
    left_col, right_col = st.columns([1.2, 3.8])

    with left_col:
        st.markdown("### Recent Chats")

        # ---------- Search Patients ----------
        search_patient = st.text_input(
            "",
            placeholder="Search patient by name...",
            key="search_patient_input"
        )

        # Filter recent chats if a search term is entered
        filtered_chats = recent_chats
        if search_patient:
            filtered_chats = [
                chat for chat in recent_chats
                if search_patient.strip().lower() in chat.get("patient_name", "").lower()
            ]

        if not filtered_chats:
            st.info("No recent chats match your search.")
        else:
            for chat in filtered_chats:
                pid = chat["patient_id"]
                pname = chat["patient_name"]
                preview = chat.get("last_message", "")
                last_msg_preview = preview[:25] + ("..." if len(preview) > 25 else "")
                st.button(
                    f"👤 {pname} – {last_msg_preview or 'No messages'}",
                    key=f"chat_{pid}",
                    on_click=select_chat,
                    args=(pid, pname)
                )

    with right_col:
        if patient_id:
            header_col, call_col = st.columns([6, 1])
            with header_col:
                st.markdown(f"### 💬 Chat with 👤 {patient_name}")
            with call_col:
                if st.button("📞 Call", key="call_btn"):
                    start_call(patient_id)
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
                msg_col, send_col = st.columns([16, 2])
                with msg_col:
                    st.text_input("Type a message...", key="chat_input", label_visibility="collapsed")
                with send_col:
                    st.form_submit_button("Send", key="send_btn", on_click=lambda: send_message(patient_id))
            st_autorefresh(interval=5000, key=f"chat_refresh_{patient_id}")
        else:
            st.markdown("### 💬 No chat selected")
            st.info("Select a patient from the left panel to start chatting 💬")
