import json
import uuid
import redis
import os
from datetime import timedelta
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

from services.ai_hub.db.agent_repo import AgentRepository

# Redis Connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

class AgentManager:
    """
    Core Logic for Agent Lifecycle (Draft -> Publish)
    Delegates DB operations to AgentRepository.
    """
    
    def __init__(self):
        self.repo = AgentRepository()

    # --- 1. Draft Management (Redis) ---

    async def create_draft(self, user_id: str, intent: str, messages: List[Dict]) -> str:
        draft_id = str(uuid.uuid4())
        key = f"draft_agent:{draft_id}"
        
        draft_data = {
            "id": draft_id,
            "user_id": user_id,
            "status": "DRAFT",
            "name": f"Agent_{draft_id[:8]}", 
            "description": intent if intent else "Created via Chat",
            "messages": json.dumps(messages),
            "step": "1",
            "model_type": "GPT-4",
            "use_rag": "False",
            "visibility": "PRIVATE"
        }
        
        redis_client.hset(key, mapping=draft_data)
        redis_client.expire(key, timedelta(hours=24))
        
        user_list_key = f"user_drafts:{user_id}"
        redis_client.sadd(user_list_key, draft_id)
        
        return draft_id

    def list_drafts(self, user_id: str) -> List[Dict]:
        user_list_key = f"user_drafts:{user_id}"
        draft_ids = redis_client.smembers(user_list_key)
        
        results = []
        for draft_id in draft_ids:
            key = f"draft_agent:{draft_id}"
            data = redis_client.hgetall(key)
            if data:
                if "messages" in data:
                    try:
                        data["messages"] = json.loads(data["messages"])
                    except:
                        pass
                results.append(data)
            else:
                redis_client.srem(user_list_key, draft_id)
        return results

    def update_draft_step(self, draft_id: str, step: int, data: Dict) -> bool:
        key = f"draft_agent:{draft_id}"
        if not redis_client.exists(key):
            return False
        
        updates = {}
        for k, v in data.items():
            if isinstance(v, (list, dict, bool)):
                updates[k] = str(v)
            else:
                updates[k] = str(v)
        
        updates["step"] = str(step)
        redis_client.hset(key, mapping=updates)
        return True

    # --- 2. Publish (DB via Repository) ---

    def publish_agent(self, draft_id: str, db: Session) -> Optional[object]:
        key = f"draft_agent:{draft_id}"
        draft = redis_client.hgetall(key)
        
        if not draft:
            raise ValueError("Draft not found or expired")
            
        # Use Repository for DB Insert
        new_agent = self.repo.create_agent(db, draft)
        
        # Cleanup Redis
        redis_client.delete(key)
        redis_client.srem(f"user_drafts:{draft['user_id']}", draft_id)
        
        return new_agent
