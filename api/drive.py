"""
AI Drive API Router
HTTP 요청/응답 처리만 담당합니다.
Application Layer(Facade)로 위임합니다.
"""
from fastapi.responses import FileResponse, Response
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Any

from application.usecases.ai_drive.service import drive_service

import os
from application.auth import decode_access_token
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

# 인증 의존성 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("user_id")

# ==================== 라우터 설정 ====================

router = APIRouter(
    prefix="/drive",
    tags=["AI Drive"]
)

# 상수
MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1GB

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

class DocChatRequest(BaseModel):
    """문서별 채팅 요청"""
    question: str
    user_id: str = ""

class UpdateMetadataRequest(BaseModel):
    """메타데이터 수정 요청"""
    user_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[str] = None
    tags: Optional[List[str]] = None

class DocChatResponse(BaseModel):
    """문서별 채팅 응답"""
    success: bool
    doc_id: str
    question: str
    answer: str
    sources: List[Any]
    processing_time_ms: int


# ==================== API 엔드포인트 ====================

@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    creator_id: str = Form(...),
    creator_department: str = Form(...),
    title: Optional[str] = Form(None),
    description: str = Form(""),
    visibility: str = Form("team"),
    tags: str = Form(""),  # 쉼표로 구분
    user_id: str = Depends(get_current_user_id)
):
    """
    파일 업로드 API
    
    - HTTP 처리만 담당
    - Application Layer로 위임
    """
    # 기본 검증
    if not file:
        raise HTTPException(400, "파일이 없습니다")
    
    # 파일 크기 검증
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(413, "파일 크기가 1GB를 초과합니다")
    
    # Application Layer로 위임
    try:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        
        result = await drive_service.upload_document(
            file=file,
            creator_id=creator_id,
            creator_department=creator_department,
            title=title,
            description=description,
            visibility=visibility,
            tags=tag_list
        )
        
        return DocumentResponse(**result)
    except Exception as e:
        raise HTTPException(500, f"파일 업로드 실패: {str(e)}")


@router.post("/documents/chat-save", response_model=DocumentResponse)
async def save_chat(request: ChatSaveRequest, user_id: str = Depends(get_current_user_id)):
    """
    채팅 저장 API
    
    - HTTP 처리만 담당
    - Application Layer로 위임
    """
    try:
        result = await drive_service.save_chat(request)
        return DocumentResponse(**result)
    except Exception as e:
        raise HTTPException(500, f"채팅 저장 실패: {str(e)}")


@router.post("/documents/agent-save", response_model=DocumentResponse)
async def save_agent_result(request: AgentSaveRequest, user_id: str = Depends(get_current_user_id)):
    """
    에이전트 결과 저장 API
    
    - HTTP 처리만 담당
    - Application Layer로 위임
    """
    try:
        result = await drive_service.save_agent_result(request)
        return DocumentResponse(**result)
    except Exception as e:
        raise HTTPException(500, f"에이전트 결과 저장 실패: {str(e)}")


@router.post("/documents/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest, user_id: str = Depends(get_current_user_id)):
    """
    RAG 검색 API
    
    - HTTP 처리만 담당
    - Application Layer로 위임
    """
    try:
        results = await drive_service.search_documents(request)
        return SearchResponse(
            success=True,
            query=request.query,
            results=results,
            total_count=len(results)
        )
    except Exception as e:
        raise HTTPException(500, f"검색 실패: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    department: Optional[str] = Query(None),
    visibility: Optional[str] = Query(None),
    status: str = Query("active"),
    limit: int = Query(50),
    user_id: str = Depends(get_current_user_id)
):
    """
    문서 목록 조회 API
    
    - HTTP 처리만 담당
    - Application Layer로 위임
    """
    try:
        documents = await drive_service.list_documents(
            department=department,
            visibility=visibility,
            status=status,
            limit=limit
        )
        return DocumentListResponse(
            success=True,
            documents=documents,
            total_count=len(documents)
        )
    except Exception as e:
        raise HTTPException(500, f"문서 목록 조회 실패: {str(e)}")


@router.get("/documents/{doc_id}", response_model=DocumentDetail)
async def get_document(doc_id: str, user_id: str = Depends(get_current_user_id)):
    """
    문서 상세 조회 API
    
    - HTTP 처리만 담당
    - Application Layer로 위임
    """
    try:
        document = await drive_service.get_document(doc_id)
        if not document:
            raise HTTPException(404, "문서를 찾을 수 없습니다")
        return DocumentDetail(**document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"문서 조회 실패: {str(e)}")


@router.patch("/documents/{doc_id}")
async def update_document_metadata(doc_id: str, request: UpdateMetadataRequest, user_id: str = Depends(get_current_user_id)):
    """
    문서 메타데이터 수정 API
    
    수정 가능: 제목, 설명, 공개범위, 태그
    재임베딩 불필요 (메타데이터만 변경)
    """
    # 최소 1개 필드는 있어야 함
    if all(v is None for v in [request.title, request.description, request.visibility, request.tags]):
        raise HTTPException(400, "수정할 필드가 없습니다")
    
    try:
        result = await drive_service.update_metadata(
            doc_id=doc_id,
            user_id=request.user_id,
            title=request.title,
            description=request.description,
            visibility=request.visibility,
            tags=request.tags
        )
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"메타데이터 수정 실패: {str(e)}")


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user_id: str = Depends(get_current_user_id)):
    """
    문서 삭제 API (아카이브로 이동)
    """
    try:
        await drive_service.delete_document(doc_id, user_id)
        return {"success": True, "message": "문서가 삭제되었습니다"}
    except Exception as e:
        raise HTTPException(500, f"문서 삭제 실패: {str(e)}")


