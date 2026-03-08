import sys
import os
import uuid
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application.database import SessionLocal, User
from services.ai_hub.db.tables import Agent
from services.ai_hub.db.milvus_client import MilvusClient
from services.ai_drive.core.embedding import EmbeddingGenerator
from application.usecases.orchestrator.service import Orchestrator

# ==========================================
# 15 Essential Agents (Source List)
# ==========================================
ESSENTIAL_AGENTS = [
    # 1. 생산성 (Productivity)
    {
        "name": "회의록 정리 비서",
        "category": "생산성",
        "model_type": "GPT-4o-mini",
        "description": "지저분한 회의 녹취록(STT)을 입력하면 [핵심 안건 / 논의 내용 / 결정 사항 / Action Item]으로 깔끔하게 구조화하여 요약해줍니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "이메일 초안 작성기",
        "category": "생산성",
        "model_type": "Claude-3-Haiku",
        "description": "상황(거절, 제안, 사과 등)과 수신자를 알려주면, 격식 있고 정중한 비즈니스 이메일 초안을 작성해줍니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "보고서 요약 요정",
        "category": "생산성",
        "model_type": "GPT-4o-mini",
        "description": "긴 보고서나 문서를 1페이지 핵심 요약본(Executive Summary)으로 압축하여 바쁜 상사가 바로 이해할 수 있게 합니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "글로벌 비즈니스 번역기",
        "category": "기타",
        "model_type": "GPT-4o",
        "description": "단순 번역기가 아닙니다. 비즈니스 격식과 IT 전문 용어를 살려 한국어↔영어를 자연스럽게(Native 처럼) 번역합니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "보도자료 작성기",
        "category": "마케팅",
        "model_type": "Claude-3.5-Sonnet",
        "description": "신규 기능 출시나 업데이트 소식을 입력하면, 언론 배포용(Press Release) 보도자료 스타일로 변환합니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "코드 리뷰 파트너",
        "category": "개발",
        "model_type": "Claude-3.5-Sonnet",
        "description": "코드를 붙여넣으면 [버그/보안취약점/성능이슈/가독성] 관점에서 리뷰하고 개선된 코드를 제안합니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "API 문서 작성기",
        "category": "개발",
        "model_type": "GPT-4o-mini",
        "description": "파이썬 함수나 클래스 코드를 주면, OpenAPI(Swagger) 스타일의 명세서와 예제 요청/응답을 생성합니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "SQL 쿼리 마법사",
        "category": "개발",
        "model_type": "Claude-3.5-Sonnet",
        "description": "\"저번 달에 가입하고 결제 안 한 유저 찾아줘\"라고 말하면, 실행 가능한 SQL 쿼리를 짜줍니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "Git 커밋 메시지 생성기",
        "category": "개발",
        "model_type": "Gemini-1.5-Flash",
        "description": "`git diff` 내용을 붙여넣으면, Conventional Commits 규칙(feat, fix, refactor 등)에 맞는 메시지를 생성합니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "기획서 초안 생성기",
        "category": "기획",
        "model_type": "GPT-4o",
        "description": "아이디어 한 줄을 입력하면 [배경/목적/주요기능/User Flow/기대효과]가 포함된 PRD 초안을 작성합니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "디자인 QA 체크리스트",
        "category": "기획",
        "model_type": "GPT-4o-mini",
        "description": "기획서나 화면 설계를 입력하면, 디자이너와 개발자가 놓치기 쉬운 디테일한 QA 체크리스트를 뽑아줍니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "UX 라이팅 교정기",
        "category": "기획",
        "model_type": "Claude-3.5-Sonnet",
        "description": "딱딱한 에러 메시지나 버튼명을 사용자 친화적이고 직관적인 UX 라이팅으로 다듬어줍니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "마케팅 카피라이터",
        "category": "마케팅",
        "model_type": "Claude-3.5-Sonnet",
        "description": "제품 특징을 입력하면 인스타그램, 링크드인, 페이스북 용 홍보 카피와 해시태그를 3가지 톤으로 제안합니다.",
        "use_rag": False,
        "is_public": "PUBLIC"
    },
    {
        "name": "사내 규정 척척박사",
        "category": "인사",
        "model_type": "Gemini-1.5-Pro",
        "description": "취업규칙, 휴가, 복리후생 등 사내 규정에 대해 물어보면 관련 문서를 찾아 답변해줍니다.",
        "use_rag": True,
        "is_public": "PUBLIC"
    },
    {
        "name": "신규 입사자 가이드",
        "category": "인사",
        "model_type": "GPT-4o-mini",
        "description": "신규 입사자를 위한 친절한 멘토입니다. 와이파이 비번, 슬랙 채널, 결재 방법 등을 안내합니다.",
        "use_rag": True,
        "is_public": "PUBLIC"
    }
]

