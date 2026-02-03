# IN7 AI 플랫폼 - 상세 구현 계획서 (Master Plan v33)

이 문서는 시스템 구현 시 오류를 방지하기 위해 데이터 흐름, 파라미터 규격, 아키텍처, 비즈니스 로직을 **요약이나 생략 없이, 빠짐없이 상세하게 기술한 최종 마스터 설계서**입니다.

**[작업 기준]**
*   **Root Folder:** `app/`
*   **Documentation:** 개발 완료 시 이 내용을 `app/README.md`로 변환하여 메인 문서로 활용.

---

## 1. 시스템 아키텍처 (System Architecture)

### 1.1 전체 구조 (4-Layer)
본 시스템은 확장성과 유지보수성을 위해 4계층 구조로 설계되었습니다.

*   **Interface Layer (`app/main.py`)**:
    *   **역할:** 사용자 요청을 수신하고, 검증(Validation) 및 인증(Auth)을 수행한 뒤 적절한 비즈니스 로직으로 라우팅하는 시스템의 관문(Gateway)입니다. 프론트엔드와 직접 통신하는 유일한 계층입니다. **[내 담당]**
    *   **책임:** Pydantic 모델을 통한 입출력 검증, JWT 기반 인증 미들웨어 처리.
*   **Orchestration Layer (`core/orchestrator.py`)**:
    *   **역할:** 사용자 의도를 분석하고 LLM 모델(Router, Researcher, Reasoner)을 제어할 뿐만 아니라, **데이터 변환의 매개체(Middleware)** 역할을 수행합니다.
    *   **Chat-to-Action Mediation:** 채팅 내용을 에이전트 생성용 프롬프트로 변환하거나, AI Drive 저장용 문서로 가공하여 각 서비스(`ai_agent`, `ai_drive`)로 넘겨주는 데이터 브로커 역할을 수행합니다.
    *   **연결:** `main.py`에서는 이 모듈의 함수를 호출하는 **'연결(Wiring)'** 작업만 수행합니다. 실제 내부의 복잡한 추론 로직은 권영민 님이 구현합니다.
*   **Service Layer (`services/`)**:
    *   `ai_agent` **(Agent Factory)**: 에이전트 생성(Draft -> Step1 -> Step2 -> Final), 관리, 공유 로직. **[내 담당]**
    *   `ai_hub`: 에이전트 검색, 공유 로직. **[내 담당]**
    *   `ai_drive`: 문서 벡터화(Embedding), RAG 검색, 지식 저장소 관리를 담당하는 모듈. **[송호성 담당]**
    *   **CRITICAL:** 내가 이 모듈의 핵심(CRUD, DB)을 담당하지만, **내부에서 '오케스트레이터'를 사용하거나 'AI Drive'를 참조해야 하는 특수 로직**은 권영민/송호성 님이 구현할 수 있도록 **인터페이스(함수 껍데기)만 연결**해 둡니다.
*   **Data Layer**:
    *   **PostgreSQL**: 사용자 정보(`users`), 에이전트 메타데이터(`agents`), 대화 로그(`chat_logs`) 저장.
    *   **Redis**: 사용자 세션 및 **에이전트 생성 중 임시 데이터(Draft)** 저장.
    *   **Milvus (Standalone):** 벡터 임베딩을 저장하고 검색(RAG)하기 위한 벡터 데이터베이스. 서버 환경에서의 안정성을 위해 Lite가 아닌 **Docker 기반 Standalone 버전**을 사용합니다. (`etcd`, `minio` 의존성 포함)

### 1.2 핵심 연결 로직 (Connection Logic)
*   **Auto Mode (기본 연결 상태):**
    *   **개념:** 사용자가 프롬프트에 입력 시, 별도 설정 없이 **기본적으로 오케스트레이션 레이어와 연결**되어 작동합니다.
    *   **동작:** 입력된 내용은 즉시 `Orchestrator`로 전달되며, 시스템 내부의 Route 로직이 최적의 모델(Gemini, GPT-4 등)을 자동으로 결정하여 답변을 생성합니다. 사용자는 모델을 고민할 필요가 없습니다.
*   **Manual Mode (모델 강제 지정):**
    *   **개념:** 사용자가 의도적으로 특정 모델(Override)을 지정하여 사용하는 모드입니다.
    *   **동작:** 인터페이스 레이어는 `model_type="gpt-4"` 인자를 전달하여, 오케스트레이터의 자동 판단 로직을 건너뛰고 지정된 모델을 직접 호출하도록 요청합니다.