@router.post("/documents/{doc_id}/restore")
async def restore_document(doc_id: str, user_id: str = Depends(get_current_user_id)):
    """아카이브 문서 복원"""
    try:
        await drive_service.restore_document(doc_id, user_id)
        return {"success": True, "message": "문서가 복원되었습니다"}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"복원 실패: {str(e)}")


@router.delete("/documents/{doc_id}/permanent")
async def permanent_delete_document(doc_id: str, user_id: str = Depends(get_current_user_id)):
    """아카이브 문서 영구 삭제"""
    try:
        await drive_service.permanent_delete_document(doc_id, user_id)
        return {"success": True, "message": "문서가 영구 삭제되었습니다"}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"영구 삭제 실패: {str(e)}")

def _read_text_file_utf8(file_path: str) -> bytes:
    """텍스트 파일을 UTF-8/CP949 등에서 읽어 UTF-8 bytes로 반환 (미리보기 깨짐 방지)"""
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read().encode("utf-8")
        except (UnicodeDecodeError, LookupError):
            continue
    with open(file_path, "rb") as f:
        return f.read()


@router.get("/documents/{doc_id}/file")
async def get_document_file(doc_id: str, download: bool = Query(False), user_id: str = Depends(get_current_user_id)):
    """
    문서 원본 파일 서빙
    
    - download=false: 브라우저에서 미리보기 (PDF 등). txt/md는 charset=utf-8로 서빙해 깨짐 방지.
    - download=true: 파일 다운로드
    """
    try:
        document = await drive_service.get_document(doc_id)
        if not document:
            raise HTTPException(404, "문서를 찾을 수 없습니다")
        
        file_path = document.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(404, "파일을 찾을 수 없습니다")
        
        filename = document.get("filename", "document")
        ext = (os.path.splitext(filename)[1] or "").lower()
        is_text = ext in (".txt", ".md", ".csv")

        if download:
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/octet-stream"
            )
        if is_text:
            # 텍스트 파일: 인코딩 정규화 후 UTF-8로 응답 (미리보기 깨짐 방지)
            body = _read_text_file_utf8(file_path)
            return Response(
                content=body,
                media_type="text/plain; charset=utf-8",
            )
            
        # 오피스 파일 미리보기 분기 (다운로드가 아닌 뷰어 요청일 때 PDF 변환본 제공)
        if not download and ext in (".docx", ".pptx", ".xlsx"):
            pdf_path = file_path + ".pdf"
            if os.path.exists(pdf_path):
                return FileResponse(path=pdf_path, filename=filename.replace(ext, ".pdf"))
                
        return FileResponse(path=file_path, filename=filename)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"파일 조회 실패: {str(e)}")

@router.post("/documents/{doc_id}/chat", response_model=DocChatResponse)
async def chat_with_document(doc_id: str, request: DocChatRequest, user_id: str = Depends(get_current_user_id)):
    """
    문서 채팅 API
    
    - HTTP 처리만 담당
    - Application Layer로 위임
    """
    try:
        result = await drive_service.chat_with_document(doc_id, request)
        return DocChatResponse(**result)
    except Exception as e:
        raise HTTPException(500, f"문서 채팅 실패: {str(e)}")
