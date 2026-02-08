# Orchestrator 로직 흐름도

**작성일:** 2026-02-08  
**작성자:** Kwon (feature-Y)

---

## 🎯 개요

Orchestrator는 AI-agent 시스템의 두뇌 역할을 하며, 3가지 주요 Flow를 관리합니다:
1. **User Request Processing** - 사용자 요청 처리
2. **Agent Recommendation** - 실시간 Agent 추천
3. **Agent Creation** - 대화 기반 Agent 생성

---

## 📊 전체 시스템 아키텍처

![Orchestrator Flow Diagram](orchestrator_flow_diagram.webp)

---

## 🔄 Flow 1: User Request Processing (사용자 요청 처리)

### 흐름도

```
사용자 요청
    ↓
┌─────────────────────────────────────────────┐
│  Orchestrator.process()                     │
│  - user_input, user_id, use_rag            │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Pipeline (5-Layer Architecture)            │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Layer 1: Router                            │
│  Model: Gemini 2.0 Flash                    │
│  Role: 의도 분류 (QUERY/SEARCH/ANALYSIS)    │
│  Speed: TTFT 0.2s                           │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Layer 2: Researcher (RAG)                  │
│  Model: Gemini Pro                          │
│  Role: 문서 검색 (멀티모달, 대용량)         │
│  Context: 2M tokens                         │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Layer 3: Reasoner                          │
│  Model: GPT-5.2 (COMPLEX)                   │
│  Role: 답변 생성 (MMLU 최상위)              │
│  Fallback: GPT-5.2-mini → Claude 4.5        │
│           → DeepSeek-R1 → Llama 4           │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Layer 4: Synthesizer                       │
│  Model: Claude 4.5                          │
│  Role: 답변 정리 (일관성, JSON 스키마)      │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Layer 5: Guardrail                         │
│  Model: Llama 4 (로컬)                      │
│  Role: 안전성 검수 (개인정보 필터링)        │
│  Cost: 무료 (로컬 실행)                     │
└─────────────────────────────────────────────┘
    ↓
최종 응답 반환
{
  "response": "...",
  "used_model": "gpt-5.2",
  "sources": ["doc1.pdf", "doc2.pdf"]
}
```

### 복잡도별 모델 선택

| 복잡도 | 주 모델 | Fallback 체인 |
|--------|---------|---------------|
| **SIMPLE** | Gemini 2.0 Flash | GPT-4o-mini → Claude 4.5 → DeepSeek Chat |
| **COMPLEX** | GPT-5.2 | GPT-5.2-mini → Claude 4.5 → DeepSeek-R1 → Llama 4 |
| **BULK** | Gemini Pro | GPT-5.2 → Claude 4.5 → Llama 4 |

---

## 🔍 Flow 2: Agent Recommendation (실시간 추천)

### 흐름도

```
사용자 입력 중 (타이핑)
    ↓
┌─────────────────────────────────────────────┐
│  Orchestrator.recommend_agents()            │
│  - current_message                          │
│  - conversation_history (최근 5개)          │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  대화 컨텍스트 구성                         │
│  context + current_message                  │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  LLM Prompting (Pipeline)                   │
│  "다음 대화의 주제와 의도를 분석해주세요"   │
│  → JSON 형식 요청                           │
│    {topic, category, keywords}              │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Pipeline.process()                         │
│  Router → Reasoner → Synthesizer            │
│  (Claude 4.5가 JSON 생성)                   │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  JSON 파싱                                  │
│  정규식으로 JSON 추출                       │
│  Fallback: _extract_simple_keywords()       │
└─────────────────────────────────────────────┘
    ↓
반환 결과
{
  "topic": "마케팅 전략 수립",
  "category": "MARKETING",
  "keywords": ["마케팅", "전략", "분석"]
}
    ↓
┌─────────────────────────────────────────────┐
│  Agent Hub 검색 (Service Layer)             │
│  category + keywords로 관련 Agent 검색      │
└─────────────────────────────────────────────┘
    ↓
UI에 Agent 카드 2-3개 표시
```

### 구현 위치
- **메서드:** `app/core/orchestrator.py:68-144`
- **LLM 연동:** Pipeline 사용
- **Fallback:** 키워드 추출 (빈도수 기반)

---

## 🛠️ Flow 3: Agent Creation (Agent 생성)

### 흐름도 (Pull-Fill-Push 패턴)

