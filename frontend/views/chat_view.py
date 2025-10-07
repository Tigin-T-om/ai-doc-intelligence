# frontend/views/chat_view.py
from backend.db.db_handler import get_session, get_chat_session, add_message_to_session
import streamlit as st
from backend.llm_client import generate_text
from backend.rag_pipeline import retrieve_relevant_chunks

# frontend/views/chat_view.py

def chat_view(active_doc_obj, current_user_id):
    st.subheader("💬 Chat with Document(s)")

    if "active_session" not in st.session_state or not st.session_state.active_session:
        st.info("Start a new chat from the sidebar.")
        return

    with get_session() as db:
        session = get_chat_session(db, st.session_state.active_session)
        if not session:
            st.error("Invalid session.")
            return

        # Show old messages
        for msg in session.messages:
            with st.chat_message(msg.role):
                st.markdown(msg.content)

    # Input box
    if user_question := st.chat_input("Ask a question..."):
        with get_session() as db:
            add_message_to_session(db, session.id, "user", user_question)

        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # ✅ Safe handling of active_doc_obj
                if hasattr(active_doc_obj, "filename"):
                    doc_name_for_retrieval = f"{current_user_id}_{active_doc_obj.filename}"
                else:
                    doc_name_for_retrieval = "all"

                retrieved_docs = retrieve_relevant_chunks(user_question, doc_name=doc_name_for_retrieval)
                context = "\n\n".join([doc.page_content for doc in retrieved_docs])
                prompt = f"Answer based on context:\n\n{context}\n\nQuestion: {user_question}"
                answer, provider = generate_text(prompt)
                st.markdown(answer)
                st.caption(f"✅ Generated with {provider}")

        with get_session() as db:
            add_message_to_session(db, session.id, "assistant", answer)
