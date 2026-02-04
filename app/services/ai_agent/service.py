from services.ai_hub.core.agent import AgentManager
from app.core.orchestrator import orchestrator

# Singleton Instance from Root Service
agent_manager = AgentManager()

class AgentService:
    """
    Wrapper Service for 'app' layer.
    Delegates actual logic to 'root/services/ai_agent/core.py'.
    """
    def __init__(self):
        pass

    async def create_draft(self, user_id: str, messages: list):
        # 1. Analyze with Orchestrator (Still in core/orchestrator.py for now, or move this too?)
        # For now, keep Orchestrator call here as it's part of the "App" flow customization.
        draft_data = await orchestrator.analyze_for_draft(messages)
        intent = draft_data.get("description", "")
        
        # 2. Delegate to Root Service
        return await agent_manager.create_draft(user_id, intent, messages)

    def list_drafts(self, user_id: str):
        return agent_manager.list_drafts(user_id)

    def update_draft(self, draft_id: str, updates: dict):
        # Infer step from updates (simple logic for now)
        # In reality, API should pass step explicitly.
        step = 1
        if "model_type" in updates:
            step = 2
            
        return agent_manager.update_draft_step(draft_id, step, updates)

    def publish_agent(self, draft_id: str, db):
        return agent_manager.publish_agent(draft_id, db)

# Export Singleton
agent_service = AgentService()
