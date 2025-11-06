import streamlit as st
from streamlit_option_menu import option_menu

PATIENT_PAGE_TO_MENU = {
    "chat_dashboard": "Chats",  # <-- New menu item
    "patient_dashboard": "Dashboard",
    "book_appointment": "Book Appointment",
    "your_appointments": "Your Appointments",
    "health_records": "Health Records",
    "prescriptions": "Prescriptions",
    "profile": "Profile",
    "logout": "Logout",
}

# For doctors
DOCTOR_PAGE_TO_MENU = {
    "chat_dashboard": "Chats",  # <-- New menu item
    "doctor_dashboard": "Dashboard",
    "schedule": "Schedule",
    "appointments": "Appointments",
    "treatments": "Treatments",
    "shared_documents": "Shared Documents",
    "prescriptions": "Prescriptions",
    "profile": "Profile",
    "logout": "Logout",
}


def get_default_index(page_key_to_menu_map):
    """Calculates the default_index for the option_menu based on current session state page."""
    current_page = st.session_state.get("page")
    menu_options = list(page_key_to_menu_map.values())
    
    # Get the menu option that corresponds to the current session state page key
    selected_menu_option = page_key_to_menu_map.get(current_page)
    
    # Find the index of that menu option. Default to 0 (Dashboard) if not found.
    try:
        default_index = menu_options.index(selected_menu_option)
    except ValueError:
        default_index = 0 # Default to the first item (Dashboard)
    
    return default_index


def patient_sidebar(): 
    """Render the sidebar menu for patients."""
    # Get the dynamically calculated default index
    default_index = get_default_index(PATIENT_PAGE_TO_MENU)
    
    with st.sidebar:
        selected = option_menu(
            menu_title="Patient Menu",
            options=list(PATIENT_PAGE_TO_MENU.values()), # Use values as options
            icons=[
                "chat-dots",
                "house",
                "calendar-plus",
                "calendar-check",
                "file-medical",
                "prescription2",
                "person",
                "box-arrow-right",
            ],
            # Pass the dynamically calculated index value here
            default_index=default_index, 
            key="patient_sidebar",
        )
    return selected


def doctor_sidebar():
    """Render the sidebar menu for doctors."""
    # Get the dynamically calculated default index
    default_index = get_default_index(DOCTOR_PAGE_TO_MENU)
    
    with st.sidebar:
        selected = option_menu(
            menu_title="Doctor Menu",
            options=list(DOCTOR_PAGE_TO_MENU.values()), # Use values as options
            icons=[
                "chat-dots",
                "house",
                "calendar",
                "calendar-check",
                "briefcase",
                "file-earmark-text",
                "prescription",
                "person",
                "box-arrow-right",
            ],
            # Pass the dynamically calculated index value here
            default_index=default_index, 
            key="doctor_sidebar",
        )
    return selected