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

사용자가 자신만의 에이전트를 쉽고 빠르게 만들 수 있도록 지원합니다.

### 데이터 흐름 (Data Flow)
```mermaid
graph TD
    User[사용자 UI] -->|1. 의도 입력| Draft[Redis 임시 저장 (Draft)]
    Draft -->|2. 지식 연결| Docs[AI Drive (문서)]
    Draft -->|3. 최종 확인| Logic[Core Logic (agent.py)]
    Logic -->|4. 저장 요청| Repo[Repository (agent_repo.py)]
    Repo -->|5. DB 반영| DB[(PostgreSQL)]
```

---

## 기능 2: AI Hub (허브 및 검색)

만들어진 에이전트를 검색하고 필터링합니다.

### 검색 및 추천 로직
1.  **기본 보기 (Open Hub):**
    *   기본적으로 **모든 공개 에이전트**를 보여줍니다.
    *   *필터링:* 사용자가 원할 경우 '내 팀', '내 부서' 버튼을 눌러 목록을 좁힐 수 있습니다.

2.  **하이브리드 검색 (Hybrid Search):**
    *   **현재 구현:** 키워드 매칭 (이름 또는 설명에 포함된 단어 검색).
    *   *향후 계획:* 벡터 유사도 검색(Milvus) 추가 예정.
