# Core Module

AI-agent의 핵심 파이프라인 로직을 담당하는 모듈입니다.

## 📂 구조

```
core/
├── pipeline.py          # 5단계 레이어드 파이프라인
├── cost_calculator.py   # 비용 계산 및 추적 시스템
└── logger.py            # 로깅 및 추적 시스템
```

---

## 🔄 Pipeline (`pipeline.py`)

### 개요
사용자 요청을 5단계 레이어드 아키텍처로 처리하는 핵심 파이프라인입니다.

### 5단계 파이프라인 구조

```
Router → Researcher → Reasoner → Synthesizer → Guardrail
```

#### 1️⃣ **Router** - 의도 분류 및 복잡도 판단
- **역할**: 사용자 요청의 의도 파악 및 적절한 LLM 선택
- **모델**: Gemini 3 Flash (`gemini/gemini-3-flash`)
- **선정 사유**: TTFT 0.2s 미만, 빠른 의도 파싱
- **주요 기능**:
  - 하이브리드 의도 분류 (키워드 기반 + LLM 기반)
  - 복잡도 판단 (simple, complex, bulk)
  - 신뢰도 기반 LLM 호출 최적화 (비용 절감)

**의도 분류 타입**:
- `QUERY`: 단순 질문
- `ANALYSIS`: 분석 요청
- `GENERATION`: 생성 요청
- `SEARCH`: 검색 요청

**복잡도 레벨**:
- `SIMPLE`: Gemini 3 Flash 사용
- `COMPLEX`: GPT-5 사용
- `BULK`: Claude Opus 4.6 사용

#### 2️⃣ **Researcher** - RAG 기반 정보 검색
- **역할**: AI Drive에서 관련 문서 검색 및 정보 인출
- **주요 기능**:
  - 벡터 검색을 통한 유사도 기반 정보 추출
  - 부서별 권한 필터링
  - Mock 데이터 지원 (개발 중)

#### 3️⃣ **Reasoner** - 논리적 답변 생성
- **역할**: 복잡도에 따른 적절한 LLM 선택 및 답변 생성
- **모델**: GPT-5 (COMPLEX), Gemini 3 Flash (SIMPLE), Gemini 3 Pro (BULK)
- **선정 사유**: MMLU 최상위 추론 능력
- **주요 기능**:
  - CoT(Chain of Thought) 기반 팩트체크
  - 모델 실패 시 Fallback 메커니즘
  - 답변의 논리적 일관성 검증

**Fallback 체인**:
```
SIMPLE: Gemini 3 Flash → GPT-4o-mini → Claude 4.5 → DeepSeek Chat
COMPLEX: GPT-5 → GPT-5-mini → Claude 4.5 → DeepSeek-R1 → Llama 4
BULK: Gemini 3 Pro → GPT-5 → Claude Opus 4.6 → Llama 4
```

#### 4️⃣ **Synthesizer** - 최종 답변 정제
- **역할**: 답변을 사용자 친화적으로 정제
- **모델**: Claude 4.5 (`claude-sonnet-4-5-20250514`)
- **선정 사유**: 일관성, JSON 스키마 준수 능력
- **주요 기능**:
  - LLM 기반 마크다운 포맷팅
  - 출처 정보 추가
  - 답변 구조화
  - Fallback: 기본 마크다운 변환

#### 5️⃣ **Guardrail** - 품질 검증
- **역할**: 최종 답변의 품질 및 안전성 검증
- **모델**: DeepSeek-R1 (`deepseek/deepseek-r1`)
- **선정 사유**: CoT 기반 논리 검증, 팩트체크 특화
- **주요 기능**:
  - LLM 기반 품질 검수 (COMPLEX/BULK만)
  - 유해성 필터링
  - 민감정보 탐지
  - 답변 품질 검증 (완성도, 논리적 일관성, 사실 정확성)
  - Fallback: 기본 검수 로직

---

## 💰 Cost Calculator (`cost_calculator.py`)

### 개요
모델별 토큰 단가 관리 및 실시간 비용 추적 시스템입니다.

### 주요 기능

#### 1. 모델별 가격 정보 관리
지원 모델:
- **OpenAI**: GPT-5, GPT-5-mini, GPT-4o, GPT-4o-mini
- **Anthropic**: Claude Opus 4.6, Claude Sonnet 4.5, Claude Haiku 4.5
- **Google**: Gemini 3 Pro, Gemini 3 Flash
- **DeepSeek**: DeepSeek-R1, DeepSeek Chat, DeepSeek V3.2
- **Meta**: Llama 4, Llama 3.3-70b

#### 2. 실시간 비용 계산
```python
calculator = get_cost_calculator()
cost_info = calculator.calculate_cost(
    model_name="gpt-4o",
    input_tokens=1000,
    output_tokens=500
)
```

**반환 정보**:
- `total_cost`: 총 비용 (USD)
- `input_cost`: 입력 토큰 비용
- `output_cost`: 출력 토큰 비용
- `in7_cost`: IN7 요금표 기준 비용
- `savings`: 절감액
- `savings_rate`: 절감률 (%)

#### 3. 복잡도별 예상 비용
```python
estimate = calculator.estimate_cost_by_complexity(
    complexity="complex",
    estimated_input_tokens=1000,
    estimated_output_tokens=500
)
```

#### 4. 세션 비용 리포트
```python
report = calculator.generate_cost_report(session_logs)
```

