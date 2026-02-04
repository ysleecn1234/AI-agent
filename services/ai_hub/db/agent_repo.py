from sqlalchemy.orm import Session
from typing import Optional, Dict

class AgentRepository:
    """
    Repository for Agent Entity (INSERT/UPDATE/DELETE).
    Separates DB access from business logic.
    """
    
    def create_agent(self, db: Session, agent_data: Dict) -> object:
        # Lazy Import
        from app.models import Agent
        
        new_agent = Agent(
            creator_id=agent_data["user_id"],
            name=agent_data.get("name", "Untitled Agent"),
            description=agent_data.get("description", ""),
            category=agent_data.get("category", "UNCATEGORIZED"),
            model_type=agent_data.get("model_type", "GPT-4"),
            parameters={}, # Default params
            is_public=agent_data.get("visibility") == "PUBLIC",
            use_rag=(agent_data.get("use_rag") == "True")
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return new_agent
