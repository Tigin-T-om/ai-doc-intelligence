import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment (.env)")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from backend.db.models import Base, User, Document, ChatMessage, ChatSession

def create_tables():
    Base.metadata.create_all(bind=engine)

def drop_tables():
    Base.metadata.drop_all(bind=engine)

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

# --- Chat CRUD ---
def add_chat_message(db, doc_id=None, session_id=None, role=None, content=None):
    msg = ChatMessage(
        document_id=doc_id,
        session_id=session_id,
        role=role,
        content=content
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_chat_history_by_doc(db, doc_id):
    return db.query(ChatMessage).filter(ChatMessage.document_id == doc_id).order_by(ChatMessage.created_at).all()

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
