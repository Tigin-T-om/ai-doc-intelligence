import os
import fitz
import streamlit as st
from backend.rag_pipeline import split_text_into_chunks, create_vector_store
from backend.db.db_handler import get_session, get_document_by_name_for_user, add_document_for_user

def render_upload_view(current_user_id, uploaded_files):
    if uploaded_files:
        processed_any = False
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name.strip()

            # ✅ Check once before processing
            with get_session() as db:
                existing_doc = get_document_by_name_for_user(db, current_user_id, filename)

            if existing_doc:
                # Only warn if it's truly in DB
                st.info(f"ℹ️ '{filename}' is already uploaded and indexed.")
                continue

            # --- Save file ---
            user_doc_dir = os.path.join("documents", str(current_user_id))
            os.makedirs(user_doc_dir, exist_ok=True)
            file_path = os.path.join(user_doc_dir, filename)

            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            # --- Extract text ---
            doc_text = "".join([page.get_text() for page in fitz.open(file_path)])
            chunks = split_text_into_chunks(doc_text)

            # --- Progress bar ---
            progress_bar = st.progress(0, text=f"Indexing {filename}...")
            total = len(chunks)
            for i in range(1, total + 1):
                progress_bar.progress(
                    int((i / total) * 100),
                    text=f"Indexing {filename}... {i}/{total}"
                )

            # --- Create FAISS index ---
            _, vector_store_path = create_vector_store(
                chunks,
                f"{current_user_id}_{filename}"
            )

            # --- Save in DB immediately ---
            with get_session() as db:
                add_document_for_user(db, current_user_id, filename, file_path, vector_store_path, doc_text)
                db.commit()  # ✅ ensure persistence before rerun

            progress_bar.empty()
            st.success(f"✅ Uploaded & indexed '{filename}'.")
            processed_any = True

        if processed_any:
            st.rerun()

    else:
        st.header("Upload & Manage Your Documents")
        st.info("👈 Upload a PDF from the sidebar to begin.")
