from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Union

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

class ChatSourceOut(BaseModel):
    id: str
    title: str
    score: float

class ChatResponse(BaseModel):
    response: str
    used_model: str
    sources: List[ChatSourceOut]
    session_id: str
    web_searched: bool = False
    web_citations: List[Union[str, dict]] = []

class RenameRequest(BaseModel):
    title: str

class MisclassificationFeedback(BaseModel):
    user_input: str
    predicted_label: str
    correct_label: str
    confidence: Optional[float] = None

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
        ai_response=result["response"],
        sources=result.get("sources", [])
    )

    return {
        "response": result["response"],
        "used_model": result.get("used_model", "unknown"),
        "sources": result.get("sources", []),
        "session_id": session_id,
        "web_searched": result.get("web_searched", False),
        "web_citations": result.get("web_citations", []),
    }


@router.post("/feedback/misclassification")
async def report_misclassification(
    req: MisclassificationFeedback,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """사용자가 분류 오류를 신고하는 엔드포인트"""
    from services.orchestrator.db.tables import MisclassificationLog
    from services.orchestrator.retrainer import trigger_retrain
    
    log = MisclassificationLog(
        user_input=req.user_input,
        predicted_label=req.predicted_label,
        correct_label=req.correct_label,
        confidence=req.confidence,
    )
    db.add(log)
    db.commit()

    # 미사용 오분류 건수 확인
    unused_count = db.query(MisclassificationLog).filter(
        MisclassificationLog.is_used == False
    ).count()

    # 100건 도달 시 재학습 트리거
    if unused_count >= 100:
        trigger_retrain(db)

    return {"status": "logged", "unused_count": unused_count}


@router.get("/sessions")
def get_chat_sessions(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """사용자의 채팅 세션 목록 조회 (커스텀 제목 우선, 없으면 첫 메시지)"""
    from services.orchestrator.db.tables import ChatLog, ChatSessionMeta
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
        db.query(ChatLog, subq.c.last_at, subq.c.first_at, ChatSessionMeta.custom_title)
        .join(subq, ChatLog.session_id == subq.c.session_id)
        .outerjoin(ChatSessionMeta, ChatLog.session_id == ChatSessionMeta.session_id)
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
            "title": row.custom_title or row.ChatLog.user_input[:60],
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
        messages.append({
            "role": "assistant", 
            "content": log.ai_response, 
            "sources": log.sources if hasattr(log, "sources") and log.sources else [],
            "created_at": log.created_at.isoformat()
        })

    return {"session_id": session_id, "messages": messages}


@router.put("/sessions/{session_id}/title")
def rename_chat_session(
    session_id: str,
    req: RenameRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """채팅 세션 제목 변경 (upsert)"""
    from services.orchestrator.db.tables import ChatLog, ChatSessionMeta

    # 해당 세션이 이 유저의 것인지 확인
    exists = (
        db.query(ChatLog)
        .filter(
            ChatLog.user_id == uuid.UUID(user_id),
            ChatLog.session_id == session_id,
        )
        .first()
    )
    if not exists:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # Upsert: 기존 메타가 있으면 업데이트, 없으면 새로 생성
    meta = db.query(ChatSessionMeta).filter(ChatSessionMeta.session_id == session_id).first()
    if meta:
        meta.custom_title = req.title.strip()
    else:
        meta = ChatSessionMeta(
            session_id=session_id,
            user_id=uuid.UUID(user_id),
            custom_title=req.title.strip()
        )
        db.add(meta)

    db.commit()
    return {"status": "ok", "session_id": session_id, "title": req.title.strip()}


@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """채팅 세션 삭제 (chat_logs + chat_session_meta 모두 삭제)"""
    from services.orchestrator.db.tables import ChatLog, ChatSessionMeta

    # 해당 세션이 이 유저의 것인지 확인
    log_count = (
        db.query(ChatLog)
        .filter(
            ChatLog.user_id == uuid.UUID(user_id),
            ChatLog.session_id == session_id,
        )
        .count()
    )
    if log_count == 0:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # chat_session_meta 삭제
    db.query(ChatSessionMeta).filter(ChatSessionMeta.session_id == session_id).delete()

    # chat_logs 삭제
    db.query(ChatLog).filter(
        ChatLog.user_id == uuid.UUID(user_id),
        ChatLog.session_id == session_id,
    ).delete()

    db.commit()
    return {"status": "ok", "deleted_session_id": session_id}

