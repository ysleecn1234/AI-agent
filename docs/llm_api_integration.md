# LLM API 통합 가이드

**작성일:** 2026-02-08  
**작성자:** Kwon (feature-Y)  
**커밋:** ddcdbcf

---

## 📋 개요

이 문서는 AI-agent 프로젝트에서 LLM API를 어디서 어떻게 사용하는지 설명합니다.

---

## 🔑 필요한 API 키

### 1. Google API (Gemini)
- **용도:** Router (의도 분류), Guardrail (검수)
- **모델:** `gemini-2.0-flash-exp`
- **환경변수:** `GOOGLE_API_KEY`

### 2. OpenAI API
- **용도:** Reasoner (답변 생성), Embedding (벡터화)
- **모델:** `gpt-4o-mini`, `text-embedding-3-small`
- **환경변수:** `OPENAI_API_KEY`

### 3. Anthropic API (Optional)
- **용도:** Fallback 모델
- **모델:** `claude-3-5-sonnet-20241022`
- **환경변수:** `ANTHROPIC_API_KEY`

### 4. Deepseek API (Optional)
- **용도:** Fallback 모델
- **모델:** `deepseek-chat`
- **환경변수:** `DEEPSEEK_API_KEY`

---

## 📂 API 사용 위치

### 1. **Router (의도 분류)**

**파일:** `core/pipeline.py`  
**클래스:** `Router`  
**메서드:** `classify_intent_with_llm()`  
**라인:** 122-173

**사용 모델:**
- Primary: `gemini/gemini-2.0-flash-exp`

**코드 위치:**
```python
# core/pipeline.py:122
def classify_intent_with_llm(self, user_input: str) -> IntentType:
    import litellm
    
    response = litellm.completion(
        model=self.model,  # "gemini/gemini-2.0-flash-exp"
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=10
    )
```

**API 키 요구사항:**
- `GOOGLE_API_KEY` (필수)

**Fallback:**
- API 실패 시 키워드 기반 분류로 폴백

---

### 2. **Reasoner (답변 생성)**

**파일:** `core/pipeline.py`  
**클래스:** `Reasoner`  
**메서드:** `generate_response_with_fallback()`  
**라인:** 518-560

**사용 모델:**
- Primary: `gpt-4o-mini`
- Fallback 1: `claude-3-5-sonnet-20241022`
- Fallback 2: `deepseek-chat`
- Fallback 3: `gemini-2.0-flash`

**코드 위치:**
```python
# core/pipeline.py:518
def generate_response_with_fallback(self, context: Dict[str, Any]) -> tuple[str, str]:
    import litellm
    
    models_to_try = self.fallback_models.get(complexity, ["gpt-4o-mini"])
    
    for model in models_to_try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
```

**API 키 요구사항:**
- `OPENAI_API_KEY` (필수)
- `ANTHROPIC_API_KEY` (선택, Fallback용)
- `DEEPSEEK_API_KEY` (선택, Fallback용)
- `GOOGLE_API_KEY` (선택, Fallback용)

**Fallback 체인:**
1. GPT-4o-mini 시도
2. 실패 시 Claude 3.5 Sonnet 시도
3. 실패 시 Deepseek Chat 시도
4. 실패 시 Gemini Flash 시도
5. 모두 실패 시 Exception 발생

---

### 3. **Researcher (RAG 검색)** - 미구현

**파일:** `core/pipeline.py`  
**클래스:** `Researcher`  
**메서드:** `search_documents()`  
**라인:** 300-400

**현재 상태:** Mock (구현 예정)

**예정 모델:**
- Embedding: `text-embedding-3-small` (OpenAI)

---

### 4. **Synthesizer (답변 정리)** - 미구현

**파일:** `core/pipeline.py`  
**클래스:** `Synthesizer`  
**메서드:** `format_response()`  
**라인:** 600-700

**현재 상태:** Mock (구현 예정)

**예정 모델:**
- `gemini-2.0-flash-exp` (Google)

---

### 5. **Guardrail (검수)** - 미구현

**파일:** `core/pipeline.py`  
**클래스:** `Guardrail`  
**메서드:** `check_safety()`, `verify_quality()`  
**라인:** 700-800

**현재 상태:** Mock (구현 예정)

**예정 모델:**
- `gemini-2.0-flash-exp` (Google)

---

### 6. **Agent 생성 (Orchestrator)**

**파일:** `app/core/orchestrator.py`  
**클래스:** `Orchestrator`  
**메서드:** `analyze_for_draft()`, `_analyze_conversation()`  
**라인:** 147-250

**사용 모델:**
- Pipeline 내부 모델 사용 (간접 호출)

**코드 위치:**
```python
# app/core/orchestrator.py:220
async def _analyze_conversation(self, messages: List[Dict], template: Dict) -> Dict:
    # Pipeline으로 분석
    result = self.pipeline_without_rag.process(user_input=prompt, user_id=None)
```

**API 키 요구사항:**
- Pipeline이 사용하는 모든 API 키 필요

---

## ⚙️ 환경 설정

