import streamlit as st
import pandas as pd
import os
import json
import base64
from io import BytesIO
from docx import Document
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

from pages.util.menu import doctor_sidebar
from database.connection import SessionLocal
from database.queries.share_document_queries import get_shared_documents_for_doctor
from database.queries.doctor_queries import get_doctor_by_email


# ---------- Document Viewer ----------
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


# ---------- Shared Documents Page ----------
def show_shared_documents():
    user = st.session_state.get("user")
    if not user or user.get("role") != "doctor":
        st.error("Please log in as a doctor")
        st.session_state.page = "auth"
        st.rerun()
        return

    st.header("📁 Shared Documents", divider="gray")

    # ---------- Fetch Data ----------
    db = SessionLocal()
    doctor_id = get_doctor_by_email(user["email"]).doctor_id
    shared_records = get_shared_documents_for_doctor(doctor_id)
    db.close()

    if not shared_records:
        st.info("No shared documents available at the moment.")
        return

    # ---------- DataFrame Setup ----------
    df = pd.DataFrame(shared_records, columns=[
        "ID",
        "Patient Name",
        "Document Name",
        "Document Type",
        "Category",
        "Description",
        "File Path",
        "Doctor ID"
    ])

    df["File Path"] = df["File Path"].apply(lambda p: p.replace("\\", "/"))
    df["Actions"] = "👁️ View | ⬇️ Download"

    # ---------- AgGrid Renderer ----------
    button_renderer = JsCode("""
        class BtnCellRenderer {
            init(params) {
                this.params = params;
                this.eGui = document.createElement('div');
                this.eGui.innerHTML = `
                    <div style="display:flex; gap:6px;">
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
                        <button style="
                            background-color:#28A745;
                            color:white;
                            border:none;
                            border-radius:6px;
                            padding:4px 10px;
                            cursor:pointer;
                            font-size:14px;">
                            ⬇️ Download
                        </button>
                    </div>
                `;

                const [viewBtn, downloadBtn] = this.eGui.querySelectorAll('button');

                // View button
                viewBtn.addEventListener('click', () => {
                    const payload = {
                        action: 'view',
                        file: params.data["File Path"],
                        name: params.data["Document Name"]
                    };
                    console.log("👁️ View clicked:", payload);
                    window.top.postMessage({ type: "view_file", detail: payload }, "*");
                });

                // Download button
                downloadBtn.addEventListener('click', () => {
                    const payload = {
                        action: 'download',
                        file: params.data["File Path"],
                        name: params.data["Document Name"]
                    };
                    console.log("⬇️ Download clicked:", payload);
                    window.top.postMessage({ type: "download_file", detail: payload }, "*");
                });
            }
            getGui() { return this.eGui; }
        }
    """)

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, cellStyle={'fontSize': '16px'})
    gb.configure_column("File Path", hide=True)
    gb.configure_column("Doctor ID", hide=True)
    gb.configure_column("Actions", cellRenderer=button_renderer)
    grid_options = gb.build()

    # ---------- Render Grid ----------
    try:
        AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.NO_UPDATE,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            height=440,
        )
    except Exception as e:
        print(f"[⚠️ AgGrid Rendering Warning] {e}")

    # ---------- JS → Streamlit Bridge ----------
    js_bridge_script = """
    <script>
    (function() {
        console.log("✅ Initializing SharedDocuments JS bridge");

        const topWindow = window.top;
        if (!topWindow.hasSharedDocListener) {
            topWindow.hasSharedDocListener = true;

            topWindow.addEventListener("message", (e) => {
                console.log("📨 JS bridge received message:", e.data);

                if (!e.data || !e.data.type) return;
                const detail = e.data.detail || {};

                if (e.data.type === "view_file") {
                    const params = new URLSearchParams(topWindow.location.search);
                    params.set(e.data.type, JSON.stringify(detail));
                    const newUrl = topWindow.location.pathname + '?' + params.toString();
                    topWindow.history.replaceState({}, '', newUrl);
                    topWindow.dispatchEvent(new Event('popstate'));
                }

                else if (e.data.type === "download_file") {
                    console.log("⬇️ JS bridge setting param for:", detail.file);
                    const params = new URLSearchParams(topWindow.location.search);
                    params.set("download_file", JSON.stringify(detail));
                    const newUrl = topWindow.location.pathname + '?' + params.toString();
                    topWindow.history.replaceState({}, '', newUrl);
                    topWindow.dispatchEvent(new Event('popstate'));
                }
            });
        }
    })();
    </script>
    """
    st.components.v1.html(js_bridge_script, height=0)

    # ---------- Handle "View" ----------
    query = st.query_params
    js_event_view = query.get("view_file")

    if js_event_view:
        try:
            data = json.loads(js_event_view)
            if data and "file" in data and "name" in data:
                view_attachment_dialog(data["file"], data["name"])
                del query["view_file"]
                st.query_params = query
        except Exception as e:
            st.error(f"Error loading document: {e}")

    # ---------- Handle "Download" ----------
    query = st.query_params
    js_event_download = query.get("download_file")

    if js_event_download:
        try:
            data = json.loads(js_event_download)
            file_path = data["file"]
            file_name = data["name"]

            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    content = f.read()

                import base64, mimetypes
                b64_data = base64.b64encode(content).decode()

                # ✅ Determine MIME type from extension
                ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    ".pdf": "application/pdf",
                    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ".txt": "text/plain",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".mp3": "audio/mpeg",
                    ".wav": "audio/wav",
                    ".ogg": "audio/ogg",
                    ".mp4": "video/mp4",
                    ".webm": "video/webm",
                }
                mime_type = mime_types.get(ext, "application/octet-stream")

                # ✅ Restrict allowed extensions
                allowed_exts = set(mime_types.keys())
                if ext not in allowed_exts:
                    st.warning(f"❌ File type '{ext}' is not allowed for download.")
                else:
                    download_script = f"""
                    <script>
                        const a = document.createElement('a');
                        a.href = "data:{mime_type};base64,{b64_data}";
                        a.download = "{file_name}";
                        a.click();
                    </script>
                    """
                    st.components.v1.html(download_script, height=0)
            else:
                st.error(f"File not found: {file_path}")

            del query["download_file"]
            st.query_params = query

        except Exception as e:
            st.error(f"Error downloading document: {e}")

