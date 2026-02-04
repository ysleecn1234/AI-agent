from sqlalchemy.orm import Session
from typing import List, Optional

class HubRepository:
    """
    Repository for Hub Queries (SELECT).
    Handles filtering and searching agents.
    """
    
    def get_all_public_agents(self, db: Session) -> List[object]:
        from app.models import Agent
        return db.query(Agent).filter(Agent.is_public == True).all()
        
    def get_agents_by_keyword(self, db: Session, keyword: str) -> List[object]:
        from app.models import Agent
        search_fmt = f"%{keyword}%"
        return db.query(Agent).filter(
            (Agent.dname.ilike(search_fmt)) | 
            (Agent.description.ilike(search_fmt))
        ).limit(10).all()

    def get_agent_by_id(self, db: Session, agent_id: str) -> Optional[object]:
        from app.models import Agent
        return db.query(Agent).filter(Agent.id == agent_id).first()