*   **RAG Connection (내부 참조):**
    *   **개념:** 사내 지식(AI Drive)을 참조하여 답변할지 여부를 결정합니다.
    *   **동작:** UI 스위치 ON -> `req.use_rag = True` 설정 -> `Orchestrator` 전달 -> `AIDrive` 모듈 호출.
    *   **책임:** `main.py`는 스위치를 켜는 신호만 전달합니다. 실제 검색 로직의 연결은 오케스트레이터(권영민)와 드라이브(송호성) 간의 협업 영역입니다.

---

## 2. 사용자 경험 흐름 및 UI 로직 (Detailed User Flow)

### Step 1. 랜딩 & 인증 (Entry & Auth)
*   **화면 구성:** 중앙에 심플한 카드 형태의 로그인/회원가입 폼이 배치됩니다. 배경은 깔끔한 단색 또는 그라데이션을 사용합니다.
*   **단일 사용자 체제:** 관리자/일반 사용자 구분 없이 모든 가입자는 '사용자(Member)'로 통합 관리됩니다. 별도의 관리자 페이지가 존재하지 않습니다.
*   **회원가입 프로세스:**
    1.  사용자가 `이메일`, `비밀번호`, `이름`, `부서(HR/Dev/Sales 등)`를 입력합니다.
    2.  `POST /auth/register`를 호출하여 DB에 저장합니다. 비밀번호는 Bcrypt로 해싱됩니다.
*   **로그인 프로세스:**
    1.  사용자가 `이메일`, `비밀번호`를 입력합니다.
    2.  `POST /auth/login`을 호출합니다.
    3.  정보가 일치하면 서버는 `access_token` (JWT)을 발급합니다.
    4.  클라이언트는 토큰을 로컬 스토리지에 저장하고 메인 화면으로 이동합니다.

### Step 2. 메인 화면 (Prompt Interface)
ChatGPT나 Gemini와 유사한 대화형 인터페이스를 중심으로, 주요 기능으로 이동할 수 있는 네비게이션이 추가됩니다.

#### A. 상단 컨트롤 패널 (Top-Left Navigation & Controls)
1.  **메인 네비게이션 (Navigation Bar):**
    *   **위치:** 화면 좌측 상단. 하이퍼링크 형태의 버튼 3개가 배치됩니다.
    *   **[에이전트 허브 (Agent Hub)]**: 클릭 시 `/hub` 페이지로 이동합니다. 이곳에서 공개된 에이전트를 탐색할 수 있습니다.
    *   **[AI 드라이브 (AI Drive)]**: 클릭 시 `/drive` 페이지로 이동합니다. 이곳에서 문서를 업로드하고 관리할 수 있습니다.
    *   **[거버넌스 차트 (Governance)]**: 클릭 시 `/governance` 페이지로 이동합니다. 이곳에서 AI 사용량 통계를 확인할 수 있습니다.
2.  **모델 선택기 (Model Override):**
    *   **기본 상태:** 선택하지 않음 (화면에 "Auto" 표시). 시스템이 자동 판단합니다.
    *   **UI 동작:** 드롭다운을 열어 특정 모델(ChatGPT, Gemini 등)을 선택하면, 그 값이 상태 변수에 저장됩니다.
    *   **데이터 바인딩:** API 호출 시 `model_type` 필드에 바인딩됩니다 (기본값: "auto").
3.  **내부 참조 스위치 (RAG Toggle):**
    *   **UI 동작:** "내부 지식 참조" 라벨 옆의 토글 스위치입니다.
    *   **Logic:** ON이면 `true`, OFF면 `false`입니다.
    *   **데이터 바인딩:** API 호출 시 `use_rag` 필드에 바인딩됩니다.

#### B. 중앙 채팅 영역 (Chat Area) & [New] 액션 모드
1.  **기본 대화:** 질문(User)과 답변(AI)이 하나의 **'세트(Set)'**로 묶여서 표시됩니다.
2.  **선택 모드 (Selection Mode):**
    *   **Trigger:** 사용자가 대화 세트(말풍선)를 클릭하거나, 옆에 있는 체크박스를 누르면 '선택 모드'가 활성화됩니다.
    *   **Interaction:** 여러 개의 질문-답변 세트를 다중 선택할 수 있습니다. 선택된 대화는 시각적으로 강조(Highlight)됩니다.
3.  **액션 버튼 (Floating Action Bar):**
    *   선택 시 화면 하단 또는 입력창 위에 작업 버튼이 나타납니다.
    *   **[AI Drive 저장]:** 선택한 대화 세트를 문서 형태로 정리하여 지식 저장소에 업로드합니다.
    *   **[에이전트 생성 버튼]:** 오케스트레이터를 통해 에이전트 초안을 생성하도록 요청합니다.

