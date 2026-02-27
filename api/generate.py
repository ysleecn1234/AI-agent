"""
Generate API Router
문서 메타데이터(제목/설명) 자동 생성용 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from application.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("user_id")

router = APIRouter(
    prefix="/generate",
    tags=["Generate"]
)


class DocumentMetadataRequest(BaseModel):
    content: str   # 채팅 내용 (최대 3000자 사용)


class DocumentMetadataResponse(BaseModel):
    title: str
    description: str


@router.post("/document-metadata", response_model=DocumentMetadataResponse)
async def generate_document_metadata(
    request: DocumentMetadataRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    채팅 내용을 기반으로 문서 제목과 한줄 설명을 LLM으로 자동 생성합니다.
    """
    from application.usecases.orchestrator.service import orchestrator
    import json

    content_snippet = request.content[:3000]

    prompt = (
        "다음 대화 내용을 분석하여 적절한 문서 제목과 한 줄 설명을 JSON으로 생성하세요.\n"
        "반드시 아래 JSON 형식만 출력하세요. 다른 텍스트는 출력하지 마세요.\n\n"
        '{"title": "문서 제목 (50자 이내)", "description": "문서의 핵심 내용을 한 줄로 요약한 설명 (80자 이내)"}\n\n'
        f"대화 내용:\n{content_snippet}"
    )

    try:
        result = orchestrator.call_llm(task="title_gen", prompt=prompt)
        response_text = result["content"].strip()

        # 마크다운 코드블록 제거
        if "```" in response_text:
            parts = response_text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:]
                try:
                    data = json.loads(part.strip())
                    if "title" in data:
                        response_text = part.strip()
                        break
                except Exception:
                    continue

        data = json.loads(response_text)
        title = (data.get("title") or "").strip() or "채팅 대화 내용"
        description = (data.get("description") or "").strip() or "AI와의 대화 내용을 정리한 문서입니다."
        return {"title": title, "description": description}

    except Exception as e:
        print(f"[Generate] 메타데이터 생성 실패: {e}")
        # LLM 실패 시 단순 fallback (첫 줄 기반)
        lines = [l.strip() for l in content_snippet.split("\n") if l.strip()]
        first_line = lines[0][:50] if lines else "채팅 대화"
        return {
            "title": first_line,
            "description": "AI와의 대화 내용을 정리한 문서입니다."
        }
