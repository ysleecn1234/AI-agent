from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from application.database import get_db
from application.auth import decode_access_token
from fastapi.security import OAuth2PasswordBearer
from application.usecases.ai_agent.service import agent_service

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
    name: str # 제목
    description: str # [New] 설명 (Step 1으로 이동)
    input_example: str
    output_example: str

class Step2Update(BaseModel):
    draft_id: str
    category: str
    # role removed (moved to description)
    visibility: str
    model_type: str
    use_rag: bool
    linked_doc_ids: List[str]

class PublishRequest(BaseModel):
    draft_id: str

# --- Endpoints ---

@router.post("/draft")
async def create_draft(req: DraftCreateRequest, user_id: str = Depends(get_current_user_id)):
    """마법사 시작: 대화 내용으로부터 초안 생성"""
    # 오케스트레이터 분석 + Redis 저장
    draft_id = await agent_service.generate_draft_from_chat(user_id, req.selected_messages)
    return {"status": "success", "draft_id": draft_id, "message": "Draft created in Redis with Orchestrator analysis."}

@router.get("/drafts")
def list_drafts(user_id: str = Depends(get_current_user_id)):
    """작업 중인 초안 목록 조회"""
    return agent_service.list_drafts(user_id)

@router.post("/draft/step1")
def update_step1(req: Step1Update, user_id: str = Depends(get_current_user_id)):
    """1단계 업데이트: 개념 정의 (이름, 예시 등)"""
    success = agent_service.update_draft(req.draft_id, req.dict(exclude={"draft_id"}))
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"status": "updated"}

@router.post("/draft/step2")
def update_step2(req: Step2Update, user_id: str = Depends(get_current_user_id)):
    """2단계 업데이트: 설정 (모델, RAG, 공개범위 등)"""
    # Redis는 주로 문자열 저장을 선호하므로, 서비스 계층에서 처리
    updates = req.dict(exclude={"draft_id"})
    updates["use_rag"] = str(req.use_rag) # Serialize bool
    success = agent_service.update_draft(req.draft_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"status": "updated"}

@router.post("/publish")
async def publish_agent(req: PublishRequest, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """최종 확정: Draft(Redis)에서 DB(Postgres)로 이동 및 벡터화"""
    try:
        # 비동기 처리: 벡터화 (Orchestrator) + DB 삽입 포함
        agent = await agent_service.publish_agent(req.draft_id, db)
        return {"status": "published", "agent_id": str(agent.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

from application.usecases.ai_hub.service import hub_service

@router.delete("/{agent_id}")
def delete_agent(agent_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """
    에이전트 삭제 (본인 소유만 가능, 공식 에이전트 불가)
    """
    result = hub_service.delete_agent(db, agent_id, user_id)
    
    if not result["success"]:
        raise HTTPException(status_code=result["code"], detail=result["message"])
        
    return {"status": "deleted", "agent_id": agent_id}
