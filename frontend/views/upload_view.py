# frontend/views/upload_view.py
import os
import fitz # PyMuPDF
import streamlit as st
from backend.rag_pipeline import split_text_into_chunks, create_vector_store
from backend.db.db_handler import get_session, get_document_by_name_for_user, add_document_for_user, get_documents_by_user

def render_upload_view(current_user_id, uploaded_files):
    st.header("⬆️ Upload & Manage Your Documents")
    st.markdown("Add new PDF documents here. They will be processed for summarization and chat.")
    st.markdown("---")

    # --- Section to show existing documents ---
    st.subheader("Your Uploaded Documents")
    try:
        with get_session() as db:
            user_docs = get_documents_by_user(db, current_user_id)
        
        if not user_docs:
            st.info("You haven't uploaded any documents yet. Use the uploader in the sidebar to add your first PDF.")
        else:
            st.write(f"You have **{len(user_docs)}** document(s) indexed:")
            # Display documents in columns for better layout
            num_columns = 3
            cols = st.columns(num_columns)
            for i, doc in enumerate(user_docs):
                with cols[i % num_columns]:
                    st.container(border=True).markdown(f"📄 **{doc.filename}**")
            st.markdown("---")

    except Exception as e:
        st.error(f"Could not load your documents: {e}")
        st.markdown("---")


    # --- Processing Logic for New Uploads ---
    # This part mostly stays the same, but we improve feedback
    if uploaded_files:
        st.subheader("Processing New Uploads...")
        processed_any = False
        
        # Use columns for processing feedback
        num_feedback_cols = 2
        feedback_cols = st.columns(num_feedback_cols)
        feedback_col_index = 0

        for uploaded_file in uploaded_files:
            filename = uploaded_file.name.strip()
            
            # Check if document already exists
            with get_session() as db:
                existing_doc = get_document_by_name_for_user(db, current_user_id, filename)

            current_col = feedback_cols[feedback_col_index % num_feedback_cols]

            if existing_doc:
                with current_col:
                    st.info(f"ℹ️ '{filename}' is already indexed.")
                feedback_col_index += 1
                continue # Skip to the next file

            # --- Start Processing ---
            try:
                # Save file locally
                user_doc_dir = os.path.join("documents", str(current_user_id))
                os.makedirs(user_doc_dir, exist_ok=True)
                file_path = os.path.join(user_doc_dir, filename)
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())

                # Show a spinner while extracting text
                with current_col:
                    with st.spinner(f"Extracting text from '{filename}'..."):
                        doc_text = "".join([page.get_text() for page in fitz.open(file_path)])
                    
                    if not doc_text.strip():
                        st.warning(f"⚠️ No text found in '{filename}'. Skipping.")
                        if os.path.exists(file_path): # Clean up empty file
                           os.remove(file_path) 
                        feedback_col_index += 1
                        continue

                # Show a spinner while indexing
                with current_col:
                     with st.spinner(f"Indexing '{filename}'... (This may take a moment)"):
                        chunks = split_text_into_chunks(doc_text)
                        _, vector_store_path = create_vector_store(
                            chunks, 
                            f"{current_user_id}_{filename}" # Unique name for vector store
                        )
                
                # Save metadata to database
                with get_session() as db:
                    add_document_for_user(db, current_user_id, filename, file_path, vector_store_path, doc_text)
                    db.commit() # Ensure it's saved

                with current_col:
                    st.success(f"✅ Successfully indexed '{filename}'.")
                
                processed_any = True

            except Exception as e:
                # Show specific error for this file
                with current_col:
                    st.error(f"❌ Failed to process '{filename}': {e}")
                # Clean up potentially corrupt files
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.remove(file_path)
                if 'vector_store_path' in locals() and os.path.exists(vector_store_path):
                    import shutil
                    shutil.rmtree(vector_store_path)

            feedback_col_index += 1 # Move to the next column for the next file

        # Only rerun if at least one file was successfully processed
        if processed_any:
            # --- ADD THIS LINE ---
            # Clear the file uploader state before rerunning
            st.session_state.file_uploader = None 
            # ---------------------
            st.rerun() # Refresh the page to show the updated document list

    elif not user_docs: # Only show the "upload in sidebar" message if the list is empty AND no files are processing
         st.markdown("👈 **Upload a PDF using the file uploader in the sidebar to begin.**")