# notifications.py
import streamlit as st

# Inject JS to ask for notification permission only once
st.components.v1.html("""
<script>
(async () => {
  if (!("Notification" in window)) return;  // Browser does not support

  // Check localStorage to avoid asking every time
  if (!localStorage.getItem("notifs_enabled")) {
    const permission = await Notification.requestPermission();
    if (permission === "granted") {
      localStorage.setItem("notifs_enabled", "true");
      console.log("✅ Notifications enabled");
    } else {
      console.warn("Notifications permission denied");
    }
  }
})();
</script>
""", height=0)

def trigger_notification(title, body):
    """Show a notification in the browser while the page is open."""
    js_code = f"""
    <script>
    if (Notification.permission === "granted") {{
        new Notification("{title}", {{
            body: "{body}",
            icon: "https://cdn-icons-png.flaticon.com/512/565/565547.png"
        }});
    }}
    </script>
    """
    st.components.v1.html(js_code, height=0)
