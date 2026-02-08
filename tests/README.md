# Tests Module

AI-agent의 테스트 코드 및 분석 도구를 담당하는 모듈입니다.

## 📂 구조

```
tests/
├── test_pipeline_integration.py   # 파이프라인 통합 테스트
├── test_router.py                 # Router 단위 테스트
└── analyze_hybrid_results.py      # 하이브리드 분류 성능 분석
```

---

## 🧪 테스트 파일 설명

### 1. `test_pipeline_integration.py` - 파이프라인 통합 테스트

#### 개요
전체 파이프라인의 통합 테스트를 수행합니다. 각 단계가 올바르게 연동되는지 검증합니다.

#### 테스트 케이스

##### ✅ `test_simple_query`
- **목적**: 단순 질문 처리 테스트
- **입력**: "AI Drive가 뭐야?"
- **검증 항목**:
  - Router가 `QUERY` 의도로 분류
  - `simple` 복잡도 판단
  - GPT-4o-mini 모델 선택
  - 최종 답변 생성 확인

##### ✅ `test_complex_analysis`
- **목적**: 복잡한 분석 요청 처리 테스트
- **입력**: "AI Drive의 보안 정책과 데이터 거버넌스 체계를 상세히 분석해줘"
- **검증 항목**:
  - Router가 `ANALYSIS` 의도로 분류
  - `complex` 복잡도 판단
  - GPT-4o 모델 선택
  - 검색 결과 포함 확인

##### ✅ `test_bulk_generation`
- **목적**: 대량 생성 요청 처리 테스트
- **입력**: "AI Drive 사용자 매뉴얼 전체를 작성해줘"
- **검증 항목**:
  - Router가 `GENERATION` 의도로 분류
  - `bulk` 복잡도 판단
  - Claude-3.5-sonnet 모델 선택

##### ✅ `test_cost_tracking`
- **목적**: 비용 추적 기능 테스트
- **검증 항목**:
  - 비용 정보 기록 확인
  - IN7 대비 절감률 계산
  - 모델별 비용 차이 검증

##### ✅ `test_logging`
- **목적**: 로깅 시스템 테스트
- **검증 항목**:
  - 세션 ID 생성
  - 각 단계별 로그 기록
  - 로그 파일 저장 확인

#### 실행 방법
```bash
# 전체 통합 테스트 실행
python -m pytest tests/test_pipeline_integration.py -v

# 특정 테스트만 실행
python -m pytest tests/test_pipeline_integration.py::test_simple_query -v

# 상세 출력 포함
python -m pytest tests/test_pipeline_integration.py -v -s
```

---

### 2. `test_router.py` - Router 단위 테스트

#### 개요
Router의 의도 분류 및 복잡도 판단 기능을 단위 테스트합니다.

#### 테스트 케이스

##### ✅ `test_intent_classification`
- **목적**: 의도 분류 정확도 테스트
- **테스트 데이터**:
  - "AI Drive가 뭐야?" → `QUERY`
  - "데이터 분석해줘" → `ANALYSIS`
  - "보고서 작성해줘" → `GENERATION`
  - "문서 찾아줘" → `SEARCH`

##### ✅ `test_complexity_determination`
- **목적**: 복잡도 판단 정확도 테스트
- **테스트 데이터**:
  - 짧은 질문 → `simple`
  - 상세 분석 요청 → `complex`
  - 대량 생성 요청 → `bulk`

##### ✅ `test_model_selection`
- **목적**: 복잡도별 모델 선택 검증
- **검증 항목**:
  - simple → GPT-4o-mini
  - complex → GPT-4o
  - bulk → Claude-3.5-sonnet

#### 실행 방법
```bash
# Router 단위 테스트 실행
python -m pytest tests/test_router.py -v
```

---

### 3. `analyze_hybrid_results.py` - 하이브리드 분류 성능 분석

#### 개요
키워드 기반 분류와 LLM 기반 분류의 성능을 비교 분석하는 도구입니다.

#### 분석 항목

##### 1. 정확도 비교
- 키워드 기반 분류 정확도
- LLM 기반 분류 정확도
- 하이브리드 방식 정확도

##### 2. 비용 분석
- 키워드 기반: 무료
- LLM 기반: 전체 요청에 API 호출
- 하이브리드: 신뢰도 < 0.7일 때만 API 호출

##### 3. 성능 지표
- **정확도 (Accuracy)**: 전체 중 올바른 분류 비율
- **신뢰도 (Confidence)**: 분류 결과의 확신 정도
- **API 호출률**: LLM API를 호출한 비율
- **비용 절감률**: 하이브리드 방식의 비용 절감 효과

