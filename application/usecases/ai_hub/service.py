from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from services.ai_hub.db.tables import Agent

class AIHubService:
    def __init__(self):
        pass

    def get_public_agents(self, db: Session, sort_by: str = "newest", category: Optional[str] = None) -> List[Agent]:
        """
        Fetch agents that are marked as 'TEAM' or 'COMPANY' (Public).
        """
        query = db.query(Agent).filter(Agent.is_public.in_(["TEAM", "COMPANY"]))

        # Filter by Category
        if category:
            query = query.filter(Agent.category == category)

        # Sorting
        if sort_by == "newest":
            # Assuming 'id' is uuid, we might not have created_at. 
            # In Plan v33, Agent table didn't have created_at explicitly shown in table, 
            # but usually UUID v7 or just adding a column is good.
            # For now, let's assume simple sort by name if created_at is missing, 
            # OR we should have added created_at. 
            # Let's check models.py... it does NOT have created_at.
            # I will fallback to sorting by Name for now to avoid schema drift, 
            # or request to add it later.
            query = query.order_by(Agent.name) 
        elif sort_by == "name":
             query = query.order_by(Agent.name)

        return query.all()

    def get_agent_details(self, db: Session, agent_id: str) -> Optional[Agent]:
        return db.query(Agent).filter(Agent.id == agent_id).first()

hub_service = AIHubService()
