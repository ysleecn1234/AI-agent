from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from application.database import Base

# ==========================================
# Chat Logs Table (Activity History)
# ==========================================
class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    session_id = Column(String, nullable=False, index=True)
    user_input = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    sources = Column(JSONB, server_default='[]')
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    # user = relationship("application.database.User", back_populates="chat_logs")  # TODO: User.chat_logs 복원 후 활성화


# ==========================================
# Chat Session Meta (Custom Title)
# ==========================================
class ChatSessionMeta(Base):
    __tablename__ = "chat_session_meta"

    session_id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    custom_title = Column(String(200), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

# ==========================================
# Misclassification Logs Table
# ==========================================
class MisclassificationLog(Base):
    __tablename__ = "misclassification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_input = Column(Text, nullable=False)           # 원본 사용자 입력
    predicted_label = Column(String(20), nullable=False) # Router가 분류한 값 (예: CASUAL)
    correct_label = Column(String(20), nullable=False)   # 사용자가 지정한 올바른 값
    confidence = Column(Float, nullable=True)             # 분류 시 확신도
    is_used = Column(Boolean, default=False)              # 재학습에 사용되었는지 여부
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

