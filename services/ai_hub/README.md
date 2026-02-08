# AI Hub & Agent Service

**에이전트 생성(Agent)**부터 **활용(Hub)**까지의 모든 라이프사이클을 관리하는 통합 서비스 모듈입니다.

---

## 폴더 구조 (Directory Structure)

`ai_drive` 모듈과 동일한 표준 구조를 따릅니다.

```text
ai_hub/
├── core/                (핵심 로직 / Business Logic)
│   ├── agent.py         # 에이전트 생성 마법사 (Draft -> Publish)
│   └── hub.py           # 허브 검색 및 추천 알고리즘
│
├── db/                  (데이터 관리 / Repository)
│   ├── agent_repo.py    # 에이전트 저장 (INSERT/UPDATE)
│   └── hub_repo.py      # 에이전트 조회 (SELECT)
│
└── README.md            (통합 매뉴얼)
```

---

## 기능 1: AI Agent (생성 마법사)

사용자가 자신만의 또는 팀의 에이전트를 쉽고 빠르게 만들 수 있도록 지원합니다.

### 데이터 흐름 (Data Flow: Creation)
```mermaid
graph TD
    User[사용자 채팅] -->|1. 요청 (자연어)| Hub[AgentManager]
    Hub -->|2. 의도/속성 분석| Orch[Orchestrator]
    Orch -->|3. 스키마 반환| Hub
    Hub -->|4. 초안 저장| Redis[(Redis)]
    
    User -->|5. 최종 배포| Hub
    Hub -->|6. 벡터화 (Embedding)| Milvus[(Milvus - Vector)]
    Hub -->|7. 메타데이터 저장| PG[(PostgreSQL - Meta)]
```

---

## 기능 2: AI Hub (검색 및 추천)

**핵심 알고리즘:** RAG (Retrieval-Augmented Generation) 패턴을 적용하여 정확도를 극대화했습니다.

### 검색 및 추천 로직 (Recommendation Logic)
1.  **의도 파악 (Intent Analysis):** 
    *   사용자의 질문을 Orchestrator가 분석하여 **Topic**과 **Keywords**를 추출합니다.
    *   (예: "파이썬 코드 짜줘" -> Topic: Coding, Keywords: [Python, Algorithm])

2.  **벡터 검색 (Vector Search - Milvus):** 
    *   추출된 키워드를 벡터로 변환하여, 의미적으로 가장 유사한 에이전트 ID를 찾습니다.
    *   **Status**: ✅ Real Implementation (Mock Fallback Removed).

3.  **메타데이터 조회 (Metadata Fetch - Postgres):** 
    *   찾은 ID들을 Batch Query로 DB에서 한 번에 조회하여 상세 정보를 가져옵니다.

4.  **필터링 (Filtering - Placeholder):**
    *   '내 팀', '내 부서' 필터 기능은 현재 UI상 존재하나, **실제 로직은 "전체 공개"로 동작**합니다. (Placeholder 🚧)

### 검색 흐름도 (Search Flow)
```mermaid
graph TD
    User[사용자 질문] -->|1. 추천 요청| Hub[AgentManager]
    Hub -->|2. 키워드 분석| Orch[Orchestrator]
    Orch -->|3. 분석 결과 (Json)| Hub
    
    Hub -->|4. 임베딩 생성| Embed[Embedding Model]
    Embed -->|5. 벡터 검색| Milvus[(Milvus)]
    Milvus -->|6. 유사 에이전트 ID| Hub
    
    Hub -->|7. 메타데이터 조회| PG[(PostgreSQL)]
    PG -->|8. 상세 정보 반환| Hub
    Hub -->|9. 점수순 정렬| User
```
