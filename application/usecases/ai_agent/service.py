from services.ai_hub.core.agent.manager import AgentManager
from application.usecases.orchestrator.service import orchestrator

# Singleton Instance from Root Service
agent_manager = AgentManager()

class AgentService:
    """
    'App' 계층을 위한 래퍼 서비스입니다.
    실제 로직은 'root/services/ai_agent/core.py'에 위임합니다.
    """
    def __init__(self):
        pass

    async def generate_draft_from_chat(self, user_id: str, messages: list):
        print(f"[App] Requesting draft creation to AgentManager for user: {user_id}")
        
        # 1. Orchestrator에게 대화 분석 요청 (LLM이 템플릿 채움)
        template = agent_manager.get_standard_template()
        filled_template = await orchestrator.analyze_for_draft(messages, template)
        
        # 2. 분석된 intent 추출
        intent = filled_template.get("description", "")
        
        # 3. Redis에 Draft 저장
        draft_id = await agent_manager.create_draft(user_id, intent, messages)
        
        # 4. 분석 결과로 Draft 업데이트
        agent_manager.update_draft_step(draft_id, 1, filled_template)
        
        return draft_id

    def list_drafts(self, user_id: str):
        return agent_manager.list_drafts(user_id)

    def update_draft(self, draft_id: str, updates: dict):
        # 업데이트 내용을 바탕으로 단계 추론 (현재는 간단한 로직)
        step = 1
        if "model_type" in updates:
            step = 2     
        return agent_manager.update_draft_step(draft_id, step, updates)

    async def publish_agent(self, draft_id: str, db):
        """
        최종 배포 (Publish)
        관리자(AgentManager)에게 배포 요청
        (벡터화 및 DB 저장은 Manager가 내부적으로 처리)
        """
        print(f"[App] Publishing agent draft: {draft_id}")
        
        # Manager에게 위임 (Vectorize + DB Save)
        return await agent_manager.publish_agent(draft_id, db)

    async def recommend_agents_for_chat(self, user_msg: str, conversation_history: list = None) -> list:
        """
        Agent 추천 (RAG 기반)
        (Logic: Hub에게 전적으로 위임 / Pass-through)
        """
        # Hub Layer에 추천 로직 위임 (Orchestration 포함)
        return await agent_manager.recommend_agents(user_msg, conversation_history)

# 싱글톤 내보내기
agent_service = AgentService()
