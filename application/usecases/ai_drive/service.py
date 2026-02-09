"""
AI Drive Application Service (Facade Pattern)

이 레이어는 Facade 패턴을 따릅니다:
- 현재: Service Layer로 단순 위임
- 향후: 여러 서비스 조율 및 복잡한 워크플로우 관리 가능
"""

import os
import shutil
import tempfile
from typing import List, Dict, Any
from fastapi import UploadFile

# Service Layer
from services.ai_drive.pipeline import DocumentPipeline
from services.ai_drive.db.postgres_client import PostgresClient

class AIDriveService:
    """
    Drive Application Service (Facade)
    
    역할:
    - Service Layer 메서드 조율
    - 간단한 전처리 (파일 저장 등)
    - 에러 핸들링 통합
    
    확장 가능성:
    - 여러 서비스 조합 (Pipeline + RAGSearcher)
    - 트랜잭션 관리
    - 비즈니스 규칙 검증
    """
    
    def __init__(self):
        self.pipeline = DocumentPipeline()
        self.db_client = PostgresClient()
        self._rag_searcher = None
        self._doc_chat = None

    # ==================== 기존 메서드 ====================
    
    def get_user_storage_usage(self, user_id: str) -> Dict:
        """저장소 사용량 통계"""
        # TODO: PostgresClient에서 실제 집계 로직 구현 필요
        return {"used_mb": 150, "limit_mb": 1000, "file_count": 24}

    def fetch_available_knowledge(self, user_id: str) -> List[Dict]:
        """RAG에 사용할 수 있는 문서 목록"""
        docs = self.db_client.list_documents(
            status="active",
            visibility="team"
        )
        
        return [
            {
                "id": doc["doc_id"],
                "title": doc["title"],
                "type": (doc.get("file_type") or "DOC").upper(),
                "created_at": doc.get("created_at")
            }
            for doc in docs
        ]

    # ==================== 새로운 Facade 메서드 ====================
    
    async def upload_document(
        self, 
        file: UploadFile, 
        creator_id: str,
        creator_department: str,
        title: str = None,
        description: str = "",
        visibility: str = "team",
        tags: list = None
    ) -> Dict[str, Any]:
        """
        파일 업로드 (Facade)
        
        현재: Pipeline으로 단순 위임
        향후: PII 검증, 권한 체크 등 추가 가능
        """
        # 임시 파일 저장
        temp_path = await self._save_temp_file(file)
        
        try:
            # Service Layer 호출
            result = self.pipeline.process_file_upload(
                file_path=temp_path,
                creator_id=creator_id,
                creator_department=creator_department,
                title=title or file.filename,
                description=description,
                visibility=visibility,
                tags=tags or []
            )
            return result
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    async def save_chat(self, request) -> Dict[str, Any]:
        """
        채팅 저장 (Facade)
        
        현재: Pipeline으로 단순 위임
        향후: 제목 자동 생성, PII 체크 등 추가 가능
        """
        return self.pipeline.process_chat_save(
            chat_content=request.content,
            creator_id=request.creator_id,
            creator_department=request.creator_department,
            title=request.title or "채팅 대화",
            description=request.description or "",
            visibility=request.visibility
        )
    
    async def save_agent_result(self, request) -> Dict[str, Any]:
        """
        에이전트 결과 저장 (Facade)
        
        현재: Pipeline으로 단순 위임
        향후: 에이전트 메타데이터 추가 등 가능
        """
        return self.pipeline.process_agent_save(
            agent_content=request.content,
            creator_id=request.creator_id,
            creator_department=request.creator_department,
            agent_name=request.agent_name,
            title=request.title or f"{request.agent_name} 결과",
            description=request.description or "",
            visibility=request.visibility
        )
    
    async def search_documents(self, request) -> list:
        """
        RAG 검색 (Facade)
        
        현재: RAGSearcher로 단순 위임
        향후: 검색 결과 후처리, 권한 필터링 강화 등 가능
        """
        # Lazy initialization
        if not self._rag_searcher:
            from services.ai_drive.core.rag_search import RAGSearcher
            self._rag_searcher = RAGSearcher()
        
        return self._rag_searcher.search(
            query=request.query,
            user_department=request.user_department,
            top_k=request.top_k
        )
    
    async def list_documents(
        self,
        department: str = None,
        visibility: str = None,
        status: str = "active",
        limit: int = 50
    ) -> list:
        """
        문서 목록 조회 (Facade)
        
        현재: PostgresClient로 단순 위임
        향후: 권한 필터링, 정렬 등 추가 가능
        """
        return self.db_client.list_documents(
            department=department,
            visibility=visibility,
            status=status,
            limit=limit
        )
    
    async def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        문서 상세 조회 (Facade)
        
        현재: PostgresClient로 단순 위임
        향후: 접근 권한 체크 등 추가 가능
        """
        return self.db_client.get_document(doc_id)
    
    async def delete_document(self, doc_id: str, user_id: str) -> bool:
        """
        문서 삭제 (Facade)
        
        현재: PostgresClient + MilvusClient 호출
        향후: 권한 체크, 로그 기록 등 추가 가능
        """
        # DB에서 상태 변경 (archived)
        self.db_client.update_document_status(doc_id, "archived")
        
        # Milvus에서 벡터 삭제
        from services.ai_drive.db.milvus_client import MilvusClient
        milvus_client = MilvusClient()
        milvus_client.delete_by_document(doc_id)
        
        # 활동 로그
        self.db_client.log_activity(
            user_id=user_id,
            action="delete_document",
            details={"doc_id": doc_id}
        )
        
        return True
    
    async def chat_with_document(self, doc_id: str, request) -> Dict[str, Any]:
        """
        문서 채팅 (Facade)
        
        현재: DocumentChat으로 단순 위임
        향후: 문서 권한 체크, 사용량 제한 등 추가 가능
        """
        # Lazy initialization
        if not self._doc_chat:
            from services.ai_drive.core.doc_chat import DocumentChat
            self._doc_chat = DocumentChat()
        
        return self._doc_chat.chat(
            doc_id=doc_id,
            question=request.question,
            user_id=request.user_id
        )
    
    # ==================== 헬퍼 메서드 ====================
    
    async def _save_temp_file(self, file: UploadFile) -> str:
        """임시 파일 저장"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            content = await file.read()
            tmp.write(content)
            return tmp.name

# Singleton
drive_service = AIDriveService()