**리포트 내용**:
- 총 요청 수
- 모델별 사용 통계
- 총 비용 및 절감액
- IN7 대비 절감률

---

## 📊 Logger (`logger.py`)

### 개요
요청-처리-결과 전 과정을 로깅하여 운영성과 감사 대응성을 확보하는 시스템입니다.

### 주요 기능

#### 1. 세션 관리
```python
logger = get_logger()
session_id = logger.start_session(user_input="질문", user_id="user123")
```

#### 2. 단계별 로깅
```python
logger.log_step(
    step_name="Router",
    step_data={"intent": "query", "complexity": "simple"},
    duration_ms=150
)
```

#### 3. 모델 사용 로깅
```python
logger.log_model_usage(
    model_name="gpt-4o",
    input_tokens=1000,
    output_tokens=500,
    cost_info=cost_info
)
```

#### 4. 에러 로깅
```python
logger.log_error(
    error_type="ModelAPIError",
    error_message="API timeout",
    step_name="Reasoner"
)
```

#### 5. 세션 종료
```python
logger.end_session(
    final_result={"answer": "...", "sources": [...]},
    success=True
)
```

### 로그 저장 위치
- **디렉토리**: `logs/`
- **파일명 형식**: `session_{session_id}_{timestamp}.json`
- **콘솔 출력**: INFO 레벨 이상

---

## 🚀 사용 예시

### 전체 파이프라인 실행
```python
from core.pipeline import Pipeline

# 파이프라인 초기화
pipeline = Pipeline(use_rag=False)  # 개발 중에는 False

# 요청 처리
result = pipeline.process("AI Drive의 주요 기능은 무엇인가요?")

# 결과 출력
print(result["final_answer"])
print(f"비용: ${result['total_cost']:.6f}")
print(f"처리 시간: {result['total_duration_ms']:.0f}ms")
```

### 개별 컴포넌트 사용
```python
from core.pipeline import Router, Researcher, Reasoner

# Router만 사용
router = Router()
routing_result = router.route("복잡한 분석 요청")
print(f"의도: {routing_result['intent']}")
print(f"복잡도: {routing_result['complexity']}")
print(f"선택된 모델: {routing_result['selected_model']}")
```

---

## 🔧 설정

### 환경 변수
`.env` 파일에 다음 항목 설정:
```env
# OpenAI API
OPENAI_API_KEY=your_openai_key

# Anthropic API
ANTHROPIC_API_KEY=your_anthropic_key

# Google Gemini API
GOOGLE_API_KEY=your_google_key

# AI Drive 설정 (RAG 사용 시)
AI_DRIVE_API_URL=https://api.aidrive.example.com
AI_DRIVE_API_KEY=your_aidrive_key
```

### RAG 모드 전환
```python
# 개발/테스트: Mock 데이터 사용
pipeline = Pipeline(use_rag=False)

# 프로덕션: 실제 AI Drive 연동
pipeline = Pipeline(use_rag=True)
```

---

## 📈 성능 최적화

### 1. 하이브리드 의도 분류
- 키워드 기반 분류 우선 (무료)
- 신뢰도 < 0.7일 때만 LLM 호출
- **비용 절감**: 약 60-70%

### 2. 복잡도 기반 모델 선택
- Simple 요청 → Gemini 3 Flash (저비용, 고속)
- Complex 요청 → GPT-5 (고성능, 최고 추론력)
- Bulk 요청 → Gemini 3 Pro (대용량 컨텍스트)

### 3. Fallback 메커니즘
- 1차 모델 실패 시 자동 대체
- 최대 3회 재시도
- 안정성 향상

---

## 🧪 테스트

테스트 실행 방법은 [`tests/README.md`](../tests/README.md)를 참고하세요.

---

## 📝 로그 분석

### 세션 요약 조회
```python
logger = get_logger()
summary = logger.get_session_summary()

print(f"세션 ID: {summary['session_id']}")
print(f"총 처리 시간: {summary['total_duration_ms']}ms")
print(f"총 비용: ${summary['total_cost']:.6f}")
print(f"처리 단계 수: {summary['steps_count']}")
```

### 비용 리포트 생성
```python
from core.cost_calculator import get_cost_calculator

calculator = get_cost_calculator()
report = calculator.generate_cost_report(session_logs)

print(f"총 요청: {report['total_requests']}")
print(f"총 비용: ${report['total_cost']:.4f}")
print(f"IN7 대비 절감: {report['total_savings_rate']:.1f}%")
```

---

## 🔍 디버깅

### 로그 레벨 조정
```python
import logging

# 상세 로그 출력
logging.getLogger("PipelineLogger").setLevel(logging.DEBUG)
```

### 단계별 결과 확인
```python
pipeline = Pipeline(use_rag=False)
result = pipeline.process("테스트 질문")

# 각 단계 결과 확인
print("Router:", result["routing"])
print("Researcher:", result["research"])
print("Reasoner:", result["reasoning"])
print("Synthesizer:", result["synthesis"])
print("Guardrail:", result["guardrail"])
```

---

## 📚 참고 자료

- [메인 README](../README.md) - 프로젝트 전체 개요
- [개발 상태](../docs/development_status.md) - 현재 개발 진행 상황
- [AI Drive 분석](../docs/ai_drive_analysis.md) - RAG 시스템 분석
