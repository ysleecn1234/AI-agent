# Orchestrator - Agent 생성 및 추천 기능

**작성일:** 2026-02-05  
**작성자:** Kwon (feature-Y)  
**커밋:** e201a37

---

## 📋 개요

Orchestrator에 두 가지 핵심 Agent 관련 기능이 추가되었습니다:
1. **Agent 생성 템플릿 자동 채우기** - 대화 분석 기반
2. **실시간 Agent 추천** - 주제/카테고리/키워드 추출

---

## 🎯 기능 1: Agent 생성 템플릿 (Pull-Fill)

### 메서드
```python
async def analyze_for_draft(messages: List[Dict]) -> Dict
```

### 역할
대화 내용을 분석하여 Agent 생성에 필요한 정보를 자동으로 추출합니다.

### Flow
```
1. Pull: Agent Hub에서 표준 템플릿 가져오기
   ↓
2. Fill: Pipeline으로 대화 분석 및 템플릿 채우기
   ↓
3. Return: 채워진 Draft 반환
   ↓
4. Service Layer가 Redis에 저장 (Push)
```

### 입력
```python
messages = [
    {"role": "user", "content": "마케팅 전략 짜줘"},
    {"role": "assistant", "content": "어떤 제품인가요?"},
    {"role": "user", "content": "신제품 런칭 전략"}
]
```

### 출력
```python
{
    "name": "마케팅 전략 전문가",
    "description": "신제품 런칭을 위한 마케팅 전략 수립 전문가",
    "system_prompt": "당신은 마케팅 전략 전문가입니다. 신제품 런칭...",
    "input_example": "신제품 런칭 전략 짜줘",
    "output_example": "다음과 같은 3단계 전략을 추천합니다...",
    "category": "MARKETING",
    "model_type": "AUTO",
    "use_rag": "False"
}
```

### 사용 예시
```python
# Service Layer에서 호출
from app.core.orchestrator import orchestrator

draft_data = await orchestrator.analyze_for_draft(messages)
# Redis에 저장
redis_client.hset(f"draft_agent:{draft_id}", mapping=draft_data)
```

---

## 🎯 기능 2: 실시간 Agent 추천

### 메서드
```python
async def recommend_agents(
    current_message: str, 
    conversation_history: List[Dict] = None
) -> Dict
```

### 역할
현재 대화 내용을 분석하여 관련 Agent를 추천하기 위한 정보를 추출합니다.

### Flow
```
1. 대화 컨텍스트 구성 (최근 5개 메시지)
   ↓
2. Pipeline으로 주제/카테고리/키워드 분석
   ↓
3. 분석 결과 반환
   ↓
4. Service Layer가 DB에서 관련 Agent 검색
```

### 입력
```python
current_message = "이번 달 마케팅 캠페인 기획해줘"
conversation_history = [
    {"role": "user", "content": "안녕"},
    {"role": "assistant", "content": "무엇을 도와드릴까요?"}
]
```

### 출력
```python
{
    "topic": "마케팅 캠페인 기획",
    "category": "MARKETING",
    "keywords": ["마케팅", "캠페인", "기획"]
}
```

### 사용 예시
```python
# API Layer에서 호출
analysis = await orchestrator.recommend_agents(
    current_message=req.message,
    conversation_history=req.history
)

# Hub Service로 Agent 검색
agents = hub_service.recommend_agents_by_analysis(
    db=db,
    analysis=analysis,
    top_k=3
)
```

---

## 🔧 내부 구현

### 헬퍼 메서드

#### `_get_agent_template() -> Dict`
표준 Agent 템플릿 정의를 반환합니다.

**템플릿 구조:**
```python
{
    "name": "",
    "description": "",
    "category": "GENERAL",
    "system_prompt": "",
    "input_example": "",
    "output_example": "",
    "model_type": "AUTO",
    "use_rag": "False"
}
```

#### `_analyze_conversation(messages, template) -> Dict`
대화 내용을 분석하여 템플릿을 채웁니다.

**프로세스:**
1. 대화 내용 결합
2. JSON 형식 프롬프트 생성
3. Pipeline 실행
4. JSON 파싱 (정규식 사용)
5. 파싱 실패 시 폴백

#### `_extract_simple_keywords(text) -> List[str]`
파싱 실패 시 사용하는 간단한 키워드 추출 로직입니다.

---

## 📊 역할 분담

### Orchestrator (이 구현)
- ✅ 대화 분석 (AI 로직)
- ✅ 템플릿 정의
- ✅ JSON 파싱 및 에러 처리

### Service Layer (팀원 구현)
- ⏳ Redis 저장/로드
- ⏳ DB 검색
- ⏳ Agent 추천 로직 (키워드 매칭)

### API Layer (팀원 구현)
- ⏳ `/agents/draft` - Agent 생성 엔드포인트
- ⏳ `/chat/recommend-agents` - Agent 추천 엔드포인트 (예정)

---

## 🚀 다음 단계

### 팀원 작업 필요
1. **Agent 추천 API 엔드포인트 추가**
   ```python
   # app/api/chat.py
   @router.post("/recommend-agents")
   async def recommend_agents(req: RecommendRequest, db: Session = Depends(get_db)):
       analysis = await orchestrator.recommend_agents(req.message, req.history)
       agents = hub_service.recommend_agents_by_analysis(db, analysis, top_k=3)
       return agents
   ```

2. **Hub Service 추천 로직 구현**
   ```python
   # app/services/ai_hub/service.py
   def recommend_agents_by_analysis(self, db, analysis, top_k=3):
       category = analysis.get("category")
       keywords = analysis.get("keywords", [])
       # DB 검색 및 유사도 계산
       # Top K 반환
   ```

### 통합 테스트
- [ ] Agent 생성 Flow 테스트
- [ ] Agent 추천 Flow 테스트
- [ ] Service Layer 연동 확인

---

## 📝 참고 문서

- **팀원 설계 문서:** `app/README.md` (Line 155-200)
- **Service Layer 구현:** `app/services/ai_agent/service.py`
- **Hub Service:** `app/services/ai_hub/service.py`
- **통합 문서:** `docs/integration_walkthrough.md`

---

## ⚠️ 주의사항

1. **Service Layer 수정 금지**
   - Orchestrator는 분석만 담당
   - Redis/DB 작업은 Service Layer에서 처리

2. **JSON 파싱 에러 처리**
   - LLM 응답이 항상 완벽한 JSON이 아닐 수 있음
   - 폴백 로직으로 기본값 반환

3. **템플릿 필드 확장**
   - 새 필드 추가 시 `_get_agent_template()` 업데이트 필요
   - Service Layer와 협의 필요

---

## 📞 문의

구현 관련 문의: Kwon (feature-Y 브랜치)
