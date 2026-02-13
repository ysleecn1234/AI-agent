from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

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

    # B-2. 에러 체크
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # C. Save AI Response to DB (Log)
    session_id = result.get("session_id", req.context_id or "new-session")

    orchestrator.save_chat_log(
        user_id=user_id,
        session_id=session_id,
        user_input=req.message,
        ai_response=result["response"]
    )

    return {
        "response": result["response"],
        "used_model": result.get("used_model", "unknown"),
        "sources": result.get("sources", [])
    }