#### C. 하단 맞춤형 에이전트 패널 (Dynamic Recommendation)
상황에 따라 사용자에게 가장 필요한 에이전트를 추천해 줍니다.
*   **상태 1: 입력 전 (Zero State - 로그인 직후):**
    *   **Trigger:** 페이지 로드.
    *   **Logic:** DB의 `users.memory` 컬럼 조회 (최근 사용 에이전트, 선호 토픽).
    *   **UI:** "000님, 마케팅 리포트 작업을 이어서 하시겠습니까?" 메시지와 추천 에이전트 카드 표시.
*   **상태 2: 입력 중 (Active State - 타이핑 중):**
    *   **Trigger:** 입력창 debounce(300ms).
    *   **Logic:** 실시간 텍스트를 `Orchestrator`가 분석하여 관련성 높은 에이전트 ID 반환.
    *   **UI:** 입력창 상단/하단에 실시간 카드 추천.

### Step 3. 에이전트 생성 마법사 (Agent Wizard Flow) **[New Visual Logic + Model Select]**
사용자가 제공한 다이어그램에 맞춰 **'진행중인 작업(Draft List)' 확인 후 '필수 점검(Mandatory Review)'**을 거치는 흐름을 구현합니다.

*   **1단계: 초안 생성 및 리스트 등록 (Draft Creation Logic)**
    *   **Action:** 사용자가 채팅에서 [에이전트 생성] 버튼 클릭.
    *   **Process:** 오케스트레이터가 대화 내용을 바탕으로 이름, 설명, 프롬프트, 예시를 자동으로 채워 넣은(Pre-fill) **'초안(Draft)'**을 만듭니다.
    *   **UI:** 생성된 초안은 **[진행 중인 작업 List]**에 카드로 등록됩니다. (즉시 완료되지 않음)
*   **2단계: 점검 및 수정 (Step 1 - Definition)**
    *   **Action:** 사용자가 리스트에서 특정 초안을 클릭.
    *   **User Check:** 오케스트레이터가 자동 완성한 **에이전트명, 입력 예시, 출력 예시**를 확인하고, **필수적으로 점검 및 수정**합니다.
*   **3단계: 설정 및 연결 (Step 2 - Configuration)**
    *   **Action:** Step 1에서 [다음] 버튼 클릭.
    *   **Metadata:** 카테고리(마케팅 등), 역할 설명, 공개 범위를 설정합니다.
    *   **[New] 모델 선택 (Model Selection):** 이 에이전트가 사용할 기본 모델을 지정합니다. (기본값: **Auto**, 옵션: GPT-4, Claude 3.5 Sonnet, Gemini Pro 등)
    *   **RAG Connection (핵심):**
        1.  **[내부 문서 참조]** 스위치 ON.
        2.  **[문서 리스트]** 팝업에서 `ai_drive`가 제공하는 문서 선택.
        3.  선택된 문서가 에이전트의 지식으로 **연결(Link)**됩니다.
*   **4단계: 최종 발행 (Publish)**
    *   **Action:** [저장] 버튼 클릭.
    *   **Effect:** 초안 데이터가 DB에 영구 저장되고, 리스트에서 사라집니다.

---

## 3. 인터페이스 레이어 API 명세 및 데이터 흐름 (`app/main.py`)

### 3.1 채팅 실행 (`POST /chat`)
사용자가 질문을 전송할 때 호출되는 메인 API입니다.

*   **1단계: 요청 전송 (Source -> Dest)**
    *   **출발:** 클라이언트 (실행 버튼 클릭)
    *   **도착:** `app/main.py` -> `chat_endpoint`
    *   **Payload:**
        ```json
        {
          "message": "이번 달 연차 규정 알려줘", // 질문 내용
          "model_type": "auto",               // (드롭다운) 기본값 auto
          "use_rag": true,                    // (스위치) ON 상태
          "agent_id": null,                   // (선택) 특정 에이전트 사용 시
          "context_id": "ctx-123"             // (선택) 이어지는 대화일 경우
        }
        ```
*   **2단계: 내부 처리 흐름 (Internal Flow)**
    1.  **Middleware:** `main.py`가 JWT 토큰을 확인하고 `user_id`를 추출합니다.
    2.  **Orchestration:** `core/orchestrator.py`의 `process()` 함수를 호출합니다.
    3.  **Routing/Retrieval:** 오케스트레이터는 `use_rag=true` 여부를 판단하여 `services/ai_drive`를 호출해 문서를 찾고, 질문 난이도에 따라 최적의 모델로 답변을 생성합니다.
