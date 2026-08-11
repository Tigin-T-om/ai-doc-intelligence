# backend/db/db_handler.py

import os
import shutil
from contextlib import contextmanager
from sqlalchemy import create_engine, func # Added func import
from sqlalchemy.orm import sessionmaker, joinedload # Added joinedload import
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
# --- STEP 1: IMPORT MODELS FIRST ---
from backend.db.models import Base, User, Document, ChatMessage, ChatSession, ApiLog, Summary

# --- STEP 2: CONFIGURE AND CONNECT TO THE DATABASE ---
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import streamlit as st

# Load .env for local
load_dotenv()

# Try secrets (for Streamlit Cloud)
DATABASE_URL = None
try:
    if hasattr(st, "secrets"):
        DATABASE_URL = st.secrets.get("DATABASE_URL", None)
except Exception:
    DATABASE_URL = None

# Fallback to local .env
if not DATABASE_URL:
    DATABASE_URL = os.getenv("DATABASE_URL")

# Final check
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env or Streamlit secrets")

# Database engine
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- STEP 3: DEFINE DATABASE FUNCTIONS ---

def create_tables():
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================================
#          USER FUNCTIONS
# ==================================
def get_all_users(db):
    """
    Fetches all users, eagerly loading related data, ordered by creation date desc.
    """
    return db.query(User)\
             .options(joinedload(User.documents))\
             .options(joinedload(User.chat_sessions))\
             .options(joinedload(User.summaries))\
             .order_by(User.created_at.desc())\
             .all()

def get_user_by_username(db, username):
    """Fetches a single user by username."""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db, email):
    """Fetches a single user by email."""
    return db.query(User).filter(User.email == email).first()

def add_user(db, username, hashed_password, first_name, last_name, email):
    """Adds a new user to the database after checking for duplicates."""
    # Check if username or email already exists
    if get_user_by_username(db, username):
        raise ValueError("User with this username already exists.")
    if get_user_by_email(db, email):
        raise ValueError("User with this email already exists.")

    user = User(
        username=username,
        hashed_password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        email=email
        # role defaults to 'user' in the model
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as e: # Catch specific DB errors
        db.rollback()
        # Log the detailed error e for debugging if needed
        raise ValueError(f"Database error during registration. Check logs. Error: {e}")
    except Exception as e: # Catch any other unexpected errors
        db.rollback()
        raise ValueError(f"An unexpected error occurred during registration: {e}")
    db.refresh(user)
    return user

def get_recent_users(db, limit=5):
    """Fetches the most recently registered users."""
    return db.query(User).order_by(User.created_at.desc()).limit(limit).all()

def update_user_role(db, user_id, new_role):
    """Updates a user's role in the database."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.role = new_role
        db.commit()
        return True
    return False

def delete_user_by_id(db, user_id):
    """Deletes a user and relies on cascade deletes for related data."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user) # Assumes cascade="all, delete-orphan" is set correctly in User model
        db.commit()
        return True
    return False

# ==================================
#        DOCUMENT FUNCTIONS
# ==================================
def add_document_for_user(db, user_id, filename, filepath, vector_store_path, full_text):
    """Adds a new document record for a user."""
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
    """Fetches a specific document for a user by filename."""
    return db.query(Document).filter(Document.user_id == user_id, Document.filename == filename).first()

def get_documents_by_user(db, user_id):
    """Fetches all documents belonging to a specific user."""
    return db.query(Document).filter(Document.user_id == user_id).order_by(Document.created_at.desc()).all() # Added ordering

def get_all_documents(db):
    """Fetches all documents from the database."""
    return db.query(Document).order_by(Document.created_at.asc()).all() # Added ordering

def get_recent_documents(db, limit=5):
    """Fetches the most recently uploaded documents across all users."""
    return db.query(Document).order_by(Document.created_at.desc()).limit(limit).all()

def count_documents_by_user(db, user_id):
    """Counts total documents for a single user."""
    return db.query(Document).filter(Document.user_id == user_id).count()

def get_recent_documents_by_user(db, user_id, limit=5):
    """Fetches the most recent documents for a single user."""
    return db.query(Document).filter(Document.user_id == user_id).order_by(Document.created_at.desc()).limit(limit).all()

def rename_document(db, doc_id, user_id, new_filename):
    """Renames a document's metadata and associated files/folders."""
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc: return False, "Document not found or permission denied."

    if "/" in new_filename or "\\" in new_filename: return False, "Invalid filename: contains path separators."
    if not new_filename.lower().endswith(".pdf"): new_filename += ".pdf"

    old_filepath = doc.filepath
    old_vector_store_path = doc.vector_store_path
    old_filename = doc.filename

    base_dir = os.path.dirname(old_filepath)
    new_filepath = os.path.join(base_dir, new_filename)
    new_vector_store_name = f"{user_id}_{new_filename}"
    new_vector_store_path = os.path.join("backend/vector_store", f"faiss_index_{new_vector_store_name}")

    existing_check = db.query(Document).filter(Document.user_id == user_id, Document.filename == new_filename).first()
    if existing_check: return False, f"A document named '{new_filename}' already exists."

    try:
        if os.path.exists(old_filepath): os.rename(old_filepath, new_filepath)
        if os.path.exists(old_vector_store_path): os.rename(old_vector_store_path, new_vector_store_path)

        doc.filename = new_filename
        doc.filepath = new_filepath
        doc.vector_store_path = new_vector_store_path
        db.commit()
        return True, f"Renamed '{old_filename}' to '{new_filename}'."
    except Exception as e:
        db.rollback()
        # Attempt to revert file renames
        if os.path.exists(new_filepath) and not os.path.exists(old_filepath): os.rename(new_filepath, old_filepath)
        if os.path.exists(new_vector_store_path) and not os.path.exists(old_vector_store_path): os.rename(new_vector_store_path, old_vector_store_path)
        return False, f"Error during renaming: {e}"

def delete_document_by_id(db, doc_id):
    """Deletes a document record, files, vector store, and related summaries/messages."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc: return False, "Document not found."

    filepath = doc.filepath
    vector_store_path = doc.vector_store_path

    try:
        # Explicitly delete related items first (safer than relying purely on cascade)
        db.query(Summary).filter(Summary.document_id == doc_id).delete()
        db.query(ChatMessage).filter(ChatMessage.document_id == doc_id).delete()
        # Now delete the document itself
        db.delete(doc)
        db.commit() # Commit DB deletions

        # Delete files after successful DB commit
        if os.path.exists(filepath): os.remove(filepath)
        if os.path.exists(vector_store_path): shutil.rmtree(vector_store_path)
        return True, f"Successfully deleted {doc.filename} and associated data."
    except Exception as e:
        db.rollback()
        return False, f"Error during deletion: {e}"

# ==================================
#       CHAT SESSION FUNCTIONS
# ==================================
def create_chat_session(db, user_id, name="New Chat"):
    """Creates a new chat session for a user."""
    session = ChatSession(user_id=user_id, name=name)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_chat_sessions_by_user(db, user_id):
    """Fetches all chat sessions for a specific user, ordered by recent first."""
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).all()

def get_all_chat_sessions(db):
    """Fetches all chat sessions from the database, ordered by creation."""
    return db.query(ChatSession).order_by(ChatSession.created_at.asc()).all()

def get_chat_session(db, session_id):
    """Fetches a specific chat session by its ID, including messages."""
    # Eager load messages to prevent lazy loading errors later
    return db.query(ChatSession).options(joinedload(ChatSession.messages)).filter(ChatSession.id == session_id).first()

def add_message_to_session(db, session_id, role, content):
    """Adds a new message to a specific chat session."""
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
    """Deletes a chat session (relies on cascade for messages)."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        db.delete(session) # Assumes cascade="all, delete-orphan" on ChatSession.messages
        db.commit()
        return True
    return False

def count_chat_sessions_by_user(db, user_id):
    """Counts total chat sessions for a single user."""
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).count()

