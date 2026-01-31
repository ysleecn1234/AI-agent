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


# ==================== 요청/응답 모델 ====================

class ChatSaveRequest(BaseModel):
    """채팅 저장 요청"""
    content: str
    title: str
    creator_id: str
    creator_department: str
    description: str = ""
    visibility: str = "team"


class AgentSaveRequest(BaseModel):
    """에이전트 결과 저장 요청"""
    content: str
    title: str
    creator_id: str
    creator_department: str
    agent_name: str = ""
    description: str = ""
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
        
        pipeline.close()
        
        return DocumentResponse(
            success=True,
            doc_id=result["doc_id"],
            title=result["title"],
            chunk_count=result["chunk_count"],
            duration_ms=result["duration_ms"],
            message="문서 업로드 완료"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 임시 파일 삭제
        if temp_file_path.exists():
            temp_file_path.unlink()


@router.post("/chat-save", response_model=DocumentResponse)
async def save_chat(request: ChatSaveRequest):
    """
    채팅 결과 저장 API
    
    - 대화 내용을 문서로 저장
    - 자동 처리: 청킹 → 임베딩 → 저장
    """
    try:
        pipeline = DocumentPipeline()
        
        result = pipeline.process_chat_save(
            chat_content=request.content,
            creator_id=request.creator_id,
            creator_department=request.creator_department,
            title=request.title,
            description=request.description,
            visibility=request.visibility
        )
        
        pipeline.close()
        
        return DocumentResponse(
            success=True,
            doc_id=result["doc_id"],
            title=result["title"],
            chunk_count=result["chunk_count"],
            duration_ms=result["duration_ms"],
            message="채팅 저장 완료"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent-save", response_model=DocumentResponse)
async def save_agent_result(request: AgentSaveRequest):
    """
    에이전트 결과 저장 API
    
    - 에이전트 실행 결과를 문서로 저장
    - 자동 처리: 청킹 → 임베딩 → 저장
    """
    try:
        pipeline = DocumentPipeline()
        
        result = pipeline.process_agent_save(
            agent_output=request.content,
            creator_id=request.creator_id,
            creator_department=request.creator_department,
            title=request.title,
            agent_name=request.agent_name,
            description=request.description,
            visibility=request.visibility
        )
        
        pipeline.close()
        
        return DocumentResponse(
            success=True,
            doc_id=result["doc_id"],
            title=result["title"],
            chunk_count=result["chunk_count"],
            duration_ms=result["duration_ms"],
            message="에이전트 결과 저장 완료"
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