# Application Layer (Tier 2) Documentation

**`application/`** 디렉토리는 3-Tier 아키텍처의 **2단계 (Application Core Layer)**입니다.

이 계층의 핵심 역할은 **"비즈니스 흐름의 조율(Orchestration)"**과 **"공통 인프라 관리"**입니다.
Tier 1(API)에서 받은 요청을 해석하여, Tier 3(Domain Services)의 도구들을 조합해 원하는 결과를 만들어냅니다.

---

##  디렉토리 구조 및 역할

### 1. `usecases/` (서비스 활용 사례)
**Role:** 실제 비즈니스 시나리오(Use Case)를 구현하는 **Wrapper Service**. Tier 3의 도구들을 조립하는 **작업대**입니다.

#### 1-1. `orchestrator/service.py` (채팅 로직)
*   **Role:** 채팅 요청의 흐름 제어 및 파이프라인 호출.
*   **Key Features:**
    *   **Core 호출:** `services/orchestrator`의 `Pipeline` 엔진을 호출하여 실제 작업을 위임.
    *   **대화 이력 저장(Chat History Save):** 대화 내용 및 답변을 DB(ChatLog)에 저장.
*   **Flow:**
    > User Input → `OrchestratorWrapper` → **Pipeline Engine (Tier 3)** → Result

#### 1-2. `ai_hub/service.py` (에이전트 관리)
*   **Role:** 에이전트 등록, 검색, 관리를 위한 퍼사드(Facade).
*   **Key Features:**
    *   **DTO 변환:** API 계층의 요청 데이터(Pydantic)를 내부 도메인 객체로 변환.
    *   **레포지토리 연결:** `services/ai_hub`의 DB 로직(Repository) 연결.
*   **Flow:**
    > "에이전트 찾기" 요청 → `HubWrapper` → **HubManager (Tier 3)** → DB Query

#### 1-3. `ai_agent/service.py` (제작 마법사)
*   **Role:** 에이전트 생성 마법사(Wizard)의 단계별 상태 관리.
*   **Key Features:**
    *   **임시 저장:** 제작 중인 에이전트 데이터를 Redis(Tier 3)에 임시 저장.
    *   **배포(Publish):** 완료된 에이전트를 최종 DB(Postgres)로 이관.
*   **Flow:**
    > "Step 1 저장" → `AgentService` → **Redis Client (Tier 3)** → Cache Update

### 2. `database.py` (데이터베이스 인프라)
*   **Role:** DB 연결 설정(Session) 및 핵심 모델 정의.
*   **Key Features:**
    *   `get_db()`: API 요청마다 DB 세션을 생성하고 닫는 의존성 주입(Dependency Injection) 함수.
    *   `User`: 시스템 전반에서 사용되는 사용자 계정 모델 정의.

### 3. `auth.py` (권한 관리 유틸)
*   **Role:** 보안 관련 공통 로직.
*   **Key Features:**
    *   JWT 토큰 생성 및 검증 (`create_access_token`, `decode_access_token`).
    *   비밀번호 해싱 (`verify_password`).

---

##  계층 간 관계 (Flow)

**Tier 1 (API)** → **Tier 2 (Application)** → **Tier 3 (Services)**

1.  **API**: "채팅 메시지 왔어, 처리해줘." (`application` 호출)
2.  **Application**: "오케이, 먼저 유저 권한 확인하고(`auth.py`), 오케스트레이터 파이프라인 돌려(`usecases/orchestrator`)"
3.  **Services**: "DB에서 에이전트 정보 가져오고(`ai_hub`), LLM 호출해서 답변 생성해(`ai_drive`)."

---

##  개발 가이드
*   **비즈니스 로직 작성 시**: 단순 CRUD는 `usecases`에 바로 작성해도 되지만, 복잡한 도메인 규칙은 반드시 **Tier 3 (`services/`)**로 위임하세요.
*   **테이블(Table) 정의 시**:
    *   **서비스 전용 테이블**: 해당 서비스의 `db/tables.py`에 작성 (`services/ai_hub/db/tables.py`).
    *   **전역 공통 테이블**: `application/database.py` (User 등)에 작성.

---

## 상세 디렉토리 구조

```
application/
├── auth.py                     # [Core] 인증/보안 유틸리티
├── database.py                 # [Core] DB 세션/엔진 설정 & User 테이블
└── usecases/                   # [Wrapper] 서비스 오케스트레이션
    ├── orchestrator/           # 채팅/RAG 파이프라인 제어
    │   └── service.py
    ├── ai_hub/                 # 에이전트 검색/관리
    │   └── service.py
    └── ai_agent/               # 에이전트 생성 마법사
        └── service.py
```