def get_recent_chat_sessions_by_user(db, user_id, limit=5):
    """Fetches the most recent chat sessions for a single user."""
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).limit(limit).all()

# ==================================
#         SUMMARY FUNCTIONS
# ==================================
def add_summary(db, user_id, document_id, filename, level, content, provider):
    """Saves a generated summary to the database."""
    summary = Summary(
        user_id=user_id, document_id=document_id, filename=filename,
        level=level, content=content, provider=provider
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary

def get_summaries_by_user(db, user_id):
    """Fetches all summaries generated by a specific user."""
    return db.query(Summary).filter(Summary.user_id == user_id).order_by(Summary.created_at.desc()).all()

def get_all_summaries(db):
    """Fetches all summaries from the database."""
    return db.query(Summary).order_by(Summary.created_at.asc()).all()

def delete_summary_by_id(db, summary_id):
    """Deletes a specific summary."""
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if summary:
        db.delete(summary)
        db.commit()
        return True
    return False

# ==================================
#        API LOG FUNCTIONS
# ==================================
def add_api_log(db, provider, model):
    """Adds a new API call log entry to the database."""
    log_entry = ApiLog(provider=provider, model=model)
    db.add(log_entry)
    db.commit()

def get_api_logs_last_n_days(db, days=30):
    """Fetches all API logs from the last N days using timezone-aware comparison."""
    time_threshold = datetime.now(timezone.utc) - timedelta(days=days)
    return db.query(ApiLog).filter(ApiLog.created_at >= time_threshold).order_by(ApiLog.created_at.desc()).all() # Added ordering

# ==================================
#     PLATFORM-WIDE COUNTS
# ==================================
def count_total_users(db):
    """Counts the total number of registered users."""
    return db.query(User).count()

def count_total_documents(db):
    """Counts the total number of documents uploaded."""
    return db.query(Document).count()

def count_total_chat_sessions(db):
    """Counts the total number of chat sessions created."""
    return db.query(ChatSession).count()

def count_users_by_role(db):
    """Counts users grouped by their role."""
    return db.query(User.role, func.count(User.id)).group_by(User.role).all()

def count_recent_chat_sessions(db, hours=24):
    """Counts chat sessions created in the last N hours using timezone-aware comparison."""
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
    # Ensure ChatSession.created_at is timezone-aware or consistently naive UTC in the model
    # If ChatSession.created_at is naive, this comparison might behave unexpectedly
    # For naive: time_threshold_naive = datetime.utcnow() - timedelta(hours=hours)
    return db.query(ChatSession).filter(ChatSession.created_at >= time_threshold).count()

# ==================================
#     RECENT ACTIVITY FEEDS
# ==================================
# (get_recent_users, get_recent_documents are already in their sections)
def get_recent_chat_sessions(db, limit=5):
     """Fetches the most recent chat sessions across all users."""
     return db.query(ChatSession).order_by(ChatSession.created_at.desc()).limit(limit).all()