*   **3단계: 응답 반환 (Return)**
    ```json
    {
      "response": "2026년 규정에 따르면 연차는 15일입니다.",
      "used_model": "gpt-4-turbo",  // 오케스트레이터가 선택한 모델
      "sources": ["인사규정_v2.pdf"] // 참조한 문서
    }
    ```

### 3.2 Chat-to-Action 상세 구현 로직 (**Redis Draft Flow**) [Updated]
기존의 즉시 생성 방식에서, **Redis 리스트에 등록되는 Draft 방식**으로 고도화되었습니다.

#### A. 에이전트 초안 생성 (`POST /actions/draft-agent`)
대화를 분석하여 초안을 만들고, 작업 리스트에 추가합니다.

*   **1단계: 요청 수신 (Controller)**
    *   Payload: `{ "selected_messages": [...], "user_id": "..." }`
*   **2단계: 오케스트레이터 분석 (Middleware)**
    *   `Orchestrator` 호출 -> LLM 분석 -> `{name, description, system_prompt, input_ex, output_ex}` JSON 추출.
*   **3단계: 임시 저장 (Redis List)**
    *   추출된 데이터를 **Redis**의 `draft_agents:{uuid}` 키에 저장합니다. (Model 기본값 'AUTO' 포함)
    *   동시에 해당 사용자의 `user_drafts:{user_id}` 리스트(Set)에 `uuid`를 추가합니다.
    *   **응답:** "초안이 생성되었습니다" (클라이언트는 리스트를 새로고침).

#### B. 초안 목록 조회 (`GET /agents/drafts`)
**'진행 중인 작업 List'**를 보여주기 위한 API입니다.

*   **1단계: 요청 수신**
    *   Header: `Authorization: Bearer <token>`
*   **2단계: Redis 조회**
    *   Redis의 `user_drafts:{user_id}` Set에서 모든 Draft ID를 가져옵니다.
    *   각 ID에 해당하는 `draft_agents:{id}` 상세 정보를 조회합니다.
*   **3단계: 목록 반환**
    *   `[ { "id": "...", "name": "...", "created_at": "..." }, ... ]`

#### C. 드라이브 저장 (`POST /actions/save-drive`)
대화를 '문서'로 만들어 저장하는 로직입니다.

*   **1단계: 요청 수신 (Controller)**
    *   Payload: `{ "selected_messages": [...], "user_id": "..." }`
*   **2단계: 오케스트레이터 가공 (Middleware Logic)**
    *   **문서 포맷팅:** 오케스트레이터는 선택된 메시지들을 "질문 -> 답변" 형태의 마크다운 문서로 변환합니다.
    *   **제목 생성:** LLM을 이용해 대화의 핵심 주제를 요약하여 파일명(Title)을 생성합니다.
*   **3단계: 서비스 이관 (Saving Logic)**
    *   생성된 `title`과 `content`를 담아 **`services.ai_drive.service.upload_document(title, content, user_id)`**를 호출합니다.
    *   `AIDrive` 서비스는 내부적으로 이 텍스트를 청크(Chunk)로 나누고 벡터화(Embedding)하여 Milvus와 Postgres에 저장합니다.

### 3.3 에이전트 생성 마법사 API (`/agents/draft/...`) **[Model Select Added]**
'점검 및 수정' 단계를 처리하는 API입니다.

#### A. Step 1: 정의 수정 (`POST /agents/draft/step1`)
*   **Payload:** `{ "draft_id": "...", "name": "...", "input_example": "...", "output_example": "..." }`
*   **Logic:** 사용자가 검토/수정한 내용을 Redis에 업데이트합니다.

#### B. Step 2: 설정 및 연결 (`POST /agents/draft/step2`)
이 단계에서 **AI Drive 모듈과의 연동**과 **모델 선택**이 일어납니다.

*   **Integration (문서 목록):** `GET /integrations/drive/knowledge-bases` -> `ai_drive.fetch_available_knowledge(user_id)`.
*   **Payload:**
    ```json
    {
      "draft_id": "uuid...",
      "category": "MARKETING",
      "role": "...",
      "visibility": "TEAM",
      "model_type": "GPT4",       // [New] 'AUTO', 'GPT4', 'GEMINI' ...
      "use_rag": true,
      "linked_doc_ids": ["doc-123"]
    }
    ```
*   **Logic:** 선택된 모델, 문서 ID, RAG 설정을 Redis에 업데이트합니다.

