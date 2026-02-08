from sqlalchemy.orm import Session
from typing import Optional, Dict

class AgentRepository:
    """
    에이전트 엔티티를 위한 저장소 (INSERT/UPDATE/DELETE).
    비즈니스 로직과 DB 접근을 분리합니다.
    """
    
    def create_agent(self, db: Session, agent_data: Dict) -> object:
        # 지연 임포트 (Lazy Import)
        from services.ai_hub.db.tables import Agent
        
        new_agent = Agent(
            creator_id=agent_data["user_id"],
            name=agent_data.get("name", "Untitled Agent"),
            description=agent_data.get("description", ""),
            category=agent_data.get("category", "UNCATEGORIZED"),
            model_type=agent_data.get("model_type", "GPT-4"),
            parameters={}, # 기본 파라미터
            is_public=agent_data.get("visibility") == "PUBLIC",
            use_rag=(agent_data.get("use_rag") == "True")
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return new_agent
