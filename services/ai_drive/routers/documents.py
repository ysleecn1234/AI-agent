"""
AI 드라이브 - 문서 API 라우터
파일 업로드, 채팅 저장, 에이전트 저장
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import magic
from typing import Any
from core.pii_detector import PIIDetector

# 상위 디렉토리 import 설정
import sys
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from pipeline import DocumentPipeline


# ==================== 라우터 설정 ====================

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

# 임시 파일 저장 경로
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 영구 파일 저장 경로
STORAGE_DIR = Path(__file__).parent.parent / "storage"
STORAGE_DIR.mkdir(exist_ok=True)


# ==================== 요청/응답 모델 ====================

class ChatSaveRequest(BaseModel):
    """채팅 저장 요청"""
    content: str
    title: Optional[str] = None
    creator_id: str
    creator_department: str
    description: Optional[str] = None
    visibility: str = "team"

class AgentSaveRequest(BaseModel):
    """에이전트 결과 저장 요청"""
    content: str
    title: Optional[str] = None
    creator_id: str
    creator_department: str
    agent_name: str = ""
    description: Optional[str] = None
    visibility: str = "team"

class DocumentResponse(BaseModel):
    """문서 처리 응답"""
    success: bool
    doc_id: str
    title: str
    chunk_count: int
    duration_ms: int
    message: str = ""


# ==================== API 엔드포인트 ====================

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    creator_id: str = Form(...),
    creator_department: str = Form(...),
    title: Optional[str] = Form(None),
    description: str = Form(""),
    visibility: str = Form("team"),
    tags: str = Form("")  # 쉼표로 구분된 태그
):
    """
    파일 업로드 API
    
    - 지원 형식: PDF, DOCX, PPTX, TXT, MD, CSV
    - 자동 처리: 파싱 → 청킹 → 임베딩 → 저장
    """

    # 파일 크기 제한 (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    file.file.seek(0, 2)  # 파일 끝으로 이동
    file_size = file.file.tell()  # 현재 위치 = 파일 크기
    file.file.seek(0)  # 다시 처음으로
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기가 50MB를 초과합니다. (현재: {file_size / 1024 / 1024:.1f}MB)"
        )

    # 허용된 MIME 타입
    ALLOWED_MIME_TYPES = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
        'text/plain': '.txt',
        'text/markdown': '.md',
        'text/csv': '.csv',
    }

    # 파일 내용으로 실제 타입 확인
    file_content = await file.read()
    await file.seek(0)  # 다시 처음으로

    mime_type = magic.from_buffer(file_content, mime=True)

    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"지원하지 않는 파일 형식입니다. (감지된 타입: {mime_type})"
        )

    # 파일 확장자 확인
    file_ext = Path(file.filename).suffix.lower()
    supported = ['.pdf', '.docx', '.pptx', '.txt', '.md', '.csv']
    
    if file_ext not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 지원: {supported}"
        )
    
    # 임시 파일 저장
    temp_file_path = UPLOAD_DIR / f"{uuid.uuid4()}{file_ext}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 태그 처리
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        
        # 개인정보 감지
        from utils.file_parser import FileParser
        parser = FileParser()
        text_content = parser.parse(str(temp_file_path))
        
        pii_detector = PIIDetector()
        pii_result = pii_detector.detect(text_content)
        
        # 주민등록번호 포함 시 무조건 차단
        if pii_detector.contains_critical_pii(text_content):
            raise HTTPException(
                status_code=400,
                detail="주민등록번호가 포함된 파일은 업로드할 수 없습니다."
            )
        
        # 기타 개인정보 포함 시 경고 (일단 차단)
        if pii_result["has_pii"]:
            pii_types = [f["type"] for f in pii_result["findings"]]
            raise HTTPException(
                status_code=400,
                detail=f"개인정보가 포함되어 업로드가 차단되었습니다. (감지: {', '.join(pii_types)})"
            )

        # 파이프라인 실행
        pipeline = DocumentPipeline()

        result = pipeline.process_file_upload(
            file_path=str(temp_file_path),
            creator_id=creator_id,
            creator_department=creator_department,
            title=title or Path(file.filename).stem,
            description=description,
            visibility=visibility,
            tags=tag_list
        )

        # 영구 저장 경로로 파일 이동
        doc_id = result["doc_id"]
        permanent_path = STORAGE_DIR / f"{doc_id}{file_ext}"
        shutil.move(str(temp_file_path), str(permanent_path))

        # DB에 파일 경로 업데이트
        pipeline.postgres_client.update_file_path(doc_id, str(permanent_path))

        pipeline.close()
        
        return DocumentResponse(
            success=True,
            doc_id=result["doc_id"],
            title=result["title"],
            chunk_count=result["chunk_count"],
            duration_ms=result["duration_ms"],
            message="문서 업로드 완료"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 임시 파일 삭제
        if temp_file_path.exists():
            temp_file_path.unlink()


@router.post("/chat-save", response_model=DocumentResponse)
async def save_chat(request: ChatSaveRequest):
    """채팅 결과 저장 API"""
    try:
        pipeline = DocumentPipeline()

        # 개인정보 감지
        pii_detector = PIIDetector()
        pii_result = pii_detector.detect(request.content)
        
        # 주민등록번호 포함 시 무조건 차단
        if pii_detector.contains_critical_pii(request.content):
            raise HTTPException(
                status_code=400,
                detail="주민등록번호가 포함된 내용은 저장할 수 없습니다."
            )
        
        # 기타 개인정보 포함 시 차단
        if pii_result["has_pii"]:
            pii_types = [f["type"] for f in pii_result["findings"]]
            raise HTTPException(
                status_code=400,
                detail=f"개인정보가 포함되어 저장이 차단되었습니다. (감지: {', '.join(pii_types)})"
            )
        
        # 제목/설명 자동 생성 (없으면)
        title = request.title
        description = request.description
        
        if not title:
            from core.auto_tagger import AutoTagger
            tagger = AutoTagger()
            generated = tagger.generate_title_and_description(request.content)
            title = generated["title"]
            if not description:
                description = generated["description"]
        
        result = pipeline.process_chat_save(
            chat_content=request.content,
            creator_id=request.creator_id,
            creator_department=request.creator_department,
            title=title,
            description=description or "",
            visibility=request.visibility
        )

        # 원본 텍스트 파일로 저장
        doc_id = result["doc_id"]
        text_file_path = STORAGE_DIR / f"{doc_id}.txt"
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(request.content)

        # DB에 파일 경로 업데이트
        pipeline.postgres_client.update_file_path(doc_id, str(text_file_path))

        pipeline.close()    
            
        return DocumentResponse(
            success=True,
            doc_id=result["doc_id"],
            title=result["title"],
            chunk_count=result["chunk_count"],
            duration_ms=result["duration_ms"],
            message="채팅 저장 완료"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent-save", response_model=DocumentResponse)
async def save_agent_result(request: AgentSaveRequest):
    """에이전트 결과 저장 API"""
    try:
        pipeline = DocumentPipeline()

        # 개인정보 감지
        pii_detector = PIIDetector()
        pii_result = pii_detector.detect(request.content)
        
        # 주민등록번호 포함 시 무조건 차단
        if pii_detector.contains_critical_pii(request.content):
            raise HTTPException(
                status_code=400,
                detail="주민등록번호가 포함된 내용은 저장할 수 없습니다."
            )
        
        # 기타 개인정보 포함 시 차단
        if pii_result["has_pii"]:
            pii_types = [f["type"] for f in pii_result["findings"]]
            raise HTTPException(
                status_code=400,
                detail=f"개인정보가 포함되어 저장이 차단되었습니다. (감지: {', '.join(pii_types)})"
            )
        
        # 제목/설명 자동 생성 (없으면)
        title = request.title
        description = request.description
        
        if not title:
            from core.auto_tagger import AutoTagger
            tagger = AutoTagger()
            generated = tagger.generate_title_and_description(request.content)
            title = generated["title"]
            if not description:
                description = generated["description"]
        
        result = pipeline.process_agent_save(
            agent_output=request.content,
            creator_id=request.creator_id,
            creator_department=request.creator_department,
            title=title,
            agent_name=request.agent_name,
            description=description or "",
            visibility=request.visibility
        )
        
        # 원본 텍스트 파일로 저장
        doc_id = result["doc_id"]
        text_file_path = STORAGE_DIR / f"{doc_id}.txt"
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(request.content)
        
        # DB에 파일 경로 업데이트
        pipeline.postgres_client.update_file_path(doc_id, str(text_file_path))
        
        pipeline.close()

        return DocumentResponse(
            success=True,
            doc_id=result["doc_id"],
            title=result["title"],
            chunk_count=result["chunk_count"],
            duration_ms=result["duration_ms"],
            message="에이전트 결과 저장 완료"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 문서 조회 API (Phase 2-8) ====================

class SearchRequest(BaseModel):
    """RAG 검색 요청"""
    query: str
    user_department: str
    top_k: int = 5


class SearchResultItem(BaseModel):
    """검색 결과 아이템"""
    doc_id: str
    content: str
    source: str
    score: float
    author: str
    department: str
    date: str
    freshness_bonus: float = 0


class SearchResponse(BaseModel):
    """RAG 검색 응답"""
    success: bool
    query: str
    results: List[SearchResultItem]
    total_count: int


class DocumentDetail(BaseModel):
    """문서 상세 정보"""
    doc_id: str
    title: str
    description: str
    creator_id: str
    creator_department: str
    created_at: str
    modified_at: str
    visibility: str
    status: str
    file_size: int
    file_type: str
    version: int
    is_latest: bool
    tags: List[str]
    filename: str
    source_type: str
    chunk_count: int


class DocumentListItem(BaseModel):
    """문서 목록 아이템"""
    doc_id: str
    title: str
    creator_department: str
    visibility: str
    status: str
    file_type: str
    version: int
    modified_at: str
    tags: List[str]


class DocumentListResponse(BaseModel):
    """문서 목록 응답"""
    success: bool
    documents: List[DocumentListItem]
    total_count: int


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    RAG 4단계 검색 API
    
    - 질문 임베딩 → 유사도 검색 → 권한 필터 → Freshness Score
    - 오케스트레이터 Researcher에서 호출
    """
    from core.rag_search import RAGSearcher
    
    try:
        searcher = RAGSearcher()
        
        results = searcher.search(
            query=request.query,
            user_department=request.user_department,
            top_k=request.top_k
        )
        
        searcher.close()
        
        return SearchResponse(
            success=True,
            query=request.query,
            results=[
                SearchResultItem(
                    doc_id=r.get("doc_id", ""),
                    content=r.get("content", ""),
                    source=r.get("source", "알 수 없음"),
                    score=r.get("score", 0),
                    author=r.get("author", ""),
                    department=r.get("department", ""),
                    date=r.get("date", ""),
                    freshness_bonus=r.get("freshness_bonus", 0)
                )
                for r in results
            ],
            total_count=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    department: Optional[str] = None,
    visibility: Optional[str] = None,
    status: str = "active",
    limit: int = 50
):
    """
    문서 목록 조회 API
    
    - 필터: 부서, 공개범위, 상태
    - 최신 버전만 조회 (is_latest=True)
    """
    try:
        pipeline = DocumentPipeline()
        
        docs = pipeline.postgres_client.list_documents(
            creator_department=department,
            visibility=visibility,
            status=status,
            is_latest=True,
            limit=limit
        )
        
        pipeline.close()
        
        return DocumentListResponse(
            success=True,
            documents=[
                DocumentListItem(
                    doc_id=d.get("doc_id", ""),
                    title=d.get("title", ""),
                    creator_department=d.get("creator_department", ""),
                    visibility=d.get("visibility", "team"),
                    status=d.get("status", "active"),
                    file_type=d.get("file_type", ""),
                    version=d.get("version", 1),
                    modified_at=d.get("modified_at", ""),
                    tags=d.get("tags", [])
                )
                for d in docs
            ],
            total_count=len(docs)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(doc_id: str):
    """
    문서 상세 조회 API
    
    - 메타데이터 전체 반환
    - 출처 정보 포함
    """
    try:
        pipeline = DocumentPipeline()
        
        doc = pipeline.postgres_client.get_document(doc_id)
        
        pipeline.close()
        
        if not doc:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
        
        return DocumentDetail(
            doc_id=doc.get("doc_id", ""),
            title=doc.get("title", ""),
            description=doc.get("description", ""),
            creator_id=doc.get("creator_id", ""),
            creator_department=doc.get("creator_department", ""),
            created_at=doc.get("created_at", ""),
            modified_at=doc.get("modified_at", ""),
            visibility=doc.get("visibility", "team"),
            status=doc.get("status", "active"),
            file_size=doc.get("file_size", 0),
            file_type=doc.get("file_type", ""),
            version=doc.get("version", 1),
            is_latest=doc.get("is_latest", True),
            tags=doc.get("tags", []),
            filename=doc.get("filename", ""),
            source_type=doc.get("source_type", "file"),
            chunk_count=doc.get("chunk_count", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doc_id}/versions")
async def get_version_history(doc_id: str):
    """
    문서 버전 히스토리 조회 API
    """
    try:
        pipeline = DocumentPipeline()
        
        history = pipeline.postgres_client.get_version_history(doc_id)
        
        pipeline.close()
        
        if not history:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "versions": history,
            "total_versions": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{doc_id}")
async def delete_document(doc_id: str, user_id: str):
    """
    문서 삭제 API
    
    - 실제 삭제가 아닌 상태 변경 (archived)
    - Milvus 벡터도 삭제
    - 활동 로그 기록
    """
    try:
        pipeline = DocumentPipeline()
        
        # 문서 존재 확인
        doc = pipeline.postgres_client.get_document(doc_id)
        if not doc:
            pipeline.close()
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
        
        # PostgreSQL 상태 변경 (archived)
        pipeline.postgres_client.delete_document(doc_id)
        
        # Milvus에서 벡터 삭제
        pipeline.milvus_client.delete_by_doc_id(doc_id)
        
        # 활동 로그 기록
        pipeline.postgres_client.log_activity(
            user_id=user_id,
            action="delete",
            doc_id=doc_id,
            success=True,
            details={"title": doc.get("title", "")}
        )
        
        pipeline.close()
        
        return {
            "success": True,
            "message": "문서가 삭제되었습니다",
            "doc_id": doc_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 문서별 채팅 API ====================

class DocChatRequest(BaseModel):
    """문서별 채팅 요청"""
    question: str
    user_id: str = ""


class DocChatResponse(BaseModel):
    """문서별 채팅 응답"""
    success: bool
    doc_id: str
    question: str
    answer: str
    sources: List[Any]
    processing_time_ms: int


@router.post("/{doc_id}/chat", response_model=DocChatResponse)
async def chat_with_document(doc_id: str, request: DocChatRequest):
    """
    문서별 채팅 API
    
    - 특정 문서 내에서만 질문/답변
    - 5단계 SLM 파이프라인 (Router → Researcher → Reasoner → Synthesizer → Guardrail)
    """
    from core.doc_chat import DocumentChat
    
    try:
        doc_chat = DocumentChat()
        
        result = doc_chat.chat(
            doc_id=doc_id,
            question=request.question,
            user_id=request.user_id
        )
        
        doc_chat.close()
        
        return DocChatResponse(
            success=True,
            doc_id=doc_id,
            question=request.question,
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            processing_time_ms=result.get("processing_time_ms", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 테스트 코드 ====================

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="AI 드라이브 API 테스트")
    app.include_router(router)
    
    print("=" * 80)
    print("AI 드라이브 문서 API 서버 시작")
    print("=" * 80)
    print("API 문서: http://localhost:8001/docs")
    print("=" * 80)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)