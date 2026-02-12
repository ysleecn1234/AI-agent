from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

class HubRepository:
    """
    허브 쿼리용 Repository (SELECT).
    에이전트 필터링 및 검색을 처리합니다.
    """
    
    def get_all_public_agents(self, db: Session) -> List[object]:
        from services.ai_hub.db.tables import Agent
        return db.query(Agent).filter(Agent.is_public != "PRIVATE").all()
        
    def get_agents_by_keyword(self, db: Session, keyword: str) -> List[object]:
        from services.ai_hub.db.tables import Agent
        search_fmt = f"%{keyword}%"
        return db.query(Agent).filter(
            (Agent.name.ilike(search_fmt)) |  
            (Agent.description.ilike(search_fmt))
        ).limit(10).all()

    def get_agent_by_id(self, db: Session, agent_id: str) -> Optional[object]:
        from services.ai_hub.db.tables import Agent
        return db.query(Agent).filter(Agent.id == agent_id).first()

    def get_agents_by_ids(self, db: Session, agent_ids: List[str]) -> List[object]:
        """IDs 리스트로 여러 에이전트를 한 번에 조회합니다."""
        from services.ai_hub.db.tables import Agent
        return db.query(Agent).filter(Agent.id.in_(agent_ids)).all()

    # ==================== 로깅 메서드 ====================
    
    def log_activity(
        self,
        db: Session,
        user_id: str,
        action: str,
        details: dict = None,
        success: bool = True,
        duration_ms: int = None,
        doc_id: str = None,
        user_name: str = None
    ):
        """활동 로그 기록"""
        from services.ai_hub.db.tables import ActivityLog
        
        log = ActivityLog(
            user_id=uuid.UUID(user_id),
            action=action,
            details=details or {},
            success=success,
            duration_ms=duration_ms,
            doc_id=uuid.UUID(doc_id) if doc_id else None,
            user_name=user_name
        )
        
        db.add(log)
        db.commit()
    
    def log_cost(
        self,
        db: Session,
        user_id: str,
        operation: str,
        tokens_used: int = 0,
        cost_usd: float = 0,
        cost_krw: float = 0,
        doc_id: str = None,
        model_name: str = ""
    ):
        """비용 로그 기록"""
        from services.ai_hub.db.tables import CostLog
        
        log = CostLog(
            user_id=uuid.UUID(user_id),
            doc_id=uuid.UUID(doc_id) if doc_id else None,
            operation=operation,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            cost_krw=cost_krw,
            model_name=model_name
        )
        
        db.add(log)
        db.commit()
