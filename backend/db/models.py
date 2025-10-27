from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON # Import JSON for preferences
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True) # New field
    last_name = Column(String, nullable=True)  # New field
    email = Column(String, unique=True, index=True, nullable=False) # New field
    role = Column(String, default="user", nullable=False) # 'user' or 'admin'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Define relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan") # <--- ENSURE THIS LINE EXISTS
    summaries = relationship("Summary", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

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

    # RENAME THIS: Change 'owner' to 'user' for consistency
    user = relationship("User", back_populates="documents") # <--- CHANGED FROM 'owner' TO 'user'
    chat_messages = relationship("ChatMessage", back_populates="document", cascade="all, delete-orphan")
    # No need for summaries relationship here if handled via user or direct delete

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, default="New Chat", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship to User and ChatMessage
    user = relationship("User", back_populates="chat_sessions") # <--- ENSURE THIS 'back_populates' MATCHES
    messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, name='{self.name}')>"

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow) # This should ideally be timezone-aware if possible

    document = relationship("Document", back_populates="chat_messages")
    chat_session = relationship("ChatSession", back_populates="messages")

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

    # Relationships
    user = relationship("User", back_populates="summaries") # Link to User
    document = relationship("Document") # Link to Document