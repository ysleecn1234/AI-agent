import json
import uuid
import redis
from sqlalchemy.orm import Session
from datetime import timedelta
import os

from app.models import Agent
from app.core.orchestrator import orchestrator

# Redis Connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

class AgentService:
    def __init__(self):
        pass

    # A. Draft Creation
    async def create_draft(self, user_id: str, messages: list):
        # 1. Analyze with Orchestrator
        draft_data = await orchestrator.analyze_for_draft(messages)
        
        # 2. Store in Redis
        draft_id = str(uuid.uuid4())
        key = f"draft_agent:{draft_id}"
        
        # Add metadata
        draft_data["id"] = draft_id
        draft_data["user_id"] = user_id
        draft_data["status"] = "DRAFT"
        draft_data["model_type"] = "AUTO" # Default
        draft_data["use_rag"] = "False"
        
        # Save Hash
        redis_client.hset(key, mapping=draft_data)
        redis_client.expire(key, timedelta(hours=1)) # 1 hour TTL
        
        # Add to User's Draft List (Set)
        user_list_key = f"user_drafts:{user_id}"
        redis_client.sadd(user_list_key, draft_id)
        
        return draft_id

    # B. List Drafts
    def list_drafts(self, user_id: str):
        user_list_key = f"user_drafts:{user_id}"
        draft_ids = redis_client.smembers(user_list_key)
        
        results = []
        for draft_id in draft_ids:
            key = f"draft_agent:{draft_id}"
            data = redis_client.hgetall(key)
            if data:
                results.append(data)
            else:
                # Cleanup expired
                redis_client.srem(user_list_key, draft_id)
        
        return results

    # C. Update Draft (Step 1 & 2)
    def update_draft(self, draft_id: str, updates: dict):
        key = f"draft_agent:{draft_id}"
        if not redis_client.exists(key):
            return False
            
        redis_client.hset(key, mapping=updates)
        return True

    # D. Publish Agent (Finalize)
    def publish_agent(self, draft_id: str, db: Session):
        key = f"draft_agent:{draft_id}"
        draft = redis_client.hgetall(key)
        
        if not draft:
            raise ValueError("Draft expired or not found")
            
        # 1. Create DB Record
        new_agent = Agent(
            creator_id=draft["user_id"],
            name=draft["name"],
            description=draft["description"],
            category=draft.get("category", "UNCATEGORIZED"),
            system_prompt=draft["system_prompt"],
            input_example=draft.get("input_example"),
            output_example=draft.get("output_example"),
            model_type=draft.get("model_type", "AUTO"),
            is_public=draft.get("visibility", "PRIVATE"),
            use_rag=(draft.get("use_rag") == "True")
        )
        
        # Handle JSON field manually if needed, or rely on SQLAlch
        if "linked_doc_ids" in draft:
             # Redis stores strings, need to parse if it was stored as JSON string
             pass 

        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        # 2. Cleanup Redis
        redis_client.delete(key)
        redis_client.srem(f"user_drafts:{draft['user_id']}", draft_id)
        
        return new_agent

agent_service = AgentService()