#### C. Final: 최종 발행 (`POST /agents/publish`)
*   **Payload:** `{ "draft_id": "..." }`
*   **Logic (Finalization):**
    1.  Redis에서 모든 데이터를 꺼냅니다.
    2.  **PostgreSQL (`agents`)**에 영구 저장 (RAG 정보, 모델 타입 포함).
    3.  **Milvus**에 역할 설명 벡터 저장.
    4.  Redis의 `draft_agents:{id}` 및 `user_drafts:{user_id}`에서 삭제.

### 3.4 인증 API (`POST /auth/register`, `/auth/login`)
*   **Register:** 이메일, 이름, 부서 정보를 받아 `users` 테이블에 저장합니다 (비밀번호는 해싱).
*   **Login:** 이메일/비번 확인 후 JWT Access Token을 발급합니다. Payload에는 `user_id`와 `department`가 포함됩니다.

### 3.5 서브 페이지 연결 API (Skeleton Implementation)
팀원들이 구현할 영역의 진입점(Entry Point)입니다. 우리는 연결만 보장합니다.

*   **`GET /hub/list`**: (에이전트 허브용) 에이전트 목록 조회 스텁.
*   **`GET /drive/status`**: (AI 드라이브용) 용량/파일 현황 조회 스텁.
*   **`GET /governance/stats`**: (거버넌스용) 통계 데이터 조회 스텁.

---

## 4. 데이터베이스 및 관계 구조 상세 (PostgreSQL)

관계형 데이터베이스(RDB)의 특성을 살려, **사용자 정보(Identity)**와 **활동 데이터(Activity)**를 분리하여 관리하고, Foreign Key로 연결합니다.

### A. 사용자 기본 정보 테이블 (`users`)
**[Identity & Profile]**: 사용자의 "신원"과 "개인화 설정"을 담는 메인 테이블입니다.

| 컬럼명 | 타입 | Nullable | 설명 | 예시 데이터 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | **PK (기본키)** | `550e8400...` |
| `email` | VARCHAR(100) | NO | Unique, 로그인 ID | `lee@in7.co.kr` |
| `password_hash` | VARCHAR(255) | NO | Bcrypt 암호화 | `$2b$12$...` |
| `name` | VARCHAR(50) | NO | 사용자 실명 | `이지석` |
| `department` | VARCHAR(50) | NO | 소속 부서 | `AI_Dev_Team` |
| `memory` | JSONB | YES | **개인화 데이터** | `{"recent": ["a-1"], "pref_model": "gpt-4"}` |

### B. 사용자 활동 로그 테이블 (`chat_logs`)
**[Activity History]**: 사용자가 남긴 수많은 대화 기록을 저장합니다.

| 컬럼명 | 타입 | Nullable | 설명 | 예시 데이터 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | PK | `log-9999` |
| **`user_id`** | **UUID** | NO | **FK (users.id 참조)** | `550e8400...` |
| `session_id` | VARCHAR | NO | 세션 구분 아이디 | `sess-abc` |
| `user_input` | TEXT | NO | 사용자 질문 | `연차 내고 싶어` |
| `ai_response` | TEXT | NO | AI 답변 | `신청 방법은...` |
| `created_at` | TIMESTAMP | NO | 생성 일시 | `2026-02-01...` |

### C. 에이전트 통합 테이블 (`agents`)
**[Unified Repository]**: RAG 설정 정보, 모델 선택 정보가 포함된 스키마입니다.

| 컬럼명 | 타입 | Nullable | 설명 | 예시 데이터 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | PK | `agent-1234` |
| `creator_id` | UUID | NO | FK (users.id) | `550e8400...` |
| `name` | VARCHAR(100) | NO | 에이전트 이름 | `요약 봇` |
| `description` | TEXT | NO | 설명 | `문서를 요약함` |
| `category` | VARCHAR(50) | NO | **[New] 카테고리** | `MARKETING` |
| `system_prompt` | TEXT | NO | 시스템 프롬프트 | `너는 요약 봇이야...` |
| `input_example` | TEXT | YES | **[New] 입력 예시** | `요약해줘` |
| `output_example` | TEXT | YES | **[New] 출력 예시** | `- 요약 결과:` |
| `is_public` | VARCHAR(20) | NO | **[New] 공개범위** | `TEAM` / `PRIVATE` |
| **`model_type`** | **VARCHAR(50)** | NO | **[New] 사용 모델** | `AUTO` / `GPT4` |
| **`use_rag`** | **BOOLEAN** | NO | **[New] 문서 참조 여부** | `true` |
| **`linked_knowledge_ids`** | **JSONB** | YES | **[New] 연결된 문서 ID 목록** | `["doc-77", "doc-88"]` |

### D. 데이터 저장소 역할 및 동기화 전략 (Data Storage Strategy)
**"모든 정보는 PostgreSQL에 있고, 유사도 검색이 필요한 것만 Milvus에 있다."** 이것이 핵심 원칙입니다.

