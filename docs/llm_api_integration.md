# LLM API 통합 가이드

**작성일:** 2026-02-08  
**작성자:** Kwon (feature-Y)  
**최종 업데이트:** 2026-02-08 (기획서 역할 매핑 적용)

---

## 📋 개요

이 문서는 AI-agent 프로젝트에서 LLM API를 어디서 어떻게 사용하는지 설명합니다.  
**기획서의 모델 역할 매핑**에 따라 각 Layer별로 최적의 모델을 배치했습니다.

---

## 🎯 기획서 기준 모델 역할 매핑

| 모델 | 역할 (Layer) | 선정 사유 |
|------|-------------|----------|
| **Gemini 2.0 Flash** | Router / 자동 태깅 | **[속도]** TTFT 0.2s 미만. 단순 요약 및 의도 파싱 시 가성비와 속도가 압도적 |
| **Gemini Pro** | Researcher (RAG) | **[대용량 컨텍스트]** 수백 페이지의 문서를 한 번에 읽는 능력과 멀티모달 파일 해석력 탁월 |
| **GPT-5.2 / Mini** | Reasoner (추론) | **[지능]** 현존 모델 중 추론 벤치마크(MMLU) 최상위. 복잡한 비즈니스 수식 및 논리 구조 설계에 최적 |
| **Claude 4.5** | Synthesizer / Agent 생성 | **[일관성]** 가장 인간 친화적인 문체와 정확한 JSON 스키마 준수 능력 보유 |
| **DeepSeek-R1** | Verification (검증) | **[논리 구조]** 사고의 사슬(CoT)을 통해 답변의 모순을 찾아내는 팩트체크 특화 성능 |
| **Llama 4** | Guardrail | **[보안/비용]** 사내 기밀 문서의 로컬 파싱 및 개인정보 필터링 시 API 비용 제로화 및 보안성 확보 |

---

## 🔑 필요한 API 키

### 1. Google API (Gemini)
- **용도:** Router (의도 분류), Researcher (RAG 검색)
- **모델:** `gemini-2.0-flash-exp`, `gemini-2.0-pro-exp`
- **환경변수:** `GOOGLE_API_KEY`

### 2. OpenAI API
- **용도:** Reasoner (답변 생성), Embedding (벡터화)
- **모델:** `gpt-5.2`, `gpt-5.2-mini`, `text-embedding-3-small`
- **환경변수:** `OPENAI_API_KEY`

### 3. Anthropic API
- **용도:** Synthesizer (답변 정리), Fallback
- **모델:** `claude-sonnet-4-5-20250514`
- **환경변수:** `ANTHROPIC_API_KEY`

### 4. Deepseek API
- **용도:** Verification (검증), Fallback
- **모델:** `deepseek-r1`, `deepseek-chat`
- **환경변수:** `DEEPSEEK_API_KEY`

### 5. Meta Llama (Optional - 로컬)
- **용도:** Guardrail (보안, 로컬 파싱)
- **모델:** `llama-4-maverick-17b-128e-instruct`
- **환경변수:** 로컬 실행 시 불필요

---

## 📂 API 사용 위치

### 1. **Router (의도 분류)** ✅ 구현 완료

**파일:** `core/pipeline.py`  
**클래스:** `Router`  
**메서드:** `classify_intent_with_llm()`  
**라인:** 122-173

**사용 모델:**
- Primary: `gemini/gemini-2.0-flash-exp` (TTFT 0.2s)

**코드 위치:**
```python
# core/pipeline.py:49
def __init__(self):
    self.model = "gemini/gemini-2.0-flash-exp"  # 빠른 의도 분류용 (TTFT 0.2s, 기획서 기준)

# core/pipeline.py:122
def classify_intent_with_llm(self, user_input: str) -> IntentType:
    import litellm
    
    response = litellm.completion(
        model=self.model,
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

### 2. **Reasoner (답변 생성)** ✅ 구현 완료

**파일:** `core/pipeline.py`  
**클래스:** `Reasoner`  
**메서드:** `generate_response_with_fallback()`  
**라인:** 518-560

**사용 모델:**
- Primary: `gpt-5.2` (MMLU 최상위)
- Fallback 1: `gpt-5.2-mini`
- Fallback 2: `claude-sonnet-4-5-20250514` (Synthesizer)
- Fallback 3: `deepseek-r1` (Verification)
- Fallback 4: `llama-4-maverick-17b-128e-instruct` (Guardrail)

**코드 위치:**
```python
# core/pipeline.py:480
self.model_mapping = {
    ComplexityLevel.SIMPLE.value: "gemini/gemini-2.0-flash-exp",  # Router (속도)
    ComplexityLevel.COMPLEX.value: "gpt-5.2",  # Reasoner (지능)
    ComplexityLevel.BULK.value: "gemini/gemini-2.0-pro-exp"  # Researcher (대용량)
}

# core/pipeline.py:518
def generate_response_with_fallback(self, context: Dict[str, Any]) -> tuple[str, str]:
    import litellm
    
    models_to_try = self.fallback_models.get(complexity, ["gpt-5.2"])
    
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

**Fallback 체인 (COMPLEX):**
1. GPT-5.2 시도 (Reasoner - 지능)
2. 실패 시 GPT-5.2-mini 시도
3. 실패 시 Claude 4.5 시도 (Synthesizer - 일관성)
4. 실패 시 DeepSeek-R1 시도 (Verification - CoT)
5. 실패 시 Llama 4 시도 (Guardrail - 보안)
6. 모두 실패 시 Exception 발생

---

### 3. **Researcher (RAG 검색)** - 미구현

