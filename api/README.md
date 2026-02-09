# API Layer

## 역할
HTTP 요청/응답 처리만 담당합니다.

## 책임
- **Request validation**: Pydantic 모델로 입력 검증
- **Response formatting**: 일관된 응답 형식
- **HTTP status code**: 적절한 상태 코드 반환
- **Application Layer 위임**: 비즈니스 로직은 Application Layer로 전달

## 하지 않는 것
- ❌ 비즈니스 로직
- ❌ 데이터베이스 직접 접근
- ❌ 복잡한 계산이나 처리

---

## 폴더 구조

```
api/
├── main.py           # FastAPI 애플리케이션 및 라우터 등록
├── database.py       # DB 세션 관리
├── auth.py           # 인증 API (로그인, 회원가입)
├── agents.py         # AI Hub API (에이전트 생성/관리)
├── drive.py          # AI Drive API (문서 업로드/검색/채팅)
├── chat.py           # Orchestrator API (통합 채팅)
└── README.md         # 이 파일
```

---

## 파일별 설명

### `main.py`
FastAPI 애플리케이션 생성 및 모든 라우터를 등록합니다.
- CORS 설정
- Lifespan 이벤트 (DB 초기화 등)
- Health check 엔드포인트

### `database.py`
데이터베이스 연결 및 세션 관리를 담당합니다.
- SQLAlchemy engine 생성
- `get_db()` dependency 제공

### `auth.py` - 인증 API
사용자 인증 관련 엔드포인트:
- `POST /auth/register` - 회원가입
- `POST /auth/login` - 로그인
- `GET /auth/me` - 현재 사용자 정보

### `agents.py` - AI Hub API
에이전트 생성 및 관리 엔드포인트:
- `POST /agents/draft` - 에이전트 초안 생성
- `GET /agents/drafts` - 초안 목록
- `POST /agents/draft/step1` - 1단계 업데이트
- `POST /agents/draft/step2` - 2단계 업데이트
- `POST /agents/publish` - 에이전트 배포

### `drive.py` - AI Drive API
문서 관리 및 RAG 검색 엔드포인트:
- `POST /drive/documents/upload` - 파일 업로드
- `POST /drive/documents/chat-save` - 채팅 저장
- `POST /drive/documents/agent-save` - 에이전트 결과 저장
- `POST /drive/documents/search` - RAG 검색
- `GET /drive/documents` - 문서 목록
- `GET /drive/documents/{doc_id}` - 문서 상세
- `DELETE /drive/documents/{doc_id}` - 문서 삭제
- `POST /drive/documents/{doc_id}/chat` - 문서 채팅

### `chat.py` - Orchestrator API
통합 채팅 엔드포인트:
- `POST /chat` - 오케스트레이터 채팅

---

## 예시: Drive API

```python
@router.post("/drive/documents/upload")
async def upload_document(file: UploadFile, creator_id: str, ...):
    """파일 업로드 - HTTP 처리만"""
    # 1. 기본 검증
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(413, "파일 크기 초과")
    
    # 2. Application Layer로 위임
    result = await drive_service.upload_document(file, creator_id, ...)
    
    # 3. 응답 포맷팅
    return DocumentResponse(**result)
```

---

## 일관성
모든 API 파일이 동일한 패턴을 따릅니다:
- Request → Validation → Service 호출 → Response