1.  **PostgreSQL (Source of Truth):**
    *   **역할:** 시스템의 **모든 원본 데이터**를 저장합니다. 유저, 로그, 에이전트 설정, 그리고 **문서의 원본 텍스트**까지 모두 여기에 있습니다.
    *   **이유:** 벡터 DB는 검색은 빠르지만, 원본 데이터를 관리하고 수정하거나 관계를 맺는 데는 약합니다. 그래서 RDB가 중심을 잡아야 합니다.
2.  **Milvus (Search Engine):**
    *   **역할:** PostgreSQL에 있는 데이터 중 **'검색'이 필요한 텍스트의 벡터값(숫자 배열)**만 따로 저장합니다.
    *   **데이터:** `id` (Postgres의 PK와 동일), `vector` (임베딩 값).
3.  **동기화 (Sync):**
    *   AI Drive에 문서를 올리면 -> (1) Postgres에 `documents` 테이블에 원본 저장 -> (2) 즉시 텍스트를 임베딩해서 Milvus에 저장.
    *   **결과:** 검색은 Milvus에서 하고, 검색된 ID를 가지고 실제 내용은 Postgres에서 가져와서 사용자에게 보여줍니다.

---

## 5. 테스트 전략 (Testing Strategy)

### 5.1 테스트 범위 (Scope)
*   **Middleware Logic 검증:** 사용자의 요청이 `Auth` -> `Validation` -> `Routing` 과정을 거쳐 각 계층으로 정확히 전달되는지 확인합니다.
*   **Wizard Flow Verification:**
    *   Redis Draft List 등록 확인.
    *   Step 2에서 모델 선택(`model_type`) 저장 및 RAG 연결 확인.
    *   Publish 시 Postgres에 `model_type`이 정확히 박히는지 검증.
*   **Integration Boundary Verification:**
    *   Chat-to-Action 시 우리가 `Orchestrator`를 호출할 때 올바른 파라미터를 넘기는지 확인합니다.
    *   실제 오케스트레이터와 드라이브의 내부 로직은 Mocking 처리하여, **'연결'이 잘 되는지**에 집중합니다.

### 5.2 테스트 파일 구조 (`app/tests/`)
1.  **`test_auth.py`**:
    *   회원가입/로그인 Flow 및 에러 처리 확인.
2.  **`test_wizard.py`**:
    *   Draft 생성 후 List 조회.
    *   Step 2 업데이트 (Model Select 포함).
    *   Publish 후 DB `agents` 테이블 검증.
3.  **`test_main_routes.py`**:
    *   `/chat` 호출 시 Mock Orchestrator로의 파라미터 전달 확인.
4.  **`test_actions.py`**:
    *   `/actions/save-drive` 호출 검증.

---

## 6. 인프라 및 서버 배포 전략 (Infrastructure & Server Deployment)

안정적인 서비스 운영을 위해 **Naver Cloud Platform (NCP)** 서버와 **Docker** 컨테이너 기술을 사용하여 **Milvus Standalone** 환경을 구축합니다.

### 6.1 Docker의 역할과 필요성
*   **환경 통일 (Environment Consistency):** "내 컴퓨터에선 되는데 서버에선 안 돼요" 문제를 원천 차단합니다. OS, Python 버전, 라이브러리 설치 상태를 하나의 '이미지'로 박제하여 어디서든 똑같이 실행되게 합니다.
*   **복잡한 의존성 해결 (Dependency Management):** Milvus Standalone을 실행하려면 `etcd`(메타데이터 저장)와 `minio`(스토리지)가 필수적으로 필요한데, 이를 각각 OS에 직접 설치하는 것은 매우 어렵고 버전 충돌 위험이 큽니다. Docker Compose를 쓰면 이 3가지를 한 번에 묶어서 실행할 수 있어 관리가 매우 쉬워집니다.

### 6.2 개발(Local) vs 운영(Server) 환경 전략 (Environment Strategy)
개발을 진행하는 PC(Mac)와 실제 서버(Ubuntu)의 OS가 달라도 전혀 문제가 없습니다. **Docker가 중간에서 다리 역할(Virtualization)**을 해주기 때문입니다.

| 구분 | 개발 환경 (Local Development) | 운영 환경 (Production Server) |
| :--- | :--- | :--- |
| **OS** | **Mac OS (Apple Silicon / Intel)** | **Ubuntu 22.04 LTS (Naver Cloud)** |
| **실행 방식** | Docker Desktop | Docker Engine |
| **호환성** | `docker-compose.yml` 파일 하나로 동일하게 동작 | `docker-compose.yml` 파일 하나로 동일하게 동작 |
| **결론** | **사용자는 Mac에서 개발하고, 서버에는 Ubuntu를 설치합니다. Docker가 완벽하게 호환시켜 줍니다.** |

