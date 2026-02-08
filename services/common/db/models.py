from sqlalchemy import Column, String, Integer, Boolean, DateTime, DECIMAL, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

# =========================================================
# 공통 로깅 스키마 (Mixin)
# 각 서비스는 이 Mixin을 상속받아 자신의 DB에 테이블을 생성합니다.
# =========================================================

class ActivityLogMixin:
    """활동 로그 공통 스키마 Mixin"""
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_name = Column(String(100))
    doc_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(50), nullable=False)  # 예: upload, search, chat, delete, create_draft
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    ip_address = Column(String(45))
    details = Column(JSONB, default=dict)
    duration_ms = Column(Integer)


class CostLogMixin:
    """비용 로그 공통 스키마 Mixin"""
    
    cost_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    doc_id = Column(UUID(as_uuid=True), nullable=True)
    operation = Column(String(50), nullable=False)  # 예: embedding, tagging, chat, hub_search
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(DECIMAL(10, 6), default=0)
    cost_krw = Column(DECIMAL(10, 2), default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    model_name = Column(String(50))
