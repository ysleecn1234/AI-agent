
import os
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from dotenv import load_dotenv

load_dotenv()

class MilvusClient:
    """
    AI Hub - Agent 전용 벡터 저장소 (Milvus)
    - 에이전트 정보(이름, 설명, 시스템 프롬프트)의 임베딩 저장 및 검색
    - AI Drive의 문서 저장소(db/milvus_client.py)와 구조적 대칭을 이룹니다.
    """
    
    def __init__(
        self,
        host: str = None,
        port: str = None,
        collection_name: str = "ai_hub_agents"
    ):
        self.host = host or os.getenv("MILVUS_HOST", "localhost")
        self.port = port or os.getenv("MILVUS_PORT", "19530")
        self.collection_name = collection_name
        self.collection = None
        
        self._connect()
        self._init_collection()
    
    def _connect(self):
        """Milvus 서버 연결"""
        # Alias를 분리하여 AI Drive와의 충돌 방지
        try:
            connections.connect(
                alias="ai_hub",
                host=self.host,
                port=self.port
            )
            print(f"[Hub:MilvusClient] Milvus 연결 성공: {self.host}:{self.port}")
        except Exception as e:
            print(f"[Hub:MilvusClient] Milvus 연결 실패: {e}")
            # 이미 연결된 경우 등 예외 처리

    def _init_collection(self):
        """컬렉션 초기화 (없으면 생성)"""
        if utility.has_collection(self.collection_name, using="ai_hub"):
            self.collection = Collection(self.collection_name, using="ai_hub")
            self.collection.load()
            print(f"[Hub:MilvusClient] 기존 컬렉션 로드: {self.collection_name}")
        else:
            self._create_collection()
            print(f"[Hub:MilvusClient] 새 컬렉션 생성: {self.collection_name}")
    
    def _create_collection(self):
        """
        에이전트 전용 스키마 정의
        - agent_id: UUID (String)
        - name: 에이전트 이름
        - description: 설명 (검색 대상)
        - category: 카테고리 (필터링용)
        - embedding: 1536차원 벡터 (OpenAI)
        """
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="agent_id", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
            FieldSchema(name="is_public", dtype=DataType.BOOL),
            FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=50),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="AI Hub 에이전트 벡터 저장소"
        )
        
        self.collection = Collection(
            name=self.collection_name,
            schema=schema,
            using="ai_hub"
        )
        
        # 인덱스 생성 (IVF_FLAT)
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        self.collection.load()
    
    def insert_agent(self, agent_data: Dict[str, Any], embedding: List[float]) -> bool:
        """
        에이전트 정보 및 벡터 저장
        """
        try:
            data = [
                [agent_data.get("id")],
                [agent_data.get("name", "Untitled")],
                [agent_data.get("description", "")],
                [agent_data.get("category", "Uncategorized")],
                [embedding],
                [agent_data.get("visibility", "PRIVATE") == "PUBLIC"],
                [agent_data.get("author", "Unknown")],
            ]
            
            self.collection.insert(data)
            self.collection.flush()
            print(f"[Hub:MilvusClient] Agent Saved: {agent_data.get('name')}")
            return True
            
        except Exception as e:
            print(f"[Hub:MilvusClient] Insert Failed: {e}")
            return False

    def search_agents(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """
        유사도 기반 에이전트 검색
        """
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        expr = None
        if category and category != "ALL":
            expr = f'category == "{category}"'
            
        # 공개된 에이전트만 검색 (기본 정책)
        # expr = f'{expr} and is_public == true' if expr else 'is_public == true'
        
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["agent_id", "name", "description", "category", "author"]
        )
        
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.entity.get("agent_id"),
                    "name": hit.entity.get("name"),
                    "description": hit.entity.get("description"),
                    "category": hit.entity.get("category"),
                    "author": hit.entity.get("author"),
                    "score": hit.score
                })
        
        return formatted_results

    def close(self):
        """연결 종료"""
        try:
            connections.disconnect("ai_hub")
            print("[Hub:MilvusClient] 연결 종료")
        except:
            pass