### 6.3 서버 환경 구성 (Naver Cloud Server)
*   **OS:** Ubuntu 22.04 LTS (NCP Standard Image).
*   **Spec:** Standard Spec (vCPU 2, RAM 8GB 이상 권장). Milvus Standalone 구동을 위해서는 최소 8GB RAM이 권장됩니다.
*   **Network:**
    *   **ACG (Access Control Group):** 인바운드 포트 설정.
        *   `22` (SSH): 관리자 IP만 허용.
        *   `80` (HTTP) / `443` (HTTPS): 전체 허용 (Any).
        *   `8000` (FastAPI App): 내부 Nginx 리버스 프록시 연결용 (외부 차단 권장).

### 6.4 배포 아키텍처 (With Docker Compose)
우리는 `docker-compose.yml` 파일 하나로 다음 컨테이너들을 통합 관리합니다.

1.  **Reverse Proxy (`nginx`):**
    *   외부 요청(80/443)을 받아 내부 애플리케이션(8000)으로 전달합니다.
2.  **App Container (`backend`):**
    *   FastAPI 애플리케이션(`app.main:app`)이 Uvicorn으로 실행됩니다.
3.  **DB Container (`postgres`):**
    *   사용자 및 에이전트 메타데이터를 저장하는 관계형 데이터베이스입니다.
4.  **Redis Container (`redis`):**
    *   사용자 세션 및 캐시를 관리합니다.
5.  **Vector DB Layer (Milvus Standalone):**
    *   `milvus-standalone`: 벡터 검색 엔진 본체.
    *   `etcd`: Milvus의 메타데이터 관리를 위한 분산 키-값 저장소.
    *   `minio`: Milvus의 벡터 데이터를 저장하기 위한 S3 호환 객체 스토리지.

**[배포 스크립트 deploy.sh 동작 방식]**
1.  `git pull`: Git 저장소에서 최신 코드를 내려받습니다.
2.  `docker-compose build`: 변경된 코드를 기반으로 새로운 Docker 이미지를 빌드합니다.
3.  `docker-compose up -d`: 컨테이너를 백그라운드 모드로 재시작합니다. 변경된 부분만 스마트하게 업데이트됩니다.

---

## 7. 구현 우선순위 (Implementation Roadmap)

1.  **Project Setup (기반 마련):**
    *   `app/` 폴더 구조 생성.
    *   `main.py` (FastAPI App) 기본 틀 작성.
    *   `requirements.txt` 작성.
    *   `Dockerfile`, `docker-compose.yml` (App + DB + Redis + Milvus Standalone) 작성.
    *   `deploy.sh` 작성.
2.  **Database Setup (데이터 저장소):**
    *   PostgreSQL 및 Milvus 연결 설정 (`database.py`).
    *   **`agents` (RAG, Model Select 컬럼 추가됨)** 및 기타 테이블 생성.
3.  **Auth System Implementation (인증):**
    *   `POST /auth/register` 및 `POST /auth/login` 구현.
    *   JWT 토큰 발급 및 검증 유틸리티 작성.
4.  **Integration Interface (AI Drive & Orchestrator):**
    *   `services/ai_drive` 스텁 및 `fetch_available_knowledge` 구현.
    *   `core/orchestrator` 초안 생성 로직 스텁 구현.
5.  **Agent Logic (Service Layer) [Core]:**
    *   `agent_service.py`에 Draft List/Step1/Step2/Publish 로직 구현.
    *   `/actions`, `/agents/draft`, `/agents/publish` 엔드포인트 구현.
6.  **Interface Logic (Main):**
    *   `POST /chat`, `/recommend` 등 메인 로직 구현.
    *   Sub-page Routes (`/hub`, `/drive`, `/governance`) 스텁 구현.
7.  **Testing & Verification (검증):**
    *   `app/tests/` 폴더에 테스트 코드 작성.
    *   각 엔드포인트별 기능 검증 수행.

---

## 8. 프로젝트 폴더 및 파일 구조 (Project Structure)

현재 구현된 파일들의 역할 설명입니다.

