from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from services.ai_hub.db.tables import Agent

class AIHubService:
    def __init__(self):
        pass

    def get_public_agents(self, db: Session, sort_by: str = "newest", category: Optional[str] = None) -> List[Agent]:
        """
        Fetch agents that are marked as 'TEAM' or 'PUBLIC' (Public).
        """
        query = db.query(Agent).filter(Agent.is_public.in_(["TEAM", "PUBLIC"]))

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

    def delete_agent(self, db: Session, agent_id: str, requester_id: str) -> dict:
        """
        Agent 삭제 처리 (권한 확인 포함)
        Result: {"success": bool, "message": str, "code": int}
        """
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        # 1. 존재 여부 확인
        if not agent:
            return {"success": False, "message": "Agent not found", "code": 404}
            
        # 2. 공식 에이전트 보호 (삭제 불가)
        if agent.creator and agent.creator.name == "AI Agent 공식":
            return {"success": False, "message": "시스템 공식 에이전트는 삭제할 수 없습니다.", "code": 403}
            
        # 3. 소유권 확인 (본인이 만든 것만 삭제 가능)
        # UUID 비교 시 문자열 변환 필요할 수 있음
        if str(agent.creator_id) != str(requester_id):
            return {"success": False, "message": "삭제 권한이 없습니다. (본인이 만든 에이전트만 삭제 가능)", "code": 403}
            
        # 4. 삭제 수행
        db.delete(agent)
        db.commit()
        return {"success": True, "message": "Agent deleted successfully", "code": 204}

hub_service = AIHubService()
