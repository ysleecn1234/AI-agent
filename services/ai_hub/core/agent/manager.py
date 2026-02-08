import json
import uuid
import redis
import os
from datetime import timedelta
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

from services.ai_hub.db.agent_repo import AgentRepository
from services.ai_hub.db.hub_repo import HubRepository
from application.database import SessionLocal  # Hub DB 세션

# Redis Connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

class AgentManager:
    """
    에이전트 수명 주기 관리의 핵심 로직 (Draft -> Publish)
    DB 작업은 AgentRepository에 위임합니다.
    """
    
    
    def __init__(self):
        self.repo = AgentRepository()
        
        # [AI Drive] 임베딩 및 벡터 검색 통합
        try:
            from services.ai_hub.db.milvus_client import MilvusClient
            from services.ai_drive.core.embedding import EmbeddingGenerator
            self.milvus_client = MilvusClient()
            self.embedding_generator = EmbeddingGenerator()
            self.use_rag = True
            print("[Hub] AI Drive 연동 성공: Vector Search 활성화 (Agent 전용)")
        except ImportError:
            self.use_rag = False
            print("[Hub] AI Drive 모듈 없음: Mock Search 모드")

        # [Logging] Hub Repository 초기화
        self.hub_repo = HubRepository()

    # --- 1. Recommendation (Hub-Centric Pattern) ---

    async def recommend_agents(self, user_msg: str, conversation_history: list = None) -> List[Dict]:
        """
        사용자 질문을 분석하여 그에 맞는 에이전트를 추천합니다.
        (Hub가 Orchestration 및 Search 로직을 직접 수행)
        1. Orchestrator에게 의도 분석 요청
        2. Vector Search (의미 기반) + DB Search (키워드 기반) 결합
        """
        # 1. Orchestrator 호출
        from application.usecases.orchestrator.service import orchestrator
        
        print(f"[Hub] Analyzing intent for recommendation: {user_msg[:20]}...")
        analysis = await orchestrator.recommend_agents(user_msg, conversation_history)
        
        # 2. 검색 수행 (DB 세션은 상위에서 주입받아야 함 - 현재는 None으로 호출될 수 있음)
        # TODO: Service Layer에서 DB 세션을 넘겨주도록 개선 필요
        return self.search_agents_by_analysis(analysis)

    def search_agents_by_analysis(self, analysis: Dict, db: Session = None) -> List[Dict]:
        """
        분석된 데이터(키워드, 토픽)를 기반으로 에이전트를 검색합니다.
        (목적: 사용자에게 적합한 에이전트 추천)
        
        [검색 전략]
        1. Vector Search (Milvus): 의미 기반 유사도 검색으로 후보군(ID) 추출
        2. Metadata Fetch (Postgres): 추출된 ID로 Agent 상세 정보 조회
        """
        topic = analysis.get("topic", "General")
        keywords = analysis.get("keywords", [])
        category = analysis.get("category", "ALL")
        
        results = []
        candidate_map = {}  # {id: score}
        
        # 1. Vector Search (AI Drive) - 의미 기반 추천
        if self.use_rag:
            try:
                # 검색어 생성 (Topic + Keywords)
                search_query = f"{topic} {' '.join(keywords)}"
                query_vector = self.embedding_generator.create(search_query)
                
                # Milvus 검색 (Agent 전용 Collection)
                search_results = self.milvus_client.search_agents(
                    query_embedding=query_vector, 
                    top_k=5, 
                    category=category
                )
                
                # 결과에서 ID 및 Score 추출
                for res in search_results:
                    res_id = res.get('id') or res.get('agent_id')
                    score = res.get('score', 0)
                    if res_id:
                        candidate_map[str(res_id)] = score
                
                print(f"[Hub] Vector Search executed for: '{search_query}' -> IDs: {list(candidate_map.keys())}")
                
                # [Log] Cost (Embedding)
                try:
                    db = SessionLocal()
                    tokens = len(search_query) * 2
                    cost_usd = tokens * 0.00000002
                    cost_krw = cost_usd * 1400
                    
                    self.hub_repo.log_cost(
                        db=db,
                        user_id="00000000-0000-0000-0000-000000000000",
                        operation="hub_search",
                        tokens_used=tokens,
                        cost_usd=cost_usd,
                        cost_krw=cost_krw,
                        model_name="text-embedding-3-small"
                    )
                    db.close()
                except Exception as e:
                    print(f"[Hub] Failed to log searching cost: {e}")
                
            except Exception as e:
                print(f"[Hub] Vector Search Failed: {e}")
        
        # 2. Metadata Fetch (DB) - 상세 정보 보완 (Batch Query)
        if db and candidate_map:
            try:
                from services.ai_hub.db.hub_repo import HubRepository
                hub_repo = HubRepository()
                
                # Batch 조회 (IN Query)
                db_agents = hub_repo.get_agents_by_ids(db, list(candidate_map.keys()))
                
                for agent in db_agents:
                    agent_id_str = str(agent.id)
                    match_score = candidate_map.get(agent_id_str, 0)
                    
                    results.append({
                        "id": agent_id_str,
                        "name": agent.name,
                        "description": agent.description,
                        "author": "Unknown", # DB 스키마 확인 필요
                        "is_official": agent.is_public,
                        "match_score": match_score
                    })
                
                # 점수순 정렬
                results.sort(key=lambda x: x["match_score"], reverse=True)
                
            except Exception as e:
                print(f"[Hub] DB Fetch Failed: {e}")
                import traceback
                traceback.print_exc()

        return results

    # --- 1. Definition Management ---

    def get_standard_template(self) -> Dict:
        """
        새로운 에이전트를 위한 표준 JSON 스키마/템플릿을 반환합니다.
        (Delegated to schema.py)
        """
        from .schema import get_standard_template
        return get_standard_template()

    # --- 2. Draft Management (Redis) ---

    async def create_draft(self, user_id: str, intent: str, messages: List[Dict]) -> str:
        from .utils import generate_agent_id
        
        draft_id = generate_agent_id()
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
        
        # [Log] Activity
        try:
            db = SessionLocal()
            self.hub_repo.log_activity(
                db=db,
                user_id=user_id,
                action="create_draft",
                details={"intent": intent, "draft_id": draft_id},
                success=True
            )
            db.close()
        except Exception as e:
            print(f"[Hub] Failed to log activity: {e}")
        
        return draft_id

    def get_draft(self, draft_id: str) -> Optional[Dict]:
        """
        ID로 단일 초안(Draft)을 조회합니다.
        """
        from .utils import safe_json_loads
        
        key = f"draft_agent:{draft_id}"
        data = redis_client.hgetall(key)
        if not data:
            return None
            
        if "messages" in data:
            data["messages"] = safe_json_loads(data["messages"])
        return data

    def list_drafts(self, user_id: str) -> List[Dict]:
        from .utils import safe_json_loads
        
        user_list_key = f"user_drafts:{user_id}"
        draft_ids = redis_client.smembers(user_list_key)
        
        results = []
        for draft_id in draft_ids:
            key = f"draft_agent:{draft_id}"
            data = redis_client.hgetall(key)
            if data:
                if "messages" in data:
                    data["messages"] = safe_json_loads(data["messages"])
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

    async def publish_agent(self, draft_id: str, db: Session) -> Optional[object]:
        """
        에이전트 배포 (Publish)
        1. Redis Draft 조회
        2. Vector DB (Milvus) 저장 (AgentVectorStore 사용)
        3. RDB (Postgres) 저장
        """
        key = f"draft_agent:{draft_id}"
        draft = redis_client.hgetall(key)
        
        if not draft:
            raise ValueError("Draft not found or expired")
            
        # 1. Vectorize & Save to Milvus (Agent Dedicated Store)
        if self.use_rag:
            try:
                # 임베딩 생성 (Description + System Prompt)
                text_to_embed = f"{draft.get('name', '')} {draft.get('description', '')} {draft.get('system_prompt', '')}"
                embedding = self.embedding_generator.create(text_to_embed)
                
                # Agent Vector Store 저장
                self.milvus_client.insert_agent(draft, embedding)
                print(f"[Hub] Agent Vectorized & Saved to Milvus: {draft.get('name')}")
                
                # [Log] Cost & Activity (Publishing)
                try:
                    db = SessionLocal()
                    
                    # 1. Cost (Embedding)
                    tokens = len(text_to_embed) * 2
                    cost_usd = tokens * 0.00000002
                    cost_krw = cost_usd * 1400
                    
                    self.hub_repo.log_cost(
                        db=db,
                        user_id=draft['user_id'],
                        operation="agent_publish_embedding",
                        tokens_used=tokens,
                        cost_usd=cost_usd,
                        cost_krw=cost_krw,
                        model_name="text-embedding-3-small"
                    )
                    
                    # 2. Activity
                    self.hub_repo.log_activity(
                        db=db,
                        user_id=draft['user_id'],
                        action="publish_agent",
                        details={"agent_name": draft.get('name'), "draft_id": draft_id},
                        success=True
                    )
                    
                    db.close()
                except Exception as e:
                    print(f"[Hub] Failed to log publishing: {e}")
                        
                        
            except Exception as e:
                print(f"[Hub] Vectorization Failed: {e}")
                # 실패해도 DB 저장은 진행할지 여부 결정 (현재는 진행)

        # 2. Save to RDB (Postgres)
        new_agent = self.repo.create_agent(db, draft)
        
        # Cleanup Redis
        redis_client.delete(key)
        redis_client.srem(f"user_drafts:{draft['user_id']}", draft_id)
        
        return new_agent