async def reseed_with_gpt():
    print("[ReSeed] 🚀 Starting GPT-5.2 Agent Generation Master Script...")
    
    db = SessionLocal()
    orchestrator = Orchestrator()
    
    milvus = None
    embedder = None
    try:
        milvus = MilvusClient()
        embedder = EmbeddingGenerator()
    except Exception as e:
        print(f"Failed to connect to Milvus: {e}")
        
    admin_email = "system_admin@ai-agent.com"
    admin = db.query(User).filter(User.email == admin_email).first()
    
    # 1. Wipe Old Data (Optional: caution if running in production)
    # db.query(Agent).delete()
    # db.commit()
    # print("[ReSeed] Wiped old Postgres agents")
    
    # 2. Loop & Generate & Save
    for agent_data in ESSENTIAL_AGENTS:
        # Skip if already exists (Optional)
        existing = db.query(Agent).filter(Agent.name == agent_data["name"]).first()
        if existing:
            print(f"[ReSeed] Skipping '{agent_data['name']}' (Already exists)")
            continue

        print(f"\n[ReSeed] Generating optimized details for '{agent_data['name']}'...")
        user_message = (
            f"나는 '{agent_data['name']}'라는 에이전트를 만들고 싶어. "
            f"이 에이전트의 역할과 특징은 다음과 같아: {agent_data['description']}. "
            "이전의 단순한 프롬프트보다 더 구체적으로 시스템 프롬프트를 작성하고 입출력 예시도 더욱 풍부하게 포함해서 전문가다운 에이전트를 기획해줘."
        )
        
        template_schema = {
            "name": agent_data["name"],
            "description": agent_data["description"],
            "category": agent_data["category"],
            "input_example": "",
            "output_example": "",
            "system_prompt": "",
            "use_rag": agent_data["use_rag"],
            "model_type": agent_data["model_type"],
            "visibility": agent_data["is_public"]
        }
        
        try:
            draft_result = await orchestrator.analyze_for_draft([{"role": "user", "content": user_message}], template_schema)
            
            new_agent = Agent(
                id=uuid.uuid4(),
                creator_id=admin.id,
                name=draft_result.get("name") or agent_data["name"],
                category=draft_result.get("category") or agent_data["category"],
                model_type=agent_data["model_type"],
                description=draft_result.get("description") or agent_data["description"],
                system_prompt=draft_result.get("system_prompt"),
                input_example=draft_result.get("input_example"),
                output_example=draft_result.get("output_example"),
                use_rag=draft_result.get("use_rag", agent_data["use_rag"]),
                is_public=draft_result.get("visibility") or agent_data["is_public"], 
                linked_knowledge_ids=[]
            )
            db.add(new_agent)
            
            if milvus and embedder:
                text_to_embed = f"{new_agent.name} {new_agent.description} {new_agent.system_prompt}"
                embedding = embedder.create(text_to_embed)
                milvus.insert_agent({
                    "id": str(new_agent.id),
                    "name": new_agent.name,
                    "description": new_agent.description,
                    "category": new_agent.category,
                    "system_prompt": new_agent.system_prompt,
                    "model_type": new_agent.model_type,
                    "visibility": new_agent.is_public,
                    "author": admin.name
                }, embedding)
                
            db.commit()
            print(f"✅ Generated & Saved: {new_agent.name}")
            await asyncio.sleep(1) # API Rate Limit protection
            
        except Exception as e:
            print(f"❌ Failed for {agent_data['name']}: {e}")
            db.rollback()

if __name__ == "__main__":
    asyncio.run(reseed_with_gpt())
