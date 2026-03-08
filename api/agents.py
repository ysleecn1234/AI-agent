from fastapi import APIRouter, Depends, HTTPException, Query
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

from typing import Literal

# ...

class Step2Update(BaseModel):
    draft_id: str
    category: str
    # role removed (moved to description)
    visibility: Literal["PRIVATE", "TEAM", "PUBLIC"] # [Updated] COMPANY -> PUBLIC
    model_type: str
    use_rag: bool
    linked_doc_ids: List[str]

class PublishRequest(BaseModel):
    draft_id: str


class RecommendRequest(BaseModel):
    """에이전트 추천 요청 (채팅 내용 + 대화 맥락 + 부서)"""
    query: str
    conversation_history: Optional[List[dict]] = None  # [{"role": "user"|"assistant", "content": "..."}]
    department: Optional[str] = None  # 사용자 부서 (예: 마케팅팀)

# --- Endpoints ---

@router.post("/draft")
async def create_draft(req: DraftCreateRequest, user_id: str = Depends(get_current_user_id)):
    """마법사 시작: 대화 내용으로부터 초안 생성 (내용 기반 name/description/category 등 자동 채움)"""
    draft_id, filled = await agent_service.generate_draft_from_chat(user_id, req.selected_messages)
    return {"status": "success", "draft_id": draft_id, "filled": filled, "message": "Draft created in Redis with Orchestrator analysis."}

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

@router.get("/")
def list_agents(
    sort_by: str = "newest",
    category: str = None,
    department: str = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """배포된 에이전트 목록 조회 (department 지정 시 해당 부서 관련 에이전트 우선)"""
    agents = hub_service.get_public_agents(db, sort_by=sort_by, category=category)
    
    result = [
        {
            "id": str(a.id),
            "name": a.name,
            "description": a.description,
            "category": getattr(a, 'category', '기타'),
            "visibility": a.is_public,
            "creator_id": str(a.creator_id) if a.creator_id else None,
            "creator_department": None,
            "model_type": getattr(a, 'model_type', 'AUTO'),
            "use_rag": getattr(a, 'use_rag', False),
            "system_prompt": getattr(a, 'system_prompt', ''),
            "is_active": True,
        }
        for a in agents
    ]
    
    # 부서 기반 우선 정렬: 에이전트 카테고리가 사용자 부서와 관련 있으면 상위로
    if department:
        # "마케팅팀" → "마케팅" 으로 키워드 추출 (팀/부/실/센터 제거)
        import re
        dept_keyword = re.sub(r'(팀|부|실|센터|본부|파트)$', '', department)
        
        def dept_match_score(agent):
            cat = (agent.get("category") or "").lower()
            kw = dept_keyword.lower()
            if kw and kw in cat:
                return 0  # 카테고리가 부서 키워드 포함 → 최우선
            return 1
        
        result.sort(key=dept_match_score)
    
    return result

@router.get("/recommend")
async def recommend_agents_get(
    query: str = Query(...),
    user_id: str = Depends(get_current_user_id)
):
    """채팅 입력 기반 에이전트 추천 (GET, 대화 히스토리 없음)"""
    try:
        recommendations = await agent_service.recommend_agents_for_chat(query, conversation_history=None)
        return {"status": "success", "recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend_agents_post(
    req: RecommendRequest,
    user_id: str = Depends(get_current_user_id)
):
    """채팅 입력 + 대화 히스토리 + 부서 기반 에이전트 추천 (권장)"""
    try:
        recommendations = await agent_service.recommend_agents_for_chat(
            req.query,
            conversation_history=req.conversation_history,
            department=req.department
        )
        return {"status": "success", "recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}")
def get_agent_detail(
    agent_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """에이전트 상세 조회"""
    agent = hub_service.get_agent_details(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "id": str(agent.id),
        "name": agent.name,
        "description": agent.description,
        "category": getattr(agent, 'category', '기타'),
        "system_prompt": agent.system_prompt,
        "input_example": getattr(agent, 'input_example', ''),
        "output_example": getattr(agent, 'output_example', ''),
        "visibility": agent.is_public,
        "creator_id": str(agent.creator_id) if agent.creator_id else None,
        "model_type": agent.model_type,
        "use_rag": agent.use_rag,
        "is_active": True,
    }

class UpdateAgentRequest(BaseModel):
    """에이전트 수정 요청"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    system_prompt: Optional[str] = None
    input_example: Optional[str] = None
    output_example: Optional[str] = None
    model_type: Optional[str] = None
    use_rag: Optional[bool] = None
    visibility: Optional[str] = None  # "PRIVATE" | "TEAM" | "PUBLIC"

@router.put("/{agent_id}")
def update_agent(
    agent_id: str,
    req: UpdateAgentRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """에이전트 수정 (DB + 벡터 DB 동시 업데이트)"""
    from services.ai_hub.db.tables import Agent
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 필드 업데이트 (None이 아닌 값만)
    if req.name is not None:
        agent.name = req.name
    if req.description is not None:
        agent.description = req.description
    if req.category is not None:
        agent.category = req.category
    if req.system_prompt is not None:
        agent.system_prompt = req.system_prompt
    if req.input_example is not None:
        agent.input_example = req.input_example
    if req.output_example is not None:
        agent.output_example = req.output_example
    if req.model_type is not None:
        agent.model_type = req.model_type
    if req.use_rag is not None:
        agent.use_rag = req.use_rag
    if req.visibility is not None:
        agent.is_public = req.visibility
    
    db.commit()
    db.refresh(agent)
    
    # 벡터 DB 업데이트 (이름/설명/카테고리 변경 시 임베딩 재생성)
    if any([req.name, req.description, req.category]):
        try:
            from services.ai_hub.core.agent.manager import agent_manager
            import asyncio
            loop = asyncio.new_event_loop()
            loop.run_until_complete(agent_manager.update_agent_vector(agent))
            loop.close()
        except Exception as e:
            print(f"[Warning] 벡터 DB 업데이트 실패 (DB는 정상 저장됨): {e}")
    
    return {
        "status": "updated",
        "agent": {
            "id": str(agent.id),
            "name": agent.name,
            "description": agent.description,
            "category": getattr(agent, 'category', '기타'),
            "system_prompt": agent.system_prompt,
            "model_type": agent.model_type,
            "use_rag": agent.use_rag,
            "visibility": agent.is_public,
        }
    }

@router.delete("/{agent_id}")
def delete_agent(agent_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """
    에이전트 삭제 (본인 소유만 가능, 공식 에이전트 불가)
    """
    result = hub_service.delete_agent(db, agent_id, user_id)
    
    if not result["success"]:
        raise HTTPException(status_code=result["code"], detail=result["message"])
        
    return {"status": "deleted", "agent_id": agent_id}
