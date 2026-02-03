from sqlalchemy import Column, String, Boolean, Text, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .database import Base

# ==========================================
# 1. Users Table (Identity & Profile)
# ==========================================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    department = Column(String(50), nullable=False)
    
    # Personalization Memory (JSONB for flexibility)
    memory = Column(JSONB, nullable=True) 

    # Relationships
    agents = relationship("Agent", back_populates="creator")
    chat_logs = relationship("ChatLog", back_populates="user")

# ==========================================
# 2. Agents Table (Unified Repository)
# ==========================================
class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Basic Info
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # e.g., MARKETING, CODING
    
    # Prompting Logic
    system_prompt = Column(Text, nullable=False)
    input_example = Column(Text, nullable=True)
    output_example = Column(Text, nullable=True)

    # Configuration & Visibility
    is_public = Column(String(20), nullable=False, default="PRIVATE")  # TEAM, PRIVATE
    model_type = Column(String(50), nullable=False, default="AUTO")    # AUTO, GPT4, etc.

    # RAG Integration Strategy
    use_rag = Column(Boolean, nullable=False, default=False)
    linked_knowledge_ids = Column(JSONB, nullable=True)  # List of Doc IDs [ "doc-1", "doc-2" ]

    # Relationships
    creator = relationship("User", back_populates="agents")

# ==========================================
# 3. Chat Logs Table (Activity History)
# ==========================================
class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    session_id = Column(String, nullable=False, index=True)
    user_input = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="chat_logs")
