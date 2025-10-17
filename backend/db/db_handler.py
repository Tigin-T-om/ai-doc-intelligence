# backend/db/db_handler.py

import os
import shutil
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

# --- STEP 1: IMPORT MODELS FIRST ---
# This ensures that the Base object knows about all your tables before any other code runs.
from backend.db.models import Base, User, Document, ChatMessage, ChatSession

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