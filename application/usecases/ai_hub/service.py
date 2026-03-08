from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from services.ai_hub.db.tables import Agent

class AIHubService:
    def __init__(self):
        pass

    def get_visible_agents(self, db: Session, user_id: str, sort_by: str = "newest", category: Optional[str] = None) -> List[Agent]:
        """
        Fetch agents based on visibility rules:
        - PUBLIC: Everyone
        - TEAM: Only users in the same department as the creator
        - PRIVATE: Only the creator
        """
        from application.database import User
        from sqlalchemy import or_
        
        user = db.query(User).filter(User.id == user_id).first()
        user_dept = user.department if user else ""

        query = db.query(Agent).join(User, Agent.creator_id == User.id).filter(
            or_(
                Agent.is_public == "PUBLIC",
                Agent.creator_id == user_id,
                (Agent.is_public == "TEAM") & (User.department == user_dept)
            )
        )

        # Filter by Category
        if category:
            query = query.filter(Agent.category == category)

        # Sorting
        if sort_by == "newest":
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
