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
import json

# Service Layer
import time
from services.ai_drive.pipeline import DocumentPipeline
from services.ai_drive.db.postgres_client import PostgresClient
from services.common.activity_logger import get_activity_logger

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
        # 오케스트레이터 연동 (중앙 LLM 관제)
        from application.usecases.orchestrator.service import orchestrator
        self._orchestrator = orchestrator
        
        self.pipeline = DocumentPipeline(orchestrator=self._orchestrator)
        self.db_client = PostgresClient()
        self.activity_logger = get_activity_logger()
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
            start = time.time()
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
            
            # 활동 로그 (성공)
            duration_ms = int((time.time() - start) * 1000)
            self.activity_logger.log(
                user_id=creator_id,
                action="upload",
                details={
                    "file_type": file.content_type,
                    "file_size": file.size,
                    "title": title or file.filename,
                },
                success=True,
                duration_ms=duration_ms,
            )
            
            return result
        except Exception as e:
            # 활동 로그 (실패)
            self.activity_logger.log(
                user_id=creator_id,
                action="upload",
                details={
                    "title": title or file.filename,
                    "error": str(e),
                },
                success=False,
            )
            raise
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    async def save_chat(self, request) -> Dict[str, Any]:
        """
        채팅 저장 (Facade)
        
        현재: Pipeline으로 단순 위임
        향후: 제목 자동 생성, PII 체크 등 추가 가능
        """
        title = request.title
        description = request.description or ""
        
        # 제목이 없으면 자동 생성 (Orchestrator 사용)
        if not title:
            try:
                # Orchestrator에게 제목/설명 생성 요청
                llm_result = self._orchestrator.call_llm(
                    task="title_gen",
                    prompt=f"다음 대화 내용을 바탕으로 적절한 제목과 설명을 생성하세요:\n\n{request.content[:1000]}"
                )
                
                # JSON 파싱
                response_text = llm_result["content"]
                if "```" in response_text:
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                
                data = json.loads(response_text.strip())
                title = data.get("title", "채팅 대화")
                
                # 설명이 비어있으면 자동 생성된 설명 사용
                if not description:
                    description = data.get("description", "")
                    
                print(f"[App] 제목 자동 생성 완료: {title}")
                    
            except Exception as e:
                print(f"[App] 제목 생성 실패: {e}")
                title = "채팅 대화"
        
        start = time.time()
        result = self.pipeline.process_chat_save(
            chat_content=request.content,
            creator_id=request.creator_id,
            creator_department=request.creator_department,
            title=title,
            description=description,
            visibility=request.visibility
        )

        duration_ms = int((time.time() - start) * 1000)
        self.activity_logger.log(
            user_id=request.creator_id,
            action="chat_save",
            details={"title": title},
            success=True,
            duration_ms=duration_ms,
        )

        return result
    
    async def save_agent_result(self, request) -> Dict[str, Any]:
        """
        에이전트 결과 저장 (Facade)
        
        현재: Pipeline으로 단순 위임
        향후: 에이전트 메타데이터 추가 등 가능
        """
        start = time.time()
        result = self.pipeline.process_agent_save(
            agent_output=request.content,
            creator_id=request.creator_id,
            creator_department=request.creator_department,
            agent_name=request.agent_name,
            title=request.title or f"{request.agent_name} 결과",
            description=request.description or "",
            visibility=request.visibility
        )

        duration_ms = int((time.time() - start) * 1000)
        self.activity_logger.log(
            user_id=request.creator_id,
            action="agent_save",
            details={"agent_name": request.agent_name},
            success=True,
            duration_ms=duration_ms,
        )

        return result
    
    async def search_documents(self, request) -> list:
        """
        RAG 검색 (Facade)
        """
        # Lazy initialization
        if not self._rag_searcher:
            from services.ai_drive.core.rag_search import RAGSearcher
            self._rag_searcher = RAGSearcher()
        
        results = self._rag_searcher.search(
            query=request.query,
            user_department=request.user_department,
            top_k=request.top_k
        )
        
        return results
    
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
        milvus_client.delete_by_doc_id(doc_id)
        
        # 활동 로그 (activity_logger로 통일)
        self.activity_logger.log(
            user_id=user_id,
            action="delete",
            details={"doc_id": doc_id},
            doc_id=doc_id,
        )
        
        return True
    
    async def update_metadata(
        self,
        doc_id: str,
        user_id: str,
        title: str = None,
        description: str = None,
        visibility: str = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        문서 메타데이터 수정 (Facade)
        
        수정 가능: 제목, 설명, 공개범위, 태그
        재임베딩/재처리 불필요 (메타데이터만 변경)
        """
        # 문서 존재 확인
        doc = self.db_client.get_document(doc_id)
        if not doc:
            raise ValueError("문서를 찾을 수 없습니다")
        
        # 메타데이터 수정
        result = self.db_client.update_document_metadata(
            doc_id=doc_id,
            title=title,
            description=description,
            visibility=visibility,
            tags=tags
        )
        
        if not result["success"]:
            raise ValueError(result.get("error", "메타데이터 수정 실패"))

        # [Critical Fix] Milvus 메타데이터 동기화 (visibility)
        if visibility:
            try:
                from services.ai_drive.db.milvus_client import MilvusClient
                milvus_client = MilvusClient()
                milvus_client.update_metadata(doc_id, visibility=visibility)
            except Exception as e:
                print(f"[App] Milvus Update Failed: {e}")
        
        # 활동 로그
        self.activity_logger.log(
            user_id=user_id,
            action="update_metadata",
            details={"changed_fields": result.get("changed_fields", [])},
            doc_id=doc_id,
        )
        
        return result
    
    async def chat_with_document(self, doc_id: str, request) -> Dict[str, Any]:
        """
        문서 채팅 (Facade)
        
        현재: DocumentChat으로 단순 위임
        향후: 문서 권한 체크, 사용량 제한 등 추가 가능
        """
        start = time.time()
        
        # Lazy initialization
        if not self._doc_chat:
            from services.ai_drive.core.doc_chat import DocumentChat
            self._doc_chat = DocumentChat(orchestrator=self._orchestrator)
        
        result = self._doc_chat.chat(
            doc_id=doc_id,
            question=request.question,
            user_id=request.user_id
        )
        
        # 활동 로그
        duration_ms = int((time.time() - start) * 1000)
        self.activity_logger.log(
            user_id=request.user_id,
            action="doc_chat",
            details={
                "doc_id": doc_id,
                "question": request.question[:100],
            },
            success=True,
            duration_ms=duration_ms,
            doc_id=doc_id,
        )
        
        return result
    
    # ==================== 헬퍼 메서드 ====================
    
    async def _save_temp_file(self, file: UploadFile) -> str:
        """임시 파일 저장"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            content = await file.read()
            tmp.write(content)
            return tmp.name

# Singleton
drive_service = AIDriveService()
