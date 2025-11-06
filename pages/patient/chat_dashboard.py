import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space

def show_chat_dashboard():
    st.set_page_config(page_title="Chat Dashboard", layout="wide")

    # --- Hide sidebar globally ---
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        div.block-container {padding-top: 0.2rem !important;}
        .return-btn {
            background-color: #007bff;
            color: white;
            padding: 8px 15px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
            margin-bottom: 5px;
        }
        .return-btn:hover {
            background-color: #0056b3;
        }
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

    # --- Return button ---
    if st.button("🔙 Return to Smart Health Hub", key="return_btn"):
        user = st.session_state.get("user", {})
        st.session_state.page = "patient_dashboard" if user.get("role", "").lower() == "patient" else "doctor_dashboard"
        st.rerun()

    st.markdown("## 💬 Chat Dashboard")

    # --- Layout ---
    left_col, right_col = st.columns([1.2, 2.8])

    # ------------------------------------------------------------------
    # LEFT: Chat History
    # ------------------------------------------------------------------
    with left_col:
        st.markdown("### Recent Chats")
        st.markdown("""
            <div style='background-color:#f8f9fa; border-radius:10px; padding:10px; height:550px; overflow-y:auto;'>
                <div style='padding:10px; border-bottom:1px solid #ddd; cursor:pointer;'>🧑‍⚕️ Dr. Ahmed</div>
                <div style='padding:10px; border-bottom:1px solid #ddd; cursor:pointer;'>🧑‍⚕️ Dr. Sara</div>
                <div style='padding:10px; border-bottom:1px solid #ddd; cursor:pointer;'>🧑‍⚕️ Dr. Bilal</div>
                <div style='padding:10px; border-bottom:1px solid #ddd; cursor:pointer;'>🧑‍⚕️ Dr. Zain</div>
            </div>
        """, unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # RIGHT: Chat Window
    # ------------------------------------------------------------------
    with right_col:
        st.markdown("### Chat with 🧑‍⚕️ Dr. Ahmed")

        # Initialize message history
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {"sender": "patient", "text": "Hello Doctor 👋"},
                {"sender": "doctor", "text": "Hi there! How are you feeling today? 🙂"},
                {"sender": "patient", "text": "Feeling much better, thanks to your advice."},
                {"sender": "doctor", "text": "That’s great to hear! Make sure to rest properly. This is a longer message to test scrolling in the window."},
            ]

        # Build HTML chat bubbles
        chat_html = "<div class='chat-box'>"
        for msg in st.session_state.chat_messages:
            if msg["sender"] == "doctor":
                chat_html += f"<div class='chat-bubble-left'><div>{msg['text']}</div></div>"
            else:
                chat_html += f"<div class='chat-bubble-right'><div>{msg['text']}</div></div>"
        chat_html += "</div>"

        # Render chat area
        st.markdown(chat_html, unsafe_allow_html=True)

        add_vertical_space(1)

        # --- Input and send ---
        msg_col1, msg_col2 = st.columns([5, 1])
        with msg_col1:
            new_message = st.text_input(
                "Type a message...",
                key="chat_input",
                label_visibility="collapsed",
                placeholder="Type a message and press Enter..."
            )
        with msg_col2:
            send = st.button("Send 📤", key="send_button")

        if new_message or send:
            if new_message.strip():
                st.session_state.chat_messages.append({"sender": "patient", "text": new_message.strip()})
                st.session_state.chat_input = ""
                st.rerun()

# ------------------------------------------------------------------
# Run app
# ------------------------------------------------------------------
if __name__ == "__main__":
    if "user" not in st.session_state:
        st.session_state.user = {"role": "patient"}
    if "page" not in st.session_state:
        st.session_state.page = "chat_dashboard"
    if st.session_state.page == "chat_dashboard":
        show_chat_dashboard()
