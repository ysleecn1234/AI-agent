# Feature-H AI Drive 파트 분석 리포트

## 📋 개요
Feature-H 브랜치의 AI Drive 파트는 **문서 관리 및 RAG(Retrieval-Augmented Generation) 시스템**의 핵심 기능을 구현한 모듈입니다. 파일 업로드부터 벡터 검색까지 전체 파이프라인이 체계적으로 구현되어 있습니다.

---

## ✅ 구현 완료 현황

### 1. 핵심 파이프라인 (5단계)
- [x] **Step 1**: 파일 파싱 (PDF, DOCX, PPTX, TXT, MD, CSV)
- [x] **Step 2**: 텍스트 청킹 (1000토큰, 200오버랩)
- [x] **Step 3**: 임베딩 생성 (OpenAI text-embedding-3-small)
- [x] **Step 4**: Milvus 벡터 DB 저장
- [x] **Step 5**: PostgreSQL 메타데이터 저장

### 2. 데이터베이스 연동
- [x] **Milvus**: 벡터 검색 엔진 (유사도 검색, 권한 필터링)
- [x] **PostgreSQL**: 메타데이터 관리 (문서, 활동 로그, 비용 로그)

### 3. API 엔드포인트
- [x] 문서 업로드 API
- [x] 문서 검색 API
- [x] 문서 조회/삭제 API
- [x] 버전 관리 API

### 4. 인프라
- [x] Docker Compose 설정 (Milvus + PostgreSQL)
- [x] 환경 변수 관리

---

## 📁 파일 구조

```
services/ai_drive/
├── core/
│   ├── __init__.py
│   └── embedding.py              # 임베딩 생성 (OpenAI API)
├── db/
│   ├── __init__.py
│   ├── milvus_client.py          # Milvus 벡터 DB 클라이언트
│   └── postgres_client.py        # PostgreSQL 메타데이터 DB 클라이언트
├── routers/
│   ├── __init__.py
│   └── documents.py              # FastAPI 라우터 (REST API)
├── tests/
│   ├── __init__.py
│   └── test_parser.py            # 파일 파싱 테스트
├── utils/
│   ├── __init__.py
│   ├── chunker.py                # 텍스트 청킹 유틸리티
│   └── file_parser.py            # 파일 파싱 유틸리티
└── pipeline.py                   # 통합 파이프라인 (메인)
```

---

## 🔧 주요 컴포넌트 분석

### 1. **pipeline.py** - 통합 파이프라인
**역할**: 전체 문서 처리 워크플로우 조율

**주요 기능**:
- `process_file_upload()`: 파일 업로드 → 파싱 → 청킹 → 임베딩 → 저장
- `process_chat_save()`: 채팅 결과 저장
- `process_agent_save()`: 에이전트 결과 저장

**처리 흐름**:
```
파일 업로드
  ↓
메타데이터 생성 (PostgreSQL)
  ↓
파일 파싱 (FileParser)
  ↓
텍스트 청킹 (TextChunker)
  ↓
임베딩 생성 (EmbeddingGenerator)
  ↓
벡터 저장 (Milvus) + 메타데이터 업데이트 (PostgreSQL)
  ↓
활동/비용 로그 기록
```

---

### 2. **file_parser.py** - 파일 파싱
**지원 형식**: PDF, DOCX, PPTX, TXT, MD, CSV

**기술 스택**:
- `PyMuPDF (fitz)`: PDF 파싱
- `python-docx`: DOCX 파싱
- `python-pptx`: PPTX 파싱
- 표준 라이브러리: TXT, MD, CSV

**특징**:
- 페이지/슬라이드 단위 구분
- 인코딩 자동 감지 (UTF-8, CP949)
- 빈 페이지/슬라이드 필터링

---

### 3. **chunker.py** - 텍스트 청킹
**설정**:
- 청크 크기: 1000토큰
- 오버랩: 200토큰
- 인코딩: `cl100k_base` (tiktoken)

**기능**:
- 토큰 기반 청킹 (문자 수가 아닌 토큰 수)
- 메타데이터 포함 청킹 (인덱스, 토큰 수, 문자 수)

---

### 4. **embedding.py** - 임베딩 생성
**모델**: OpenAI `text-embedding-3-small`
- 차원: 1536
- 비용: 1M 토큰당 $0.02 (약 28원)

**기능**:
- 단일/배치 임베딩 생성
- 빈 텍스트 필터링
- API 에러 핸들링

---

### 5. **milvus_client.py** - 벡터 DB
**컬렉션 스키마**:
```python
- chunk_id: UUID (Primary Key)
- doc_id: UUID (문서 ID)
- chunk_text: VARCHAR(5000)
- embedding: FLOAT_VECTOR(1536)
- visibility: VARCHAR(20)
- creator_department: VARCHAR(100)
- version: INT64
- is_latest: BOOL
- status: VARCHAR(20)
- created_at: INT64
```

