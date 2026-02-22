from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from application.auth import decode_access_token
from application.database import get_db
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from application.usecases.orchestrator.service import orchestrator
import uuid

router = APIRouter(prefix="/chat", tags=["Chat"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# 1. Request Schema
class ChatRequest(BaseModel):
    message: str
    model_type: str = "AUTO"
    use_rag: bool = False
    agent_id: Optional[str] = None
    context_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    used_model: str
    sources: List[str]
    session_id: str

# 2. Helper to get current user
def get_current_user_id(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return payload.get("user_id")

# 3. Chat Endpoint
@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest, 
    user_id: str = Depends(get_current_user_id)
):
    # A. Save User Input to DB (Log)
    # TODO: Generate session_id logic
    
    # B. Call Orchestrator
    result = await orchestrator.process(
        user_input=req.message,  # [Fix] 사용자 메시지 전달 누락 수정
        user_id=user_id,
        context_id=req.context_id,
        model_type=req.model_type,
        use_rag=req.use_rag,
        agent_id=req.agent_id
    )

    # B-2. 에러 체크
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # C. Save AI Response to DB (Log)
    session_id = req.context_id or result.get("session_id") or str(uuid.uuid4())

    orchestrator.save_chat_log(
        user_id=user_id,
        session_id=session_id,
        user_input=req.message,
        ai_response=result["response"]
    )

    return {
        "response": result["response"],
        "used_model": result.get("used_model", "unknown"),
        "sources": result.get("sources", []),
        "session_id": session_id
    }


@router.get("/sessions")
def get_chat_sessions(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """사용자의 채팅 세션 목록 조회 (session_id별 최신 메시지 기준)"""
    from services.orchestrator.db.tables import ChatLog
    from sqlalchemy import func

    # session_id별 최신 created_at과 첫 user_input을 가져옴
    subq = (
        db.query(
            ChatLog.session_id,
            func.max(ChatLog.created_at).label("last_at"),
            func.min(ChatLog.created_at).label("first_at"),
        )
        .filter(ChatLog.user_id == uuid.UUID(user_id))
        .group_by(ChatLog.session_id)
        .subquery()
    )

    rows = (
        db.query(ChatLog, subq.c.last_at, subq.c.first_at)
        .join(subq, ChatLog.session_id == subq.c.session_id)
        .filter(
            ChatLog.user_id == uuid.UUID(user_id),
            ChatLog.created_at == subq.c.first_at,
        )
        .order_by(subq.c.last_at.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "session_id": row.ChatLog.session_id,
            "title": row.ChatLog.user_input[:60],
            "last_at": row.last_at.isoformat() if row.last_at else None,
            "first_at": row.first_at.isoformat() if row.first_at else None,
        }
        for row in rows
    ]


@router.get("/sessions/{session_id}")
def get_chat_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """특정 세션의 대화 내용 조회"""
    from services.orchestrator.db.tables import ChatLog

    logs = (
        db.query(ChatLog)
        .filter(
            ChatLog.user_id == uuid.UUID(user_id),
            ChatLog.session_id == session_id,
        )
        .order_by(ChatLog.created_at.asc())
        .all()
    )

    if not logs:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    messages = []
    for log in logs:
        messages.append({"role": "user", "content": log.user_input, "created_at": log.created_at.isoformat()})
        messages.append({"role": "assistant", "content": log.ai_response, "created_at": log.created_at.isoformat()})

    return {"session_id": session_id, "messages": messages}
