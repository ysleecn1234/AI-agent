# 🎼 Orchestrator Service

시스템의 **"지능형 중앙 제어 장치(Brain)"** 역할을 담당하는 모듈입니다.
단순한 라우팅을 넘어, 사용자의 모호한 요청을 분석하여 구체적인 실행 명령(JSON)으로 변환합니다.

---

## 📂 구조 (Structure)

```text
services/orchestrator/
├── pipeline.py         # 핵심 로직 (Intent Analysis, Generation)
├── prompts.py          # LLM 프롬프트 템플릿 관리
├── __init__.py         # 패키지 선언
└── README.md           # 설명서 (현재 파일)
```

## 🧠 핵심 기능 (Core Logic)

### 1. `analyze_for_draft(user_msg)`
*   **역할**: 사용자의 자연어 요청을 분석하여 **에이전트 생성용 JSON 스키마**를 완성합니다.
*   **현재 상태**: 🚧 **Simple Rule-Based (지능형 LLM 미연동 - Mock)**
    *   간단한 키워드 매칭으로 템플릿을 채웁니다. (향후 LLM 연동 예정)
*   **예시**:
    *   입력: "파이썬 코드 리뷰해주는 봇 만들어줘"
    *   출력: `{"name": "Code Reviewer", "description": "파이썬 코드의 품질을...", "system_prompt": "..."}`

### 2. `recommend_agents(user_msg)`
*   **역할**: 사용자의 질문에서 **검색 키워드(Topic, Keywords)**를 추출합니다.
*   **현재 상태**: 🚧 **Simple Logic (단순 키워드 추출)**
    *   복잡한 의도 파악보다는 명시적 키워드 추출에 집중합니다.
*   **예시**:
    *   입력: "여행 계획 짜고 싶어"
    *   출력: `{"topic": "TRAVEL", "keywords": ["plan", "trip", "schedule"]}`

### 3. `router(user_msg)` (Planned)
*   **역할**: 사용자 의도를 분류하여 적절한 서비스(Hub, Drive, Chat)로 연결합니다.
*   **현재 상태**: 🗓️ **TBD (개발 예정)**

---

## 🔗 아키텍처 다이어그램 (Interaction Map)

```mermaid
graph TD
    User[사용자 요청] -->|1. 분석 요청| Orch[Orchestrator]
    
    Orchestrator -->|2. 분석 (LLM)| LLM[GPT-4o / Gemini]
    LLM -->|3. 결과 반환| Orch
    
    Orchestrator -->|4. JSON 응답| Service
    
    subgraph Service [Client Services]
        Hub[AI Hub (Agent)]
        Drive[AI Drive (Docs)]
    end
```

---

## 🔌 외부 의존성 (Dependencies)
이 모듈은 다른 서비스에 의존하지 않으며, 오직 **LLM (OpenAI, Gemini)**과 통신하여 순수 로직만 수행합니다. (Stateless)