### 8.1 App Core (`app/`)
*   **`main.py`**: [Gateway] 서버의 시작점입니다. DB 테이블을 생성하고, API 라우터들을 하나로 묶습니다.
*   **`database.py`**: [DB Connection] PostgreSQL 데이터베이스에 접속하는 도구(Engine, Session)를 제공합니다.
*   **`models.py`**: [DB Schema] `users`, `agents`, `chat_logs` 테이블의 구조를 정의한 설계도입니다.
*   **`auth.py`**: [Security Utils] 비밀번호 암호화(Hash)와 JWT 토큰 생성/검증을 담당하는 핵심 도구함입니다.

### 8.2 API Endpoints (`app/api/`)
*   **`api/auth.py`**: [Auth API] 프론트엔드가 접속하는 로그인/회원가입 창구입니다. `auth.py`의 도구를 사용해 실제 처리를 합니다.

---

## 8. 프로젝트 폴더 및 파일 구조 (Project Structure)

**[Current Implementation Status]**

### 8.1 App Core (`app/`)
*   **`main.py`**: [Gateway] 서버의 진입점. DB 테이블 생성 및 API 라우터(Auth, Chat 등)를 통합 관리합니다.
*   **`database.py`**: [DB Connection] PostgreSQL 연결 엔진 및 세션 생성기를 제공합니다.
*   **`models.py`**: [DB Schema] `users`, `agents`, `chat_logs` 테이블의 모델 클래스를 정의했습니다.
*   **`auth.py`**: [Utils] 비밀번호 암호화(Bcrypt) 및 JWT 토큰 생성/검증 로직을 담고 있습니다.

### 8.2 API Endpoints (`app/api/`)
*   **`api/auth.py`**: [Auth API] 로그인(`/login`) 및 회원가입(`/register`)을 처리하는 실제 엔드포인트입니다.

### 8.3 Interface Layer (`app/api/` & `app/core/`)
*   **`core/orchestrator.py`**: [Orchestrator Stub] 권영민 님의 로직과 연결되는 인터페이스입니다. 현재는 테스트용 가짜 응답을 반환합니다.
*   **`api/chat.py`**: [Chat API] 채팅 메시지를 받아 오케스트레이터에게 전달하고, 결과를 DB에 저장하는 중계자 역할을 합니다.

### 8.5 [Critical] Naming Convention & Role Separation
**팀원분들은 필독해주세요! (파일명 충돌 주의)**

루트 폴더(`/`)에 있는 `core` 및 `services` 폴더와 이름이 유사하지만 역할이 완전히 다릅니다.

| 내 파일 (`app/...`) | 역할 (Web/DB) | 팀원 파일 (`root/...`) | 역할 (AI Logic) |
| :--- | :--- | :--- | :--- |
| **`app/core/orchestrator.py`** | **[인터페이스]** 팀원 코드를 호출하기 위한 '껍데기' 클래스. 실제 로직 없음. | **`core/pipeline.py`** (예상) | **[구현체]** 권영민 님이 작성할 실제 LLM 추론 및 오케스트레이션 로직. |
| **`app/services/ai_agent/service.py`** | **[저장소 관리]** 에이전트 생성/수정/삭제 및 DB 저장을 담당. (CRUD) | **`services/ai_agent/pipeline.py`** | **[실행 엔진]** 저장된 설정을 불러와 실제 에이전트를 구동하는 로직. |

**결론:** `app/` 내부의 파일은 웹 서버와 DB를 위한 코드이므로, 팀원분들의 AI 로직은 `app/` 바깥의 원래 폴더에 작성해주시기 바랍니다.

### 8.6 Hub & Drive Services (`app/services/` & `app/api/`)
*   **`services/ai_hub/service.py`**: [Agent Hub Logic] 공개된 에이전트(`is_public=TEAM`)를 검색하고 인기순/최신순으로 정렬하는 기능을 제공합니다.
*   **`api/hub.py`**: [Hub API] 프론트엔드에서 에이전트 목록을 조회할 때 사용하는 엔드포인트입니다.
*   **`services/ai_drive/service.py`**: [Drive Interface] 송호성 님의 문해서 벡터화 모듈과 연결되는 접점입니다. (현재는 껍데기만 존재)
*   **`api/drive.py`**: [Drive API] 문서 업로드 및 상태 확인을 위한 엔드포인트입니다.

### 8.7 Integration Router (`app/api/integrations.py`)
*   **`api/integrations.py`**: [Unified Router] Hub와 Drive의 기능을 한 곳에서 모아 제공하는 라우터입니다. (`/hub/list`, `/drive/knowledge-bases`)

### 8.8 Verification Tools (`app/`)
*   **`verify_system.py`**: [System Checking] 서버가 정상적으로 켜져 있는지 확인하고, 회원가입부터 에이전트 생성까지 핵심 기능을 자동으로 테스트하는 스크립트입니다.
