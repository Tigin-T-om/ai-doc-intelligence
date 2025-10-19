# backend/db/db_handler.py

import os
import shutil
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
# --- STEP 1: IMPORT MODELS FIRST ---
# This ensures that the Base object knows about all your tables before any other code runs.
from backend.db.models import Base, User, Document, ChatMessage, ChatSession, ApiLog, Summary

# --- STEP 2: CONFIGURE AND CONNECT TO THE DATABASE ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment (.env)")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- STEP 3: DEFINE DATABASE FUNCTIONS ---

def create_tables():
    # The 'Base' object is now guaranteed to be fully populated with your models.
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- User CRUD ---
def get_all_users(db):
    return db.query(User).all()

def get_user_by_username(db, username):
    return db.query(User).filter(User.username == username).first()

def add_user(db, username, hashed_password):
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("User with this username already exists")
    db.refresh(user)
    return user

def get_recent_users(db, limit=5):
    """Fetches the most recently registered users."""
    return db.query(User).order_by(User.created_at.desc()).limit(limit).all()

# --- Document CRUD ---
def add_document_for_user(db, user_id, filename, filepath, vector_store_path, full_text):
    doc = Document(
        user_id=user_id,
        filename=filename,
        filepath=filepath,
        vector_store_path=vector_store_path,
        full_text=full_text
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_document_by_name_for_user(db, user_id, filename):
    return db.query(Document).filter(Document.user_id == user_id, Document.filename == filename).first()

def get_documents_by_user(db, user_id):
    return db.query(Document).filter(Document.user_id == user_id).all()

def get_all_documents(db):
    """Fetches all documents from the database."""
    return db.query(Document).all()

def get_recent_documents(db, limit=5):
    """Fetches the most recently uploaded documents."""
    return db.query(Document).order_by(Document.created_at.desc()).limit(limit).all()

def count_documents_by_user(db, user_id):
    """Counts total documents for a single user."""
    return db.query(Document).filter(Document.user_id == user_id).count()

def get_recent_documents_by_user(db, user_id, limit=5):
    """Fetches the most recent documents for a single user."""
    return db.query(Document).filter(Document.user_id == user_id).order_by(Document.created_at.desc()).limit(limit).all()

def rename_document(db, doc_id, user_id, new_filename):
    """
    Renames a document in the database, its PDF file, and its vector store directory.
    Validates the new filename to prevent path traversal issues.
    """
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc:
        return False, "Document not found or permission denied."

    # --- Basic Security Check ---
    # Ensure new_filename doesn't contain path separators to prevent security issues
    if "/" in new_filename or "\\" in new_filename:
        return False, "Invalid filename: contains path separators."
    # Ensure it ends with .pdf (case-insensitive)
    if not new_filename.lower().endswith(".pdf"):
        new_filename += ".pdf" # Append .pdf if missing
    # ---------------------------

    old_filepath = doc.filepath
    old_vector_store_path = doc.vector_store_path
    old_filename = doc.filename

    # Construct new paths
    base_dir = os.path.dirname(old_filepath)
    new_filepath = os.path.join(base_dir, new_filename)
    new_vector_store_name = f"{user_id}_{new_filename}"
    new_vector_store_path = os.path.join("backend/vector_store", f"faiss_index_{new_vector_store_name}")

    # Check if a file with the new name already exists for this user
    existing_check = db.query(Document).filter(Document.user_id == user_id, Document.filename == new_filename).first()
    if existing_check:
        return False, f"A document named '{new_filename}' already exists."

    try:
        # 1. Rename files/folders first (safer in case DB fails)
        if os.path.exists(old_filepath):
            os.rename(old_filepath, new_filepath)
        if os.path.exists(old_vector_store_path):
            os.rename(old_vector_store_path, new_vector_store_path)

        # 2. Update database record
        doc.filename = new_filename
        doc.filepath = new_filepath
        doc.vector_store_path = new_vector_store_path
        db.commit()

        return True, f"Renamed '{old_filename}' to '{new_filename}'."

    except Exception as e:
        db.rollback() # Rollback DB changes if file renaming failed
        # Attempt to revert file renames if they happened
        if os.path.exists(new_filepath) and not os.path.exists(old_filepath):
             os.rename(new_filepath, old_filepath)
        if os.path.exists(new_vector_store_path) and not os.path.exists(old_vector_store_path):
             os.rename(new_vector_store_path, old_vector_store_path)
        return False, f"An error occurred during renaming: {e}"

# ... (at the end of the --- Chat CRUD --- section)

def count_chat_sessions_by_user(db, user_id):
    """Counts total chat sessions for a single user."""
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).count()

