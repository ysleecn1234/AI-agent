from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.auth import decode_access_token
from fastapi.security import OAuth2PasswordBearer
from app.services.ai_agent.service import agent_service

router = APIRouter(prefix="/agents", tags=["Agent Factory"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("user_id")

# --- Request Models ---
class DraftCreateRequest(BaseModel):
    selected_messages: List[dict] # [{"role": "user", "content": "..."}]

class Step1Update(BaseModel):
    draft_id: str
    name: str
    input_example: str
    output_example: str

class Step2Update(BaseModel):
    draft_id: str
    category: str
    role: str # description
    visibility: str
    model_type: str
    use_rag: bool
    linked_doc_ids: List[str]

class PublishRequest(BaseModel):
    draft_id: str

# --- Endpoints ---

@router.post("/draft")
async def create_draft(req: DraftCreateRequest, user_id: str = Depends(get_current_user_id)):
    """Start Wizard: Create a draft from chat history."""
    draft_id = await agent_service.create_draft(user_id, req.selected_messages)
    return {"status": "success", "draft_id": draft_id, "message": "Draft created in Redis."}

@router.get("/drafts")
def list_drafts(user_id: str = Depends(get_current_user_id)):
    """View 'Work in Progress' list."""
    return agent_service.list_drafts(user_id)

@router.post("/draft/step1")
def update_step1(req: Step1Update, user_id: str = Depends(get_current_user_id)):
    """Update Definition (Name, Examples)."""
    success = agent_service.update_draft(req.draft_id, req.dict(exclude={"draft_id"}))
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"status": "updated"}

@router.post("/draft/step2")
def update_step2(req: Step2Update, user_id: str = Depends(get_current_user_id)):
    """Update Configuration (Model, RAG)."""
    # Redis stores flat strings mostly, handling complexity in service
    updates = req.dict(exclude={"draft_id"})
    updates["use_rag"] = str(req.use_rag) # Serialize bool
    success = agent_service.update_draft(req.draft_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"status": "updated"}

@router.post("/publish")
def publish_agent(req: PublishRequest, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Finalize: Move from Draft(Redis) to DB(Postgres)."""
    try:
        agent = agent_service.publish_agent(req.draft_id, db)
        return {"status": "published", "agent_id": str(agent.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
