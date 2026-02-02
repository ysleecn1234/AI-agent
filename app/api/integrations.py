from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.api.agents import get_current_user_id
from app.services.ai_hub.service import hub_service
from app.services.ai_drive.service import drive_service

router = APIRouter(prefix="/integrations", tags=["Hub & Drive Integrations"])

# --- Hub Endpoints ---
@router.get("/hub/list")
def get_hub_agents(sort: str = "newest", category: str = None, db: Session = Depends(get_db)):
    """Get list of public agents for the Hub."""
    agents = hub_service.get_public_agents(db, sort, category)
    return [{"id": str(a.id), "name": a.name, "category": a.category, "description": a.description} for a in agents]

# --- Drive Endpoints (Stub Access) ---
@router.get("/drive/status")
def get_drive_status(user_id: str = Depends(get_current_user_id)):
    """Get storage usage."""
    return drive_service.get_user_storage_usage(user_id)

@router.get("/drive/knowledge-bases")
def get_knowledge_bases(user_id: str = Depends(get_current_user_id)):
    """Get documents for RAG linking (Wizard Step 2)."""
    return drive_service.fetch_available_knowledge(user_id)
