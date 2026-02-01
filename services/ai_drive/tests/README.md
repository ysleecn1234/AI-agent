# Tests Module

AI 드라이브의 테스트 코드를 담당하는 모듈입니다.

## 📂 구조

```
tests/
├── test_integration.py    # 통합 테스트 (전체 파이프라인)
└── test_parser.py         # 파일 파서 단위 테스트
```

---

## 🧪 테스트 파일 설명

### 1. `test_integration.py` - 통합 테스트

#### 개요
전체 파이프라인의 통합 테스트를 수행합니다. 각 단계가 올바르게 연동되는지 검증합니다.

#### 테스트 케이스

##### ✅ `test_chat_save`
- **목적**: 채팅 저장 기능 테스트
- **검증 항목**:
  - 채팅 내용 → PostgreSQL 저장
  - 청킹 → Milvus 저장
  - AI 태깅 작동 확인
  - 문서 조회 확인

##### ✅ `test_rag_search`
- **목적**: RAG 검색 기능 테스트
- **검증 항목**:
  - 문서 저장 후 검색
  - 유사도 기반 결과 반환
  - 권한 필터링 작동

##### ✅ `test_doc_chat`
- **목적**: 문서별 채팅 테스트
- **검증 항목**:
  - 5단계 파이프라인 작동
  - 특정 문서 내 청크 검색
  - 답변 생성 확인

##### ✅ `test_version_management`
- **목적**: 버전 관리 테스트
- **검증 항목**:
  - 문서 생성 시 version=1
  - 동일 파일 재업로드 시 버전 증가
  - is_latest 플래그 확인

##### ✅ `test_cost_logging`
- **목적**: 비용 로그 테스트
- **검증 항목**:
  - 임베딩 비용 기록
  - 저장 비용 기록
  - 총 비용 집계 확인

#### 실행 방법

```bash
# 전체 통합 테스트 실행
cd ~/AI-agent/services/ai_drive
python -m tests.test_integration

# pytest로 실행 (상세 출력)
python -m pytest tests/test_integration.py -v

# 특정 테스트만 실행
python -m pytest tests/test_integration.py::TestIntegration::test_chat_save -v
```

---

### 2. `test_parser.py` - 파서 단위 테스트

#### 개요
파일 파싱 기능을 단위 테스트합니다.

#### 테스트 케이스

##### ✅ PDF 파싱
- PyMuPDF로 텍스트 추출
- 페이지별 텍스트 확인

##### ✅ DOCX 파싱
- python-docx로 텍스트 추출
- 문단별 텍스트 확인

##### ✅ PPTX 파싱
- python-pptx로 텍스트 추출
- 슬라이드별 텍스트 확인

##### ✅ TXT/MD/CSV 파싱
- 직접 읽기
- 인코딩 처리 확인

#### 실행 방법

```bash
python -m tests.test_parser
```

---

## 🚀 전체 테스트 실행

### 모든 테스트 한 번에 실행

```bash
# 기본 실행
cd ~/AI-agent/services/ai_drive
python -m pytest tests/ -v

# 상세 출력 포함
python -m pytest tests/ -v -s

# 커버리지 포함
python -m pytest tests/ --cov=. --cov-report=html
```

### 테스트 결과 예시

```
============================================================
AI 드라이브 통합 테스트
============================================================

[1/5] 채팅 저장 테스트
✓ 채팅 저장 테스트 통과

[2/5] RAG 검색 테스트
✓ RAG 검색 테스트 통과 (결과: 2개)

[3/5] 문서별 채팅 테스트
✓ 문서별 채팅 테스트 통과

[4/5] 버전 관리 테스트
✓ 버전 관리 테스트 통과

[5/5] 비용 로그 테스트
✓ 비용 로그 테스트 통과 (총 비용: 3.18원)

============================================================
✅ 모든 통합 테스트 통과!
============================================================
```

---

## 📊 테스트 커버리지 목표

