"""
AI 드라이브 - Milvus 벡터 DB 클라이언트
벡터 저장 및 검색
"""

import os
from typing import List, Dict, Any
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from dotenv import load_dotenv

load_dotenv()


class MilvusClient:
    """
    Milvus 벡터 DB 클라이언트
    - 컬렉션 생성/관리
    - 벡터 저장/검색
    """
    
    def __init__(
        self,
        host: str = None,
        port: str = None,
        collection_name: str = "ai_drive_documents"
    ):
        self.host = host or os.getenv("MILVUS_HOST", "localhost")
        self.port = port or os.getenv("MILVUS_PORT", "19530")
        self.collection_name = collection_name
        self.collection = None
        
        self._connect()
        self._init_collection()
    
    def _connect(self):
        """Milvus 서버 연결"""
        connections.connect(
            alias="default",
            host=self.host,
            port=self.port
        )
        print(f"✓ Milvus 연결 성공: {self.host}:{self.port}")
    
    def _init_collection(self):
        """컬렉션 초기화 (없으면 생성)"""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self.collection.load()
            print(f"✓ 기존 컬렉션 로드: {self.collection_name}")
        else:
            self._create_collection()
            print(f"✓ 새 컬렉션 생성: {self.collection_name}")
    
    def _create_collection(self):
        """컬렉션 생성 (기획서 스키마 반영)"""
        fields = [
            # 기본 필드
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
            
            # 권한/필터링 필드
            FieldSchema(name="visibility", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="creator_department", dtype=DataType.VARCHAR, max_length=100),
            
            # 버전 관리 필드
            FieldSchema(name="version", dtype=DataType.INT64),
            FieldSchema(name="is_latest", dtype=DataType.BOOL),
            FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=20),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="AI 드라이브 문서 벡터 저장소"
        )
        
        self.collection = Collection(
            name=self.collection_name,
            schema=schema
        )
        
        # 인덱스 생성 (기획서: COSINE, IVF_FLAT, nlist=1024)
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        self.collection.load()
    
    def insert(
        self,
        doc_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        visibility: str = "team",
        creator_department: str = "",
        version: int = 1,
        is_latest: bool = True,
        status: str = "active"
    ) -> List[int]:
        """
        문서 청크 및 벡터 저장
        
        Args:
            doc_id: 문서 ID (PostgreSQL과 연결)
            chunks: 텍스트 청크 리스트
            embeddings: 임베딩 벡터 리스트
            visibility: 공개범위 (team/company)
            creator_department: 작성자 부서
            version: 문서 버전
            is_latest: 최신 버전 여부
            status: 문서 상태 (active/archived)
            
        Returns:
            삽입된 ID 리스트
        """
        if len(chunks) != len(embeddings):
            raise ValueError("청크와 임베딩 개수가 일치하지 않습니다.")
        
        data = [
            [doc_id] * len(chunks),
            chunks,
            embeddings,
            [visibility] * len(chunks),
            [creator_department] * len(chunks),
            [version] * len(chunks),
            [is_latest] * len(chunks),
            [status] * len(chunks),
        ]
        
        result = self.collection.insert(data)
        self.collection.flush()
        
        print(f"✓ {len(chunks)}개 청크 저장 완료 (doc_id: {doc_id})")
        
        return result.primary_keys
    
    def search(
        self,
        query_embedding: List[float],
        department: str = "",
        top_k: int = 10,
        include_company: bool = True
    ) -> List[Dict[str, Any]]:
        """
        유사도 검색 (권한 필터 반영)
        
        검색 조건:
        - status = 'active'
        - is_latest = true
        - visibility = 'company' OR (visibility = 'team' AND creator_department = 부서)
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            department: 사용자 부서 (권한 필터용)
            top_k: 반환할 결과 수
            include_company: 전사 공개 문서 포함 여부
            
        Returns:
            검색 결과 리스트
        """
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        # 권한 필터 (기획서 기준)
        if include_company and department:
            expr = f'status == "active" and is_latest == true and (visibility == "company" or (visibility == "team" and creator_department == "{department}"))'
        elif department:
            expr = f'status == "active" and is_latest == true and visibility == "team" and creator_department == "{department}"'
        else:
            expr = f'status == "active" and is_latest == true and visibility == "company"'
        
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["doc_id", "chunk_text", "visibility", "creator_department", "version"]
        )
        
        search_results = []
        for hits in results:
            for hit in hits:
                search_results.append({
                    "id": hit.id,
                    "doc_id": hit.entity.get("doc_id"),
                    "chunk_text": hit.entity.get("chunk_text"),
                    "visibility": hit.entity.get("visibility"),
                    "creator_department": hit.entity.get("creator_department"),
                    "version": hit.entity.get("version"),
                    "score": hit.score
                })
        
        return search_results
    
    def delete_by_doc_id(self, doc_id: str) -> int:
        """문서 ID로 삭제"""
        expr = f'doc_id == "{doc_id}"'
        result = self.collection.delete(expr)
        self.collection.flush()
        
        print(f"✓ doc_id={doc_id} 삭제 완료")
        
        return result.delete_count

    def update_metadata(self, doc_id: str, visibility: str = None, creator_department: str = None):
        """
        메타데이터 업데이트 (Visibility, Department 등)
        Milvus는 Update를 직접 지원하지 않으므로, 기존 데이터를 조회 -> 삭제 -> 재삽입 과정을 거쳐야 함.
        """
        print(f"[Milvus] Updating metadata for doc_id={doc_id}...")
        
        # 1. 기존 데이터 조회
        expr = f'doc_id == "{doc_id}"'
        res = self.collection.query(
            expr=expr,
            output_fields=["doc_id", "chunk_text", "embedding", "visibility", "creator_department", "version", "is_latest", "status"]
        )
        
        if not res:
            print(f"[Milvus] 문서 없음 (Skip Update): {doc_id}")
            return
            
        print(f"  → Found {len(res)} chunks to update.")
        
        # 2. 데이터 수정
        new_data_list = []
        for hit in res:
            # 변경할 필드만 업데이트
            if visibility:
                hit["visibility"] = visibility
            if creator_department:
                hit["creator_department"] = creator_department
            new_data_list.append(hit)
            
        # 3. 기존 데이터 삭제
        self.collection.delete(expr)
        
        # 4. 수정된 데이터 재삽입
        # 컬럼 순서: doc_id, chunk_text, embedding, visibility, creator_department, version, is_latest, status
        insert_data = [
            [x["doc_id"] for x in new_data_list],
            [x["chunk_text"] for x in new_data_list],
            [x["embedding"] for x in new_data_list],
            [x["visibility"] for x in new_data_list],
            [x["creator_department"] for x in new_data_list],
            [x["version"] for x in new_data_list],
            [x["is_latest"] for x in new_data_list],
            [x["status"] for x in new_data_list],
        ]
        
        self.collection.insert(insert_data)
        self.collection.flush()
        print(f"✓ Milvus Metadata Updated: {doc_id} (Visibility: {visibility})")

    
    def update_version_status(self, doc_id: str, old_version: int):
        """
        이전 버전 is_latest를 False로 변경
        (Milvus는 update 미지원 → 조회 후 삭제 → 재삽입)
        """
        # 이전 버전 청크들 조회
        expr = f'doc_id == "{doc_id}" and version == {old_version}'
    
        old_chunks = self.collection.query(
            expr=expr,
            output_fields=["doc_id", "chunk_text", "embedding", "visibility", 
                        "creator_department", "version", "is_latest", "status"]
        )
    
        if not old_chunks:
            print(f"  → 이전 버전 없음 (doc_id={doc_id}, version={old_version})")
            return
    
        # 삭제
        self.collection.delete(expr)
    
        # is_latest=False로 재삽입
        data = [
            [chunk["doc_id"] for chunk in old_chunks],
            [chunk["chunk_text"] for chunk in old_chunks],
            [chunk["embedding"] for chunk in old_chunks],
            [chunk["visibility"] for chunk in old_chunks],
            [chunk["creator_department"] for chunk in old_chunks],
            [chunk["version"] for chunk in old_chunks],
            [False] * len(old_chunks),  # is_latest = False
            [chunk["status"] for chunk in old_chunks],
        ]
    
        self.collection.insert(data)
        self.collection.flush()
    
        print(f"  → 이전 버전 is_latest=False 처리 완료 ({len(old_chunks)}개 청크)")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 조회"""
        self.collection.flush()
        
        return {
            "name": self.collection_name,
            "num_entities": self.collection.num_entities,
            "schema": str(self.collection.schema)
        }
    
    def search_by_doc_id(
        self,
        doc_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        특정 문서 내에서만 유사도 검색
        (문서별 채팅용)
        """
        # 해당 doc_id만 필터링
        filter_expr = f'doc_id == "{doc_id}"'
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["doc_id", "chunk_text", "visibility", "creator_department", "version"]
        )
        
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.id,
                    "doc_id": hit.entity.get("doc_id"),
                    "chunk_text": hit.entity.get("chunk_text"),
                    "visibility": hit.entity.get("visibility"),
                    "creator_department": hit.entity.get("creator_department"),
                    "version": hit.entity.get("version"),
                    "score": hit.score
                })
        
        print(f"  → doc_id={doc_id}에서 {len(formatted_results)}개 검색")
        
        return formatted_results


    def get_chunks_by_doc_id(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        특정 문서의 모든 청크 가져오기
        (Fallback용)
        """
        filter_expr = f'doc_id == "{doc_id}"'
        
        results = self.collection.query(
            expr=filter_expr,
            output_fields=["doc_id", "chunk_text", "visibility", "creator_department", "version"],
            limit=100
        )
        
        print(f"  → doc_id={doc_id}에서 {len(results)}개 청크 조회")
        
        return results

    def close(self):
        """연결 종료"""
        connections.disconnect("default")
        print("✓ Milvus 연결 종료")


# 테스트 코드
if __name__ == "__main__":
    print("=" * 80)
    print("MilvusClient 테스트")
    print("=" * 80)
    
    try:
        client = MilvusClient()
        
        stats = client.get_collection_stats()
        print(f"\n[컬렉션 통계]")
        print(f"이름: {stats['name']}")
        print(f"문서 수: {stats['num_entities']}")
        
        # 테스트 데이터 삽입
        print(f"\n[삽입 테스트]")
        test_chunks = ["테스트 청크 1입니다.", "테스트 청크 2입니다."]
        test_embeddings = [[0.1] * 1536, [0.2] * 1536]
        
        ids = client.insert(
            doc_id="test_doc_001",
            chunks=test_chunks,
            embeddings=test_embeddings,
            visibility="team",
            creator_department="개발팀",
            version=1,
            is_latest=True,
            status="active"
        )
        print(f"삽입된 ID: {ids}")
        
        # 검색 테스트
        print(f"\n[검색 테스트]")
        query_embedding = [0.1] * 1536
        results = client.search(
            query_embedding=query_embedding,
            department="개발팀",
            top_k=5
        )
        
        for r in results:
            print(f"  - {r['chunk_text'][:30]}... (score: {r['score']:.4f})")
        
        # 삭제 테스트
        print(f"\n[삭제 테스트]")
        client.delete_by_doc_id("test_doc_001")
        
        client.close()
        
        print("\n" + "=" * 80)
        print("✓ 테스트 성공!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")