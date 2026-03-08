import sys
import os
import uuid
import time
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application.database import SessionLocal, User
from services.ai_hub.db.tables import Agent
from services.ai_hub.db.milvus_client import MilvusClient
from services.ai_drive.core.embedding import EmbeddingGenerator
from application.usecases.orchestrator.service import Orchestrator

from scripts.seed_essential_agents import ESSENTIAL_AGENTS

async def reseed_with_gpt():
    print("[ReSeed] 🚀 Starting GPT-5.2 Agent Generation...")
    
    db = SessionLocal()
    orchestrator = Orchestrator()
    
    milvus = None
    embedder = None
    try:
        milvus = MilvusClient()
        embedder = EmbeddingGenerator()
    except Exception as e:
        print(f"Failed to connect to Milvus: {e}")
        
    admin_email = "system_admin@ai-agent.com"
    admin = db.query(User).filter(User.email == admin_email).first()
    
    # Wipe old agents from DB
    db.query(Agent).delete()
    db.commit()
    print("[ReSeed] Wiped old Postgres agents")
    
    # Wipe Milvus collection
    if milvus:
        from pymilvus import utility
        if utility.has_collection("ai_hub_agents", using="ai_hub"):
            utility.drop_collection("ai_hub_agents", using="ai_hub")
            milvus._init_collection()
            print("[ReSeed] Wiped and recreated Milvus collection")
            
    for agent_data in ESSENTIAL_AGENTS:
        print(f"\n[ReSeed] Generating details for '{agent_data['name']}' using AI Engine...")
        user_message = (
            f"나는 '{agent_data['name']}'라는 에이전트를 만들고 싶어. "
            f"이 에이전트의 역할과 특징은 다음과 같아: {agent_data['description']}. "
            f"이전의 예전 프롬프트 구조보다 더 구체적으로 시스템 프롬프트 작성하고 입출력 예시도 더욱 풍부하게 포함해서 전문가다운 에이전트를 기획해줘."
        )
        messages = [
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Generate new data via pipeline
            draft_result = await orchestrator.analyze_for_draft(messages)
            
            # Use original hardcoded values if parsing failed
            name = draft_result.get("name") or agent_data["name"]
            description = draft_result.get("description") or agent_data["description"]
            system_prompt = draft_result.get("system_prompt") or agent_data["system_prompt"]
            input_example = draft_result.get("input_example") or agent_data["input_example"]
            output_example = draft_result.get("output_example") or agent_data["output_example"]
            
            category = agent_data["category"] 
            model_type = agent_data["model_type"]
            use_rag = agent_data["use_rag"]
            is_public = agent_data["is_public"]
            
            new_agent = Agent(
                id=uuid.uuid4(),
                creator_id=admin.id,
                name=name,
                category=category,
                model_type=model_type,
                description=description,
                system_prompt=system_prompt,
                input_example=input_example,
                output_example=output_example,
                use_rag=use_rag,
                is_public=is_public, 
                linked_knowledge_ids=[]
            )
            db.add(new_agent)
            
            # Embed and Save to Milvus
            if milvus and embedder:
                text_to_embed = f"{name} {description} {system_prompt}"
                embedding = embedder.create(text_to_embed)
                milvus_data = {
                    "id": str(new_agent.id),
                    "name": new_agent.name,
                    "description": new_agent.description,
                    "category": new_agent.category,
                    "system_prompt": new_agent.system_prompt,
                    "model_type": new_agent.model_type,
                    "input_example": new_agent.input_example,
                    "output_example": new_agent.output_example
                }
                milvus.insert_agent(milvus_data, embedding)
                
            db.commit()
            print(f"[ReSeed] Successfully saved '{name}'")
            # Sleep 1 second to avoid rate-limiting from LiteLLM / Upstage providers
            time.sleep(1)
            
        except Exception as e:
            print(f"[ERROR] Failed to generate {agent_data['name']}: {e}")
            db.rollback()

if __name__ == "__main__":
    asyncio.run(reseed_with_gpt())