### 1. `.env` 파일 생성

프로젝트 루트에 `.env` 파일을 만들고 API 키를 설정하세요:

```bash
# .env 파일
# ==================== LLM API KEYS ====================
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...
```

### 2. `.env.template` 참고

`.env.template` 파일을 복사하여 사용할 수 있습니다:

```bash
cp .env.template .env
# 그 다음 .env 파일을 열어서 API 키 입력
```

### 3. 환경변수 로드

코드에서 자동으로 로드됩니다:

```python
# core/pipeline.py:22
from dotenv import load_dotenv
load_dotenv()
```

---

## 🧪 테스트 방법

### 1. API 키 설정 확인

```bash
# .env 파일이 있는지 확인
ls .env

# API 키가 설정되었는지 확인 (PowerShell)
$env:GOOGLE_API_KEY
$env:OPENAI_API_KEY
```

### 2. 테스트 실행

```bash
# LLM 통합 테스트
python tests/test_llm_integration.py
```

### 3. 개별 컴포넌트 테스트

```python
# Router 테스트
from core.pipeline import Router
router = Router()
intent = router.classify_intent("마케팅 전략 찾아줘")
print(intent)  # IntentType.SEARCH

# Reasoner 테스트
from core.pipeline import Reasoner
reasoner = Reasoner()
context = {
    "complexity": "simple",
    "user_input": "AI가 뭐야?",
    "retrieved_documents": []
}
response, model = reasoner.generate_response(context)
print(response)
```

---

## 💰 비용 관리

### 1. 모델별 비용

| 모델 | 용도 | Input (1M tokens) | Output (1M tokens) |
|------|------|-------------------|-------------------|
| `gemini-2.0-flash-exp` | Router, Guardrail | 무료 (현재) | 무료 (현재) |
| `gpt-4o-mini` | Reasoner | $0.15 | $0.60 |
| `text-embedding-3-small` | Embedding | $0.02 | - |
| `claude-3-5-sonnet` | Fallback | $3.00 | $15.00 |

### 2. 비용 추적

비용 계산기가 자동으로 추적합니다:

```python
# core/cost_calculator.py
from core.cost_calculator import get_cost_calculator

calculator = get_cost_calculator()
summary = calculator.get_summary()
print(summary)
```

---

## 🚨 주의사항

### 1. API 키 보안

- ❌ **절대 GitHub에 올리지 마세요**
- ✅ `.gitignore`에 `.env` 추가됨
- ✅ `.env.template`만 공유

### 2. Rate Limit

- Gemini Flash: 분당 60회
- GPT-4o-mini: 분당 500회
- 초과 시 자동 Fallback

### 3. 에러 처리

모든 LLM 호출은 try-catch로 감싸져 있습니다:

```python
try:
    response = litellm.completion(...)
except Exception as e:
    # Fallback 로직
    print(f"LLM 실패: {e}")
```

---

## 📊 API 호출 흐름

```
사용자 요청
    ↓
Router.classify_intent_with_llm()
    → Gemini Flash API 호출
    → 의도 분류 (QUERY/SEARCH/ANALYSIS/GENERATION)
    ↓
Researcher.search_documents() (미구현)
    → Milvus 벡터 검색
    ↓
Reasoner.generate_response_with_fallback()
    → GPT-4o-mini API 호출
    → RAG 컨텍스트 + 사용자 질문 → 답변 생성
    ↓
Synthesizer.format_response() (미구현)
    → Gemini Flash API 호출
    → 마크다운 포맷팅
    ↓
Guardrail.check_safety() (미구현)
    → Gemini Flash API 호출
    → 안전성 검수
    ↓
최종 답변 반환
```

---

## 🔧 트러블슈팅

### 1. API 키 오류

```
Error: Invalid API key
```

**해결:**
- `.env` 파일에 올바른 API 키 입력
- 환경변수가 로드되었는지 확인

### 2. Rate Limit 오류

```
Error: Rate limit exceeded
```

**해결:**
- Fallback 모델이 자동으로 시도됨
- 잠시 대기 후 재시도

### 3. 모델 없음 오류

```
Error: Model not found
```

**해결:**
- 모델 이름 확인 (`gemini/gemini-2.0-flash-exp`)
- litellm 버전 확인 (`pip install --upgrade litellm`)

---

## 📝 참고 문서

- **litellm 공식 문서:** https://docs.litellm.ai/
- **OpenAI API 문서:** https://platform.openai.com/docs
- **Google Gemini API 문서:** https://ai.google.dev/docs
- **비용 계산기:** `core/cost_calculator.py`
- **로거:** `core/logger.py`

---

## ✅ 체크리스트

구현 완료:
- [x] Router LLM 연동 (Gemini Flash)
- [x] Reasoner LLM 연동 (GPT-4o-mini)
- [x] Fallback 체인 구현
- [x] 에러 처리
- [x] 환경변수 로드

구현 예정:
- [ ] Researcher LLM 연동
- [ ] Synthesizer LLM 연동
- [ ] Guardrail LLM 연동
- [ ] Agent 생성 LLM 개선
