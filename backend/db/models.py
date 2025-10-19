from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(256), unique=True, nullable=False, index=True)
    hashed_password = Column(String(512), nullable=False)
    role = Column(String(50), default="user", nullable=False)
    # --- ADD THIS LINE ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # ---------------------

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(512), nullable=False)
    filepath = Column(String(1024), nullable=False)
    vector_store_path = Column(String(1024), nullable=False)
    full_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="documents")
    chat_messages = relationship("ChatMessage", back_populates="document", cascade="all, delete-orphan")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User", back_populates="sessions")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chat_messages")
    session = relationship("ChatSession", back_populates="messages")

class ApiLog(Base):
    __tablename__ = "api_logs"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(100), nullable=False, index=True) # e.g., "Gemini", "Ollama"
    model = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    filename = Column(String(512), nullable=False) # Store filename for easy display
    level = Column(String(50), nullable=False) # e.g., "Short", "Medium", "Long"
    content = Column(Text, nullable=False)
    provider = Column(String(100)) # Which LLM generated it
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships (optional but good practice)
    owner = relationship("User")
    document = relationship("Document")