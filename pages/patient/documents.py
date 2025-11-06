import streamlit as st
import pandas as pd
import os
from io import BytesIO
from docx import Document
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import json

from database.connection import SessionLocal
from database.queries.document_queries import (
    get_patient_id_by_email,
    fetch_documents_by_patient,
    insert_document
)
from utils.document_utils import save_uploaded_file


# ---------- Constants ----------
DOCUMENT_TYPES = [
    "Lab Report", "Imaging", "Prescription", "Medical Certificate",
    "Progress Note", "Surgical Report", "Vaccination Record", "Other"
]
PREDEFINED_CATEGORIES = [
    "Allergy Records", "Blood Test Results", "Cardiology Reports", "Dental Records"
]


# ---------- Helper Functions ----------
def add_record_dialog(patient_id):
    @st.dialog("Add Health Record", width="large")
    def record_form():
        with st.form("record_form"):
            name = st.text_input("Document Name")
            doc_type = st.selectbox("Type", DOCUMENT_TYPES)
            category = st.selectbox("Category", PREDEFINED_CATEGORIES)
            desc = st.text_area("Description")
            file = st.file_uploader(
                "Upload Document",
                type=["pdf", "jpg", "png", "txt", "docx", "mp3", "mp4"]
            )

            if st.form_submit_button("Upload"):
                if not (name and file):
                    st.error("Name and file required.")
                    return

                db = SessionLocal()
                file_path = save_uploaded_file(patient_id, name, file)
                insert_document(db, patient_id, name, doc_type, category, file_path, desc)
                st.success("Record uploaded successfully!")
                st.rerun()
    record_form()


def view_attachment_dialog(file_path, document_name):
    """Open the document in a Streamlit dialog viewer."""
    if not os.path.exists(file_path):
        st.error("File not found.")
        return

    ext = os.path.splitext(file_path)[1].lower()

    @st.dialog(f"Viewing: {document_name}", width="large")
    def dialog_view():
        if ext in [".jpg", ".jpeg", ".png"]:
            st.image(file_path, use_column_width=True)

        elif ext == ".pdf":
            with open(file_path, "rb") as f:
                st.pdf(f, height=800)

        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            st.text_area("Text File Content", content, height=500)

        elif ext == ".docx":
            with open(file_path, "rb") as f:
                document = Document(BytesIO(f.read()))
                full_text = "\n\n".join([para.text for para in document.paragraphs])
                st.text_area("DOCX Content", full_text, height=500)

        elif ext in [".mp3", ".wav", ".ogg"]:
            st.audio(file_path)

        elif ext in [".mp4", ".webm"]:
            st.video(file_path)

        else:
            st.warning(f"Unsupported file format: {ext}")
            st.write("File path:", file_path)

    dialog_view()


# ---------- Main Page ----------
def show_documents():
    user = st.session_state.get("user")
    if not user or user.get("role") != "patient":
        st.error("Please log in as a patient")
        st.session_state.page = "auth"
        st.rerun()
        return

    st.header("Health Records", divider="gray")

    db = SessionLocal()
    patient_id = get_patient_id_by_email(db, user["email"])
    records = fetch_documents_by_patient(db, patient_id)

    if not records:
        st.info("No records available")
        if st.button("Add Health Record"):
            add_record_dialog(patient_id)
        return

    # ---------- DataFrame Setup ----------
    df = pd.DataFrame(records, columns=[
        "ID", "Name", "Type", "Description", "Uploaded At", "Category", "File Path"
    ])
    df["Action"] = "👁️ View"

    # ---------- AgGrid Button Renderer ----------
    button_renderer = JsCode("""
        class BtnCellRenderer {
            init(params) {
                this.params = params;
                this.eGui = document.createElement('div');
                this.eGui.innerHTML = `
                    <button style="
                        background-color:#00AEEF;
                        color:white;
                        border:none;
                        border-radius:6px;
                        padding:4px 10px;
                        cursor:pointer;
                        font-size:14px;">
                        👁️ View
                    </button>
                `;
                this.eGui.querySelector('button').addEventListener('click', () => {
                    const payload = {
                        action: 'view',
                        file: params.data["File Path"],
                        name: params.data["Name"]
                    };
                    console.log("👀 Button clicked, posting message to top:", payload);
                    window.top.postMessage({ type: "view_file", detail: payload }, "*");
                });
            }
            getGui() { return this.eGui; }
        }
    """)

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, cellStyle={'fontSize': '16px'})
    gb.configure_column("Action", cellRenderer=button_renderer)
    grid_options = gb.build()

    # ---------- Render Grid ----------
    try:
        AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.NO_UPDATE,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            height=420,
        )
    except Exception as e:
        print(f"[⚠️ AgGrid Rendering Warning] {e}")

    # ---------- JS → Streamlit Bridge ----------
    js_bridge_script = """
    <script>
    (function() {
        console.log("✅ Initializing Streamlit → JS bridge (global listener)");

        // Attach listener on the top-level window to catch messages from AgGrid
        const topWindow = window.top;
        const currentWindow = window;

        // Avoid double-listening
        if (!topWindow.hasStreamlitViewListener) {
            topWindow.hasStreamlitViewListener = true;

            topWindow.addEventListener("message", (e) => {
                console.log("📨 Global listener triggered:", e.data);

                if (e.data && e.data.type === "view_file") {
                    const detail = e.data.detail;
                    console.log("📩 JS received document data:", detail);

                    const params = new URLSearchParams(topWindow.location.search);
                    params.set("view_file", JSON.stringify(detail));
                    const newUrl = topWindow.location.pathname + '?' + params.toString();
                    topWindow.history.replaceState({}, '', newUrl);

                    // Trigger a rerun for Streamlit to pick it up
                    topWindow.dispatchEvent(new Event('popstate'));
                }
            });
        } else {
            console.log("ℹ️ JS bridge already active");
        }
    })();
    </script>
    """
    st.components.v1.html(js_bridge_script, height=0)

    # ---------- Handle the Query Param Event ----------
    query = st.query_params
    js_event = query.get("view_file")

    if js_event:
        try:
            data = json.loads(js_event)
            if data and "file" in data and "name" in data:
                view_attachment_dialog(data["file"], data["name"])
                # Cleanup after opening
                del query["view_file"]
                st.query_params = query
        except Exception as e:
            st.error(f"Error loading document: {e}")

    # ---------- Add Record Button ----------
    st.divider()
    if st.button("➕ Add New Record"):
        add_record_dialog(patient_id)