**주요 기능**:
- 벡터 저장/검색
- 권한 기반 필터링 (부서별, 공개범위별)
- 버전 관리
- 유사도 검색 (L2 거리)

**검색 조건**:
```python
status = 'active' AND 
is_latest = true AND 
(visibility = 'company' OR 
 (visibility = 'team' AND creator_department = 사용자부서))
```

---

### 6. **postgres_client.py** - 메타데이터 DB
**테이블 구조**:

#### `documents` 테이블
- 문서 메타데이터 (제목, 작성자, 부서, 공개범위 등)
- 파일 정보 (크기, 타입, 파일명)
- 버전 관리 (parent_doc_id, version, is_latest)
- 태그/키워드 (JSONB)

#### `activity_logs` 테이블
- 사용자 활동 추적 (업로드, 검색, 삭제 등)
- 성공/실패 여부
- 처리 시간 (duration_ms)

#### `cost_logs` 테이블
- 비용 추적 (토큰 사용량, USD/KRW)
- 모델별 비용 분리
- 작업별 비용 집계

**주요 기능**:
- 문서 CRUD
- 버전 히스토리 관리
- 활동/비용 로그 기록
- 통계 조회

---

### 7. **documents.py** - FastAPI 라우터
**API 엔드포인트**:
- `POST /upload`: 파일 업로드
- `POST /search`: 문서 검색 (RAG)
- `GET /documents`: 문서 목록 조회
- `GET /documents/{doc_id}`: 문서 상세 조회
- `DELETE /documents/{doc_id}`: 문서 삭제

---

## 🐳 Docker 환경 설정

### docker-compose.yml
**서비스**:
1. **etcd**: Milvus 메타데이터 저장소
2. **minio**: Milvus 객체 스토리지
3. **milvus**: 벡터 검색 엔진 (포트 19530)
4. **postgres**: 메타데이터 DB (포트 5432)

**실행 방법**:
```bash
docker-compose up -d
```

---

## 💡 개선 제안 사항

### 1. 누락된 기능
- [ ] `PostgresClient.update_chunk_count()` 메서드 구현
- [ ] 파일 업로드 시 실제 파일 저장 (현재는 경로만 받음)
- [ ] 에러 핸들링 강화 (재시도 로직, 부분 실패 처리)

### 2. 성능 최적화
- [ ] 대용량 파일 처리 (스트리밍 파싱)
- [ ] 배치 임베딩 크기 제한 (OpenAI API 제한 고려)
- [ ] Milvus 인덱스 최적화 (IVF_FLAT → HNSW)

### 3. 보안
- [ ] 파일 타입 검증 강화 (MIME 타입 체크)
- [ ] 파일 크기 제한
- [ ] SQL Injection 방지 (현재 SQLAlchemy ORM 사용으로 기본 방어)

### 4. 테스트
- [ ] 통합 테스트 추가 (전체 파이프라인)
- [ ] Milvus/PostgreSQL 연동 테스트
- [ ] API 엔드포인트 테스트

### 5. 문서화
- [ ] API 문서 (Swagger/OpenAPI)
- [ ] 데이터베이스 스키마 문서
- [ ] 배포 가이드

---

## 🎯 다음 단계 권장 사항

### 우선순위 1: 테스트 및 검증
1. Docker 환경 실행 및 연결 테스트
2. 파일 업로드 → 검색 전체 플로우 테스트
3. 권한 필터링 검증

### 우선순위 2: Core Pipeline 연동
1. `core/pipeline.py`의 Researcher 레이어와 AI Drive 연동
2. RAG 검색 결과를 Reasoner로 전달
3. 통합 테스트

### 우선순위 3: 프로덕션 준비
1. 에러 핸들링 강화
2. 로깅 개선
3. 모니터링 설정 (Prometheus, Grafana)

---

## 📊 기술 스택 요약

| 카테고리 | 기술 |
|---------|------|
| **파일 파싱** | PyMuPDF, python-docx, python-pptx |
| **텍스트 처리** | tiktoken |
| **임베딩** | OpenAI text-embedding-3-small |
| **벡터 DB** | Milvus 2.3.4 |
| **메타데이터 DB** | PostgreSQL 15 |
| **ORM** | SQLAlchemy |
| **API** | FastAPI |
| **컨테이너** | Docker, Docker Compose |

---

## ✨ 총평

Feature-H의 AI Drive 파트는 **매우 체계적이고 완성도 높게 구현**되어 있습니다. 

**강점**:
- 명확한 책임 분리 (파싱, 청킹, 임베딩, 저장)
- 확장 가능한 아키텍처
- 권한 관리 및 버전 관리 구현
- 비용 추적 시스템

**개선 필요**:
- 테스트 커버리지 확대
- 에러 핸들링 강화
- 성능 최적화 (대용량 파일)

전반적으로 **프로덕션 레벨에 가까운 구현**이며, 몇 가지 보완 작업 후 실제 서비스에 투입 가능한 수준입니다.