| 모듈 | 목표 커버리지 | 현재 상태 |
|------|--------------|----------|
| `pipeline.py` | 80% | 🟢 달성 |
| `core/rag_search.py` | 80% | 🟢 달성 |
| `core/doc_chat.py` | 80% | 🟢 달성 |
| `db/postgres_client.py` | 70% | 🟢 달성 |
| `db/milvus_client.py` | 70% | 🟢 달성 |
| `utils/file_parser.py` | 90% | 🟢 달성 |
| `utils/chunker.py` | 90% | 🟢 달성 |

---

## 🔧 테스트 환경 설정

### 필수 패키지 설치

```bash
pip install pytest pytest-cov
```

### 환경 변수 설정

테스트 실행 전 `.env` 파일 설정:

```env
# 필수
OPENAI_API_KEY=sk-xxx
POSTGRES_URL=postgresql://aiagent:aiagent123@localhost:5432/ai_drive
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 선택 (없으면 Mock 모드)
GOOGLE_API_KEY=xxx
```

### Mock 모드

API 키 없이도 테스트 가능:
- `GOOGLE_API_KEY` 없으면 → AI 태깅 Mock 모드
- 테스트용 더미 데이터 생성

---

## 🐛 디버깅

### 테스트 실패 시 확인 사항

#### 1. Docker 컨테이너 확인
```bash
docker ps

# PostgreSQL, Milvus 실행 중인지 확인
# ai-drive-postgres, milvus-standalone
```

#### 2. DB 연결 확인
```bash
# PostgreSQL
docker exec -it ai-drive-postgres psql -U aiagent -d ai_drive

# Milvus (포트 확인)
curl http://localhost:19530/v1/vector/collections
```

#### 3. 로그 확인
```bash
# 상세 출력 모드로 테스트
python -m pytest tests/ -v -s
```

#### 4. 개별 테스트 디버그
```bash
# 특정 테스트만 실행
python -m pytest tests/test_integration.py::TestIntegration::test_chat_save -v -s
```

---

## 🧹 테스트 정리

### 테스트 데이터 자동 정리

통합 테스트는 실행 후 생성된 문서를 자동 삭제합니다:

```python
def _cleanup(self):
    """테스트 데이터 정리"""
    for doc_id in self.created_doc_ids:
        postgres.delete_document(doc_id)
        milvus.delete_by_doc_id(doc_id)
```

### 수동 정리 (필요 시)

```bash
# PostgreSQL 테스트 데이터 삭제
docker exec -it ai-drive-postgres psql -U aiagent -d ai_drive
DELETE FROM documents WHERE title LIKE '%테스트%';
\q

# Milvus 컬렉션 초기화 (주의!)
# 개발 환경에서만 사용
```

---

## 📝 새로운 테스트 추가하기

### 1. 단위 테스트 추가

```python
# tests/test_new_feature.py
import pytest

def test_new_feature():
    """새 기능 테스트"""
    # Given
    input_data = "테스트 입력"
    
    # When
    result = new_function(input_data)
    
    # Then
    assert result is not None
    assert "expected" in result
```

### 2. 통합 테스트에 추가

```python
# tests/test_integration.py의 TestIntegration 클래스에 추가
def test_new_integration(self):
    """새로운 통합 시나리오 테스트"""
    pipeline = DocumentPipeline()
    
    result = pipeline.process_something(...)
    
    assert result["success"] == True
    
    pipeline.close()
```

### 3. 테스트 실행 확인

```bash
python -m pytest tests/test_new_feature.py -v
```

---

## 📈 성능 벤치마크

### 파이프라인 성능 (실측)

| 항목 | 평균 시간 |
|------|----------|
| 채팅 저장 | ~3.5초 |
| RAG 검색 | ~1초 |
| 문서별 채팅 | ~0.5초 |
| 파일 업로드 (1MB PDF) | ~4초 |

### 테스트 실행 시간

| 테스트 | 평균 시간 |
|--------|----------|
| test_chat_save | ~4초 |
| test_rag_search | ~4초 |
| test_doc_chat | ~3초 |
| test_version_management | ~4초 |
| test_cost_logging | ~4초 |
| **전체** | **~20초** |

---

## 📚 참고 자료

- [AI 드라이브 README](../README.md) - 모듈 전체 설명
- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-cov 문서](https://pytest-cov.readthedocs.io/)