#### 실행 방법
```bash
# 분석 실행
python tests/analyze_hybrid_results.py

# 결과 예시:
# ========================================
# 하이브리드 의도 분류 성능 분석
# ========================================
# 
# [키워드 기반 분류]
# 정확도: 85.2%
# 평균 신뢰도: 0.73
# 
# [LLM 기반 분류]
# 정확도: 96.8%
# API 호출: 100%
# 
# [하이브리드 방식]
# 정확도: 94.5%
# API 호출: 32.1%
# 비용 절감: 67.9%
```

#### 테스트 데이터셋
분석에 사용되는 샘플 데이터:
- QUERY: 단순 질문 (20개)
- ANALYSIS: 분석 요청 (20개)
- GENERATION: 생성 요청 (20개)
- SEARCH: 검색 요청 (20개)

---

## 🚀 전체 테스트 실행

### 모든 테스트 한 번에 실행
```bash
# pytest 사용
python -m pytest tests/ -v

# 커버리지 포함
python -m pytest tests/ --cov=core --cov-report=html
```

### 테스트 결과 확인
```bash
# HTML 커버리지 리포트 열기
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

---

## 📊 테스트 커버리지 목표

| 모듈 | 목표 커버리지 | 현재 상태 |
|------|--------------|----------|
| `pipeline.py` | 80% | 🟢 달성 |
| `cost_calculator.py` | 90% | 🟢 달성 |
| `logger.py` | 85% | 🟢 달성 |

---

## 🔧 테스트 환경 설정

### 필수 패키지 설치
```bash
pip install pytest pytest-cov
```

### Mock 데이터 사용
테스트는 기본적으로 Mock 데이터를 사용합니다:
- **RAG 검색**: Mock 문서 반환
- **LLM API**: 실제 API 호출 (`.env` 설정 필요)

### 환경 변수 설정
테스트 실행 전 `.env` 파일 설정:
```env
OPENAI_API_KEY=your_test_key
ANTHROPIC_API_KEY=your_test_key
```

---

## 🐛 디버깅

### 테스트 실패 시 확인 사항

#### 1. API 키 확인
```bash
# .env 파일 존재 확인
ls .env

# API 키 설정 확인
cat .env | grep API_KEY
```

#### 2. 로그 확인
테스트 실행 시 `logs/` 폴더에 세션 로그가 생성됩니다:
```bash
# 최근 로그 확인
ls -lt logs/ | head -5
```

#### 3. 상세 출력 모드
```bash
# 모든 print 출력 표시
python -m pytest tests/ -v -s

# 특정 테스트만 디버그
python -m pytest tests/test_router.py::test_intent_classification -v -s
```

---

## 📈 성능 벤치마크

### Router 성능
- **평균 처리 시간**: ~150ms
- **키워드 분류**: ~5ms
- **LLM 분류**: ~800ms (API 호출 시)

### 전체 파이프라인 성능
- **Simple 요청**: ~2-3초
- **Complex 요청**: ~5-8초
- **Bulk 요청**: ~10-15초

---

## 🧹 테스트 정리

### 테스트 로그 삭제
```bash
# 모든 테스트 로그 삭제
rm -rf logs/session_*.json

# 7일 이상 된 로그만 삭제 (Windows PowerShell)
Get-ChildItem logs/ -Filter "session_*.json" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item
```

### 캐시 정리
```bash
# pytest 캐시 삭제
rm -rf .pytest_cache/

# Python 캐시 삭제
find . -type d -name "__pycache__" -exec rm -rf {} +
```

---

## 📝 새로운 테스트 추가하기

### 1. 단위 테스트 추가
```python
# tests/test_new_feature.py
import pytest
from core.pipeline import NewFeature

def test_new_feature():
    """새 기능 테스트"""
    feature = NewFeature()
    result = feature.process("테스트 입력")
    
    assert result is not None
    assert "expected_key" in result
```

### 2. 통합 테스트 추가
```python
# tests/test_pipeline_integration.py에 추가
def test_new_integration():
    """새로운 통합 시나리오 테스트"""
    pipeline = Pipeline(use_rag=False)
    result = pipeline.process("새로운 테스트 케이스")
    
    # 검증
    assert result["success"] == True
```

### 3. 테스트 실행 확인
```bash
python -m pytest tests/test_new_feature.py -v
```

---

## 🔍 CI/CD 통합

### GitHub Actions 예시
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest tests/ --cov=core --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📚 참고 자료

- [Core README](../core/README.md) - 핵심 로직 설명
- [메인 README](../README.md) - 프로젝트 전체 개요
- [pytest 공식 문서](https://docs.pytest.org/)
