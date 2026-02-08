from sqlalchemy.orm import Session
from typing import List, Optional

class HubRepository:
    """
    허브 쿼리용 Repository (SELECT).
    에이전트 필터링 및 검색을 처리합니다.
    """
    
    def get_all_public_agents(self, db: Session) -> List[object]:
        from services.ai_hub.db.tables import Agent
        return db.query(Agent).filter(Agent.is_public == True).all()
        
    def get_agents_by_keyword(self, db: Session, keyword: str) -> List[object]:
        from services.ai_hub.db.tables import Agent
        search_fmt = f"%{keyword}%"
        return db.query(Agent).filter(
            (Agent.dname.ilike(search_fmt)) | 
            (Agent.description.ilike(search_fmt))
        ).limit(10).all()

    def get_agent_by_id(self, db: Session, agent_id: str) -> Optional[object]:
        from services.ai_hub.db.tables import Agent
        return db.query(Agent).filter(Agent.id == agent_id).first()

    def get_agents_by_ids(self, db: Session, agent_ids: List[str]) -> List[object]:
        """IDs 리스트로 여러 에이전트를 한 번에 조회합니다."""
        from services.ai_hub.db.tables import Agent
        return db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
