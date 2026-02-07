from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from application.database import get_db
from services.orchestrator.db.tables import ChatLog
from application.database import User
from application.auth import decode_access_token
from fastapi.security import OAuth2PasswordBearer
from application.usecases.orchestrator.service import orchestrator

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
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # A. Save User Input to DB (Log)
    # TODO: Generate session_id logic
    
    # B. Call Orchestrator
    result = await orchestrator.process(
        user_input=req.message,
        user_id=user_id,
        context_id=req.context_id,
        model_type=req.model_type,
        use_rag=req.use_rag
    )

    # C. Save AI Response to DB (Log)
    new_log = ChatLog(
        user_id=user_id,
        session_id=req.context_id or "new-session",
        user_input=req.message,
        ai_response=result["response"]
    )
    db.add(new_log)
    db.commit()

    return {
        "response": result["response"],
        "used_model": result["used_model"],
        "sources": result["sources"]
    }