def get_recent_chat_sessions_by_user(db, user_id, limit=5):
    """Fetches the most recent chat sessions for a single user."""
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).limit(limit).all()

# --- Chat CRUD ---
def create_chat_session(db, user_id, name="New Chat"):
    session = ChatSession(user_id=user_id, name=name)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_chat_sessions_by_user(db, user_id):
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).all()

def get_chat_session(db, session_id):
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()

def add_message_to_session(db, session_id, role, content):
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def update_chat_session_name(db, session_id, new_name):
    """Updates the name of a specific chat session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.name = new_name
        db.commit()
        return True
    return False

def delete_chat_session_by_id(db, session_id):
    """Deletes a chat session and its associated messages."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        db.delete(session) # Cascade delete should handle messages
        db.commit()
        return True
    return False

# --- NEW: Admin Analytics ---
def count_total_users(db):
    return db.query(User).count()

def count_total_documents(db):
    return db.query(Document).count()

def count_total_chat_sessions(db):
    return db.query(ChatSession).count()

def get_all_users(db):
    """Fetches all users from the database."""
    return db.query(User).all()

def update_user_role(db, user_id, new_role):
    """Updates a user's role in the database."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.role = new_role
        db.commit()
        return True
    return False

def delete_user_by_id(db, user_id):
    """Deletes a user and all their associated data."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def delete_document_by_id(db, doc_id):
    """
    Deletes a document from the database, its .pdf file, 
    and its vector store directory.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return False, "Document not found in database."

    filepath = doc.filepath
    vector_store_path = doc.vector_store_path

    try:
        # 1. Delete from Database
        db.delete(doc)
        db.commit()

        # 2. Delete PDF file from 'documents/'
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # 3. Delete FAISS vector store directory from 'vector_store/'
        if os.path.exists(vector_store_path):
            shutil.rmtree(vector_store_path)
            
        return True, f"Successfully deleted {doc.filename}."
    
    except Exception as e:
        db.rollback() # Rollback DB changes if file deletion fails
        return False, f"An error occurred: {e}"
    
    # --- API Log CRUD ---

def add_api_log(db, provider, model):
    """Adds a new API call log entry to the database."""
    log_entry = ApiLog(provider=provider, model=model)
    db.add(log_entry)
    db.commit()

def get_api_logs_last_n_days(db, days=30):
    """Fetches all API logs from the last N days."""
    # --- THIS LINE IS CHANGED ---
    time_threshold = datetime.now(timezone.utc) - timedelta(days=days)
    # ----------------------------
    return db.query(ApiLog).filter(ApiLog.created_at >= time_threshold).all()


# --- Summary CRUD ---

def add_summary(db, user_id, document_id, filename, level, content, provider):
    """Saves a generated summary to the database."""
    summary = Summary(
        user_id=user_id,
        document_id=document_id,
        filename=filename,
        level=level,
        content=content,
        provider=provider
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary

def get_summaries_by_user(db, user_id):
    """Fetches all summaries generated by a specific user."""
    return db.query(Summary).filter(Summary.user_id == user_id).order_by(Summary.created_at.desc()).all()

def delete_summary_by_id(db, summary_id):
    """Deletes a specific summary."""
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if summary:
        db.delete(summary)
        db.commit()
        return True
    return False

def delete_document_by_id(db, doc_id):
    """
    Deletes a document from the database, its .pdf file, its vector store,
    and any associated summaries.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return False, "Document not found in database."

    filepath = doc.filepath
    vector_store_path = doc.vector_store_path

    try:
        # 1. Delete associated summaries first
        db.query(Summary).filter(Summary.document_id == doc_id).delete()
        # 2. Delete from Database
        db.delete(doc)
        db.commit() # Commit deletion of doc and summaries

        # 3. Delete PDF file
        if os.path.exists(filepath):
            os.remove(filepath)
        # 4. Delete FAISS vector store
        if os.path.exists(vector_store_path):
            shutil.rmtree(vector_store_path)

        return True, f"Successfully deleted {doc.filename} and associated data."

    except Exception as e:
        db.rollback()
        return False, f"An error occurred during deletion: {e}"