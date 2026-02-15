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
            # parameters={}, # [Fix] 존재하지 않는 컬럼 제거
            is_public=agent_data.get("visibility", "PRIVATE"),
            use_rag=(agent_data.get("use_rag") == "True"),
            system_prompt=agent_data.get("system_prompt", ""),
            input_example=agent_data.get("input_example", ""),
            output_example=agent_data.get("output_example", "")
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return new_agent

    def get_agent(self, db: Session, agent_id: str) -> Optional[object]:
        """
        에이전트를 조회합니다.
        
        Args:
            agent_id: 조회할 에이전트 UUID
            
        Returns:
            Agent 객체 또는 None
        """
        from services.ai_hub.db.tables import Agent
        return db.query(Agent).filter(Agent.id == agent_id).first()

    def delete_agent(self, db: Session, agent_id: str) -> bool:
        """
        에이전트를 삭제합니다.
        
        Args:
            agent_id: 삭제할 에이전트 UUID
            
        Returns:
            성공 시 True, 실패(없음) 시 False
        """
        from services.ai_hub.db.tables import Agent
        
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False
            
        db.delete(agent)
        db.commit()
        return True
