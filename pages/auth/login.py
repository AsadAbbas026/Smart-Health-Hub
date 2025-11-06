import streamlit as st
import json
from utils.auth_utils import authenticate_user

def show_login(cookies):
    st.write("### Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
        
    login_btn = st.button("Login", use_container_width=False, icon="🔒")
    
    if login_btn:
        if not email or not password:
            st.warning("⚠️ Please enter both email and password.")
        else:
            with st.spinner("Authenticating..."):
                user = authenticate_user(email, password)

            if user:
                st.session_state.user = user
                st.session_state.page = f"{user['role']}_dashboard"
                st.success(f"Welcome back, {user['email']}!")

                # --- Save user info in cookies ---
                cookies["user"] = json.dumps(user)
                cookies.save()

                st.rerun()
            else:
                st.error("❌ Invalid email or password. Please try again.")
