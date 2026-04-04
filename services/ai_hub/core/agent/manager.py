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
from services.common.cost_logger import get_cost_logger
from services.orchestrator.cost_calculator import get_cost_calculator

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
        except ImportError:
            self.use_rag = False

        # [Logging] Hub Repository 초기화
        self.hub_repo = HubRepository()
        self.cost_logger = get_cost_logger()
        self.cost_calculator = get_cost_calculator()

    # --- 1. Recommendation (Hub-Centric Pattern) ---

    async def recommend_agents(self, user_msg: str, conversation_history: list = None, department: str = None) -> List[Dict]:
        """
        사용자 질문을 분석하여 그에 맞는 에이전트를 추천합니다.
        (Hub가 Orchestration 및 Search 로직을 직접 수행)
        1. Orchestrator에게 의도 분석 요청
        2. Vector Search (의미 기반) + DB Search (키워드 기반) 결합
        3. 사용자 부서 기반 가중치 반영
        """
        # 1. Orchestrator 호출
        from application.usecases.orchestrator.service import orchestrator
        analysis = await orchestrator.recommend_agents(user_msg, conversation_history)
        
        # 2. 검색 수행 (DB 세션은 상위에서 주입받아야 함 - 현재는 None으로 호출될 수 있음)
        db = SessionLocal()
        try:
            results = self.search_agents_by_analysis(analysis, db=db)
            
            # 3. 부서 기반 가중치: 동점 시 부서 관련 에이전트 우선 (tiebreaker)
            if department and results:
                import re
                dept_boost = float(os.getenv("DEPT_BOOST_WEIGHT", "0.05"))
                dept_keyword = re.sub(r'(팀|부|실|센터|본부|파트)$', '', department).lower()
                if dept_keyword:
                    for item in results:
                        cat = (item.get("category") or "").lower()
                        if dept_keyword in cat:
                            # 의도 점수를 뒤집지 않을 정도의 미세 가중치
                            item["match_score"] = item.get("match_score", 0) + dept_boost
                    # 부스트 반영 후 재정렬
                    results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            return results
        finally:
            db.close()

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

                # [Log] Cost (Embedding - API 실제 토큰)
                try:
                    actual_tokens = self.embedding_generator.last_usage.total_tokens if self.embedding_generator.last_usage else 0
                    embed_cost = self.cost_calculator.calculate_cost("text-embedding-3-small", actual_tokens, 0)

                    self.cost_logger.log_embedding_cost(
                        user_id="00000000-0000-0000-0000-000000000000",
                        tokens=actual_tokens,
                        cost_usd=embed_cost["cost_usd"]["total"],
                        cost_krw=embed_cost["cost_krw"]["total"],
                        operation="hub_search",
                    )
                except Exception as e:
                    pass

            except Exception as e:
                pass
        
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
                    results.append(_agent_to_recommendation_item(agent, match_score))
                
                # 점수순 정렬
                results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

            except Exception as e:
                pass

        # 3. Fallback: 벡터 결과 없을 때 DB 키워드/전체에서 추천
        if not results and db:
            try:
                from services.ai_hub.db.hub_repo import HubRepository
                hub_repo = HubRepository()
                fallback_agents = []
                search_term = (keywords[0] if keywords else None) or topic or "일반"
                if search_term and search_term != "General":
                    fallback_agents = hub_repo.get_agents_by_keyword(db, search_term)
                if not fallback_agents:
                    fallback_agents = hub_repo.get_all_public_agents(db)
                for agent in fallback_agents[:5]:
                    results.append(_agent_to_recommendation_item(agent, 0))
            except Exception as e:
                pass

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

        # 1. Save to RDB (Postgres) FIRST to get the ID
        new_agent = self.repo.create_agent(db, draft)
            
        # 2. Vectorize & Save to Milvus (Agent Dedicated Store)
        if self.use_rag:
            try:
                # [Fix] Postgres에서 생성된 ID를 draft에 주입하여 Milvus와 동기화
                draft['id'] = str(new_agent.id)
                
                # 임베딩 생성 (Description + System Prompt)
                text_to_embed = f"{draft.get('name', '')} {draft.get('description', '')} {draft.get('system_prompt', '')}"
                embedding = self.embedding_generator.create(text_to_embed)
                
                # Agent Vector Store 저장
                self.milvus_client.insert_agent(draft, embedding)

                # [Log] Cost & Activity (Publishing)
                try:
                    # 1. Cost (Embedding - API 실제 토큰)
                    actual_tokens = self.embedding_generator.last_usage.total_tokens if self.embedding_generator.last_usage else 0
                    embed_cost = self.cost_calculator.calculate_cost("text-embedding-3-small", actual_tokens, 0)

                    self.cost_logger.log_embedding_cost(
                        user_id=draft['user_id'],
                        tokens=actual_tokens,
                        cost_usd=embed_cost["cost_usd"]["total"],
                        cost_krw=embed_cost["cost_krw"]["total"],
                        operation="agent_publish_embedding",
                    )

                except Exception as e:
                    pass

            except Exception as e:
                pass
        
        # Cleanup Redis
        redis_client.delete(key)
        redis_client.srem(f"user_drafts:{draft['user_id']}", draft_id)
        
        return new_agent


def _agent_to_recommendation_item(agent, match_score: float = 0) -> Dict:
    """DB Agent → 프론트 Agent 형식 추천 항목"""
    return {
        "id": str(agent.id),
        "name": agent.name,
        "description": agent.description,
        "category": getattr(agent, "category", "기타"),
        "visibility": getattr(agent, "is_public", "PRIVATE"),
        "creator": str(agent.creator_id) if agent.creator_id else "Unknown",
        "creator_id": str(agent.creator_id) if agent.creator_id else None,
        "created_at": getattr(agent, "created_at", None)
        and getattr(agent.created_at, "isoformat", lambda: "")() or "",
        "is_active": True,
        "match_score": match_score,
    }
