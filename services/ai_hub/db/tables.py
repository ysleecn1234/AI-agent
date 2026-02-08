from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import sys
from pathlib import Path

from application.database import Base

# 공통 모듈 임포트
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))
from services.common.db.models import ActivityLogMixin, CostLogMixin

# ==========================================
# 2. 에이전트 테이블 (통합 저장소)
# ==========================================
class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 기본 정보
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # 예: 마케팅, 코딩
    
    # 프롬프트 로직
    system_prompt = Column(Text, nullable=False)
    input_example = Column(Text, nullable=True)
    output_example = Column(Text, nullable=True)

    # 설정 및 공개 범위
    is_public = Column(String(20), nullable=False, default="PRIVATE")  # TEAM, PRIVATE
    model_type = Column(String(50), nullable=False, default="AUTO")    # AUTO, GPT4 등

    # RAG 통합 전략
    use_rag = Column(Boolean, nullable=False, default=False)
    linked_knowledge_ids = Column(JSONB, nullable=True)  # 문서 ID 목록 [ "doc-1", "doc-2" ]

    # 관계 설정
    creator = relationship("application.database.User", back_populates="agents")


# ==========================================
# 3. 로깅 테이블 (Common Mixin 사용)
# ==========================================
class ActivityLog(Base, ActivityLogMixin):
    """활동 로그 테이블 (Hub DB)"""
    __tablename__ = "activity_logs"


class CostLog(Base, CostLogMixin):
    """비용 로그 테이블 (Hub DB)"""
    __tablename__ = "cost_logs"