**파일:** `core/pipeline.py`  
**클래스:** `Researcher`  
**메서드:** `search_documents()`  
**라인:** 300-400

**현재 상태:** Mock (구현 예정)

**예정 모델:**
- Primary: `gemini/gemini-2.0-pro-exp` (대용량 컨텍스트, 멀티모달)
- Embedding: `text-embedding-3-small` (OpenAI)

**선정 사유:**
- 수백 페이지의 문서를 한 번에 읽는 능력
- 이미지/표가 섞인 멀티모달 파일 해석력 탁월

---

### 4. **Synthesizer (답변 정리)** - 미구현

**파일:** `core/pipeline.py`  
**클래스:** `Synthesizer`  
**메서드:** `format_response()`  
**라인:** 600-700

**현재 상태:** Mock (구현 예정)

**예정 모델:**
- Primary: `claude-sonnet-4-5-20250514` (일관성, JSON 스키마)

**선정 사유:**
- 가장 인간 친화적인 문체
- 정확한 JSON 스키마 준수 능력

---

### 5. **Verification (검증)** - 미구현

**파일:** `core/pipeline.py`  
**클래스:** `Reasoner` (verify 메서드)  
**메서드:** `verify()`  
**라인:** 546-560

**현재 상태:** Mock (구현 예정)

**예정 모델:**
- Primary: `deepseek/deepseek-r1` (CoT 팩트체크)

**선정 사유:**
- 사고의 사슬(CoT)을 통해 답변의 모순을 찾아냄
- 논리 구조 검증 특화

---

### 6. **Guardrail (보안 검수)** - 미구현

**파일:** `core/pipeline.py`  
**클래스:** `Guardrail`  
**메서드:** `check_safety()`, `verify_quality()`  
**라인:** 700-800

**현재 상태:** Mock (구현 예정)

**예정 모델:**
- Primary: `meta-llama/llama-4-maverick-17b-128e-instruct` (로컬)

**선정 사유:**
- 사내 기밀 문서의 로컬 파싱
- 개인정보 필터링 시 API 비용 제로화
- 보안성 확보

---

### 7. **Agent 생성 (Orchestrator)**

**파일:** `app/core/orchestrator.py`  
**클래스:** `Orchestrator`  
**메서드:** `analyze_for_draft()`, `_analyze_conversation()`  
**라인:** 147-250

**사용 모델:**
- Pipeline 내부 모델 사용 (간접 호출)
- Synthesizer 역할: Claude 4.5 (JSON 스키마 생성)

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
    "complexity": "complex",
    "user_input": "AI가 뭐야?",
    "retrieved_documents": []
}
response, model = reasoner.generate_response(context)
print(f"모델: {model}")  # gpt-5.2
print(response)
```

---

## 💰 비용 관리

### 1. 모델별 비용 (2026년 기준)

| 모델 | 역할 | Input (1M tokens) | Output (1M tokens) |
|------|------|-------------------|-------------------|
| `gemini-2.0-flash-exp` | Router | 무료 (현재) | 무료 (현재) |
| `gemini-2.0-pro-exp` | Researcher | $1.25 | $5.00 |
| `gpt-5.2` | Reasoner | $5.00 | $15.00 |
| `gpt-5.2-mini` | Reasoner (Fallback) | $0.30 | $1.20 |
| `claude-sonnet-4-5` | Synthesizer | $3.00 | $15.00 |
| `deepseek-r1` | Verification | $0.55 | $2.19 |
| `llama-4` | Guardrail (로컬) | 무료 | 무료 |
| `text-embedding-3-small` | Embedding | $0.02 | - |

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
- GPT-5.2: 분당 500회
- Claude 4.5: 분당 50회
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

## 📊 API 호출 흐름 (기획서 기준)

```
사용자 요청
    ↓
Router.classify_intent_with_llm()
    → Gemini 2.0 Flash API 호출 (TTFT 0.2s)
    → 의도 분류 (QUERY/SEARCH/ANALYSIS/GENERATION)
    ↓
Researcher.search_documents() (미구현)
    → Gemini Pro API 호출 (멀티모달, 대용량)
    → Milvus 벡터 검색
    ↓
Reasoner.generate_response_with_fallback()
    → GPT-5.2 API 호출 (MMLU 최상위)
    → RAG 컨텍스트 + 사용자 질문 → 답변 생성
    ↓
Synthesizer.format_response() (미구현)
    → Claude 4.5 API 호출 (일관성, JSON 스키마)
    → 마크다운 포맷팅
    ↓
Verification.verify() (미구현)
    → DeepSeek-R1 API 호출 (CoT 팩트체크)
    → 논리적 모순 검증
    ↓
Guardrail.check_safety() (미구현)
    → Llama 4 로컬 실행 (보안, 비용 제로)
    → 개인정보 필터링, 안전성 검수
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
- **Anthropic Claude API 문서:** https://docs.anthropic.com/
- **DeepSeek API 문서:** https://platform.deepseek.com/
- **비용 계산기:** `core/cost_calculator.py`
- **로거:** `core/logger.py`

---

## ✅ 체크리스트

구현 완료:
- [x] Router LLM 연동 (Gemini 2.0 Flash)
- [x] Reasoner LLM 연동 (GPT-5.2)
- [x] Fallback 체인 구현 (기획서 역할 기준)
- [x] 에러 처리
- [x] 환경변수 로드

구현 예정:
- [ ] Researcher LLM 연동 (Gemini Pro)
- [ ] Synthesizer LLM 연동 (Claude 4.5)
- [ ] Verification 연동 (DeepSeek-R1)
- [ ] Guardrail 연동 (Llama 4)
- [ ] Agent 생성 LLM 개선