```
사용자 [에이전트 생성] 버튼 클릭
    ↓
┌─────────────────────────────────────────────┐
│  Orchestrator.analyze_for_draft()           │
│  - messages: List[Dict]                     │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  PULL: Agent Hub에서 템플릿 가져오기        │
│  _get_agent_template()                      │
│  → 빈 템플릿 반환                           │
│    {name, description, system_prompt, ...}  │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  FILL: 대화 분석으로 템플릿 채우기          │
│  _analyze_conversation(messages, template)  │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  대화 내용 결합                             │
│  "user: 안녕\nassistant: 네\n..."          │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  LLM Prompting (Pipeline)                   │
│  "다음 대화를 분석하여 Agent 정보 추출"     │
│  → JSON 형식 요청                           │
│    {name, description, system_prompt,       │
│     input_example, output_example, category}│
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Pipeline.process()                         │
│  Router → Reasoner → Synthesizer            │
│  (Claude 4.5가 정확한 JSON 생성)            │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  JSON 파싱                                  │
│  정규식으로 JSON 추출                       │
│  템플릿 필드만 필터링                       │
│  Fallback: 기본값 반환                      │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  템플릿 + 분석 결과 병합                    │
│  draft_data = {**template, **filled_data}   │
└─────────────────────────────────────────────┘
    ↓
반환 결과 (Draft)
{
  "name": "마케팅 전략 에이전트",
  "description": "마케팅 전략 수립을 도와주는 AI",
  "system_prompt": "당신은 마케팅 전문가입니다...",
  "category": "MARKETING",
  ...
}
    ↓
┌─────────────────────────────────────────────┐
│  PUSH: Redis에 Draft 저장 (Service Layer)  │
│  draft_id = uuid4()                         │
│  redis.hset(f"draft:{draft_id}", draft_data)│
│  redis.expire(key, 1 hour)                  │
└─────────────────────────────────────────────┘
    ↓
사용자에게 Draft 편집 UI 표시
```

### 구현 위치
- **메서드:** `app/core/orchestrator.py:147-250`
- **LLM 연동:** Pipeline 사용
- **Fallback:** 기본값 반환 (파싱 실패 시)

---

## 🧩 주요 컴포넌트

### 1. Orchestrator (두뇌)

```python
class Orchestrator:
    def __init__(self):
        self.pipeline_with_rag = None
        self.pipeline_without_rag = Pipeline(use_rag=False)
    
    # Flow 1: 사용자 요청 처리
    async def process(self, user_input, user_id, use_rag=False) -> Dict
    
    # Flow 2: Agent 추천
    async def recommend_agents(self, current_message, history) -> Dict
    
    # Flow 3: Agent 생성
    async def analyze_for_draft(self, messages) -> Dict
```

### 2. Pipeline (5-Layer)

```python
class Pipeline:
    def __init__(self, use_rag=False):
        self.router = Router()           # Gemini 2.0 Flash
        self.researcher = Researcher()   # Gemini Pro
        self.reasoner = Reasoner()       # GPT-5.2
        self.synthesizer = Synthesizer() # Claude 4.5
        self.guardrail = Guardrail()     # Llama 4
    
    def process(self, user_input, user_id) -> Dict
```

### 3. 모델 역할 매핑 (기획서 기준)

| 모델 | 역할 | 선정 사유 |
|------|------|----------|
| **Gemini 2.0 Flash** | Router | 속도 (TTFT 0.2s) |
| **Gemini Pro** | Researcher | 대용량 컨텍스트, 멀티모달 |
| **GPT-5.2** | Reasoner | 지능 (MMLU 최상위) |
| **Claude 4.5** | Synthesizer | 일관성, JSON 스키마 |
| **DeepSeek-R1** | Verification | CoT 팩트체크 |
| **Llama 4** | Guardrail | 보안, 로컬 파싱 |

---

## 🔐 데이터 흐름

### User Request Processing
```
User Input
  → Orchestrator
    → Pipeline
      → Router (의도 분류)
        → Researcher (문서 검색)
          → Reasoner (답변 생성)
            → Synthesizer (포맷팅)
              → Guardrail (검수)
  → Final Response
```

### Agent Recommendation
```
Current Message + History
  → Orchestrator.recommend_agents()
    → Pipeline (주제 분석)
      → JSON {topic, category, keywords}
        → Agent Hub (검색)
  → Recommended Agents
```

### Agent Creation
```
Conversation Messages
  → Orchestrator.analyze_for_draft()
    → PULL Template
      → FILL via Pipeline
        → JSON {name, description, ...}
          → PUSH to Redis
  → Draft ID
```

---

## ✅ 구현 완료 상태

| 기능 | 상태 | LLM 연동 | 비고 |
|------|------|----------|------|
| **User Request Processing** | ✅ 완료 | ✅ Pipeline | Router, Reasoner 연동 완료 |
| **Agent Recommendation** | ✅ 완료 | ✅ Pipeline | JSON 파싱 + Fallback |
| **Agent Creation** | ✅ 완료 | ✅ Pipeline | Pull-Fill 패턴 구현 |
| **Researcher** | ⏳ 미구현 | ❌ Mock | RAG 검색 예정 |
| **Synthesizer** | ⏳ 미구현 | ❌ Mock | 포맷팅 예정 |
| **Guardrail** | ⏳ 미구현 | ❌ Mock | 안전성 검수 예정 |

---

## 📝 참고 문서

- **API 통합 가이드:** `docs/llm_api_integration.md`
- **구현 계획:** `implementation_plan.md`
- **브랜치 비교:** `branch_comparison.md`
- **검증 보고서:** `orchestrator_verification.md`
