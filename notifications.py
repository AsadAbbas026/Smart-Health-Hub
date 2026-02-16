# notifications.py
import streamlit as st

# Ask permission once per browser
st.components.v1.html("""
<script>
(async () => {
  if (!("Notification" in window)) return;

  if (!localStorage.getItem("notifs_enabled")) {
    const permission = await Notification.requestPermission();
    if (permission === "granted") {
      localStorage.setItem("notifs_enabled", "true");
    }
  }
})();
</script>
""", height=0)


def queue_notification(title, body):
    st.session_state.setdefault("notifications", [])
    st.session_state.notifications.append({
        "title": title,
        "body": body
    })


def render_notifications():
    for n in st.session_state.get("notifications", []):
        print(f"Notifications: {n}")
        st.components.v1.html(f"""
        <script>
        if (Notification.permission === "granted") {{
            new Notification("{n['title']}", {{
                body: "{n['body']}"
            }});
        }}
        </script>
        """, height=0)

    # Clear immediately (IMPORTANT)
    st.session_state.notifications = []
