# Application Layer (Facade Pattern)

## 역할
Service Layer를 조율하는 **Facade 패턴**을 따릅니다.

## Facade 패턴이란?
복잡한 Service Layer를 단순한 인터페이스로 감싸는 디자인 패턴입니다.

## 왜 Facade 패턴인가?

### 현재 구조
- 대부분의 요청이 **단일 Service 호출**로 처리됨
- 복잡한 워크플로우가 많지 않음
- Service Layer로 **일단 단순 위임**이 주요 역할

### 향후 확장 가능성
프로젝트가 커지면 이 레이어에서:
- ✅ **여러 Service 조합**: Pipeline + RAGSearcher + Orchestrator
- ✅ **복잡한 워크플로우**: 단계별 처리 및 조율
- ✅ **트랜잭션 관리**: 여러 DB 작업 통합
- ✅ **공통 에러 핸들링**: 일관된 에러 처리

---

## 폴더 구조

```
application/
├── usecases/
│   ├── ai_agent/
│   │   └── service.py     # Hub Facade (에이전트 생성/관리)
│   ├── ai_drive/
│   │   └── service.py     # Drive Facade (문서 처리)
│   └── orchestrator/
│       └── service.py     # Orchestrator Facade (통합 채팅)
├── database.py            # DB 설정
├── auth.py                # 인증 유틸리티
└── README.md              # 이 파일
```

---

## 파일별 설명

### `usecases/ai_agent/service.py` - Hub Facade
AI Hub의 에이전트 관련 비즈니스 워크플로우를 조율합니다.

**주요 메서드**:
- `generate_draft_from_chat()` - 대화에서 초안 생성
- `list_drafts()` - 초안 목록 조회
- `update_draft()` - 초안 업데이트
- `publish_agent()` - 에이전트 배포
- `recommend_agents_for_chat()` - 에이전트 추천

**현재**: `AgentManager`로 단순 위임  
**향후**: 권한 체크, 검증, 여러 서비스 조합 가능

### `usecases/ai_drive/service.py` - Drive Facade
AI Drive의 문서 관련 비즈니스 워크플로우를 조율합니다.

**주요 메서드**:
- `upload_document()` - 파일 업로드 (임시 저장 → Pipeline 호출 → 정리)
- `save_chat()` - 채팅 저장
- `save_agent_result()` - 에이전트 결과 저장
- `search_documents()` - RAG 검색
- `list_documents()` - 문서 목록
- `get_document()` - 문서 상세
- `delete_document()` - 문서 삭제 (DB + Milvus)
- `chat_with_document()` - 문서 채팅

**현재**: `Pipeline`, `RAGSearcher`, `DocumentChat`으로 단순 위임  
**향후**: PII 검증, 권한 체크, 사용량 제한 등 추가 가능

### `usecases/orchestrator/service.py` - Orchestrator Facade
Orchestrator의 채팅 워크플로우를 조율합니다.

**주요 메서드**:
- `process_chat()` - 통합 채팅 처리

**현재**: `OrchestratorPipeline`으로 단순 위임  
**향후**: Hub + Drive 연동, 복잡한 멀티턴 대화 관리 가능

### `database.py`
데이터베이스 설정 및 연결 관리:
- Hub DB 설정 (`ai_hub`)
- Drive DB 설정 (`ai_drive`)
- Orchestrator DB 설정 (`orchestrator`)
- `get_db()` dependency

### `auth.py`
인증 및 권한 관련 유틸리티:
- JWT 토큰 생성/검증
- 비밀번호 해싱
- 사용자 인증 헬퍼

---

## 예시: Drive Facade

```python
class AIDriveService:
    """Drive Application Service (Facade)"""
    
    def __init__(self):
        self.pipeline = DocumentPipeline()
    
    async def upload_document(self, file, creator_id, ...):
        """
        파일 업로드 (Facade)
        
        현재: Pipeline으로 단순 위임
        향후: PII 검증, 권한 체크 등 추가 가능
        """
        # 최소한의 전처리
        temp_path = await self._save_temp_file(file)
        
        try:
            # Service Layer 호출
            return self.pipeline.process_file_upload(temp_path, ...)
        finally:
            os.remove(temp_path)
```

---

## 일관성
모든 서비스가 동일한 Facade 패턴을 따릅니다:
- Hub: `AgentService` → `AgentManager`
- Drive: `AIDriveService` → `Pipeline`, `RAGSearcher`, `DocumentChat`
- Orchestrator: `OrchestratorService` → `OrchestratorPipeline`

