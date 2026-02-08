# AI Drive Module

AI-agent의 문서 관리 및 RAG 검색 시스템을 담당하는 모듈입니다.

---

## 📂 구조

```
ai_drive/
├── pipeline.py                 # 문서 처리 메인 파이프라인
├── scheduler.py                # 아카이브 자동 삭제 스케줄러
├── routers/
│   └── documents.py            # FastAPI 라우터 (API 엔드포인트)
├── core/
│   ├── embedding.py            # OpenAI 임베딩 생성
│   ├── auto_tagger.py          # AI 자동 태깅 및 제목 생성 (Gemini Flash)
│   ├── cost_manager.py         # 크기별 과금 관리
│   ├── rag_search.py           # RAG 4단계 검색
│   ├── doc_chat.py             # 문서별 채팅 (2단계 간소화 버전)
│   └── pii_detector.py         # 개인정보 감지 및 차단
├── db/
│   ├── postgres_client.py      # PostgreSQL 클라이언트
│   └── milvus_client.py        # Milvus 벡터 DB 클라이언트
├── utils/
│   ├── file_parser.py          # 파일 파싱 (PDF, DOCX, PPTX, XLSX 등)
│   └── chunker.py              # 토큰 기반 텍스트 청킹
├── tests/                      # 테스트 (별도 README 참고)
├── storage/                    # 원본 파일 저장소
└── uploads/                    # 임시 업로드 폴더
```

---

## 🔄 주요 기능

### 1️⃣ 문서 업로드 및 처리

| 항목 | 내용 |
|------|------|
| 지원 형식 | PDF, DOCX, PPTX, XLSX, TXT, MD, CSV |
| 파일 제한 | 최대 50MB |
| 보안 | MIME 타입 검증 (파일 위조 방지) |

**처리 흐름:**
```
파일 업로드 → 텍스트 추출 → 청킹(1000토큰) → AI 태깅 → 임베딩 → 저장
```

### 2️⃣ 채팅/에이전트 결과 저장

| 항목 | 내용 |
|------|------|
| AI 자동 생성 | 제목, 상세 설명 (Gemini Flash) |
| 원본 보관 | storage/ 폴더에 .txt 파일로 저장 |

**처리 흐름:**
```
텍스트 입력 → AI 제목/설명 생성 → AI 태깅 → 청킹 → 임베딩 → 저장
```

### 3️⃣ RAG 4단계 검색

오케스트레이터 Researcher 레이어와 연동됩니다.

| 단계 | 역할 |
|------|------|
| Step 1 | 질문 임베딩 생성 (OpenAI) |
| Step 2 | Milvus 유사도 검색 (Top-10) |
| Step 3 | 권한 필터링 (visibility, department) |
| Step 4 | Freshness Score 적용 → Top-5 반환 |

### 4️⃣ 문서별 채팅 (5단계 SLM 파이프라인)

단일 문서에 대해 깊이 있는 질의응답을 수행하는 핵심 로직입니다. 비용 효율성을 위해 **Gemini Flash(Router/Researcher/Synthesizer)**와 **GPT-4o-mini(Reasoner)**를 혼합하여 사용합니다.

**처리 흐름 (Sequence Diagram):**

```mermaid
sequenceDiagram
    actor User as 사용자
    participant Drive as DocumentChat<br>(core/doc_chat.py)
    participant Router as LLM (Router)<br>(Gemini Flash)
    participant Milvus as Milvus (Researcher)<br>(Vector DB)
    participant Reasoner as LLM (Reasoner)<br>(GPT-4o-mini)
    participant Syn as LLM (Synthesizer)<br>(Gemini Flash)

    User->>Drive: chat(doc_id, question)
    
    Note right of Drive: Step 1. 의도 파악
    Drive->>Router: classify_intent(question)
    Router-->>Drive: "summary" / "search" / "analysis"

    Note right of Drive: Step 2. 관련 청크 검색
    Drive->>Milvus: search_by_doc_id(doc_id, vector)
    Milvus-->>Drive: [Chunk1, Chunk2, ...] (Top-5)

    Note right of Drive: Step 3. 답변 생성 (핵심 지능)
    Drive->>Reasoner: generate_answer(question, chunks, intent)
    Reasoner-->>Drive: Raw Answer (Text)
    
    Note right of Drive: Step 4. 답변 정리
    Drive->>Syn: format_answer(raw_answer)
    Syn-->>Drive: Markdown Formatted Answer

    Note right of Drive: Step 5. 안전성 검증
    Drive->>Drive: guardrail_check(pii_detection)
    Drive-->>User: Final Result
```

**단계별 상세 역할:**
1.  **Router (의도 파악)**: 사용자의 질문이 단순 조회인지, 요약인지, 비교 분석인지 분류합니다.
2.  **Researcher (정보 검색)**: 질문을 벡터화하여 해당 문서 내에서 가장 관련성 높은 청크(Chunk)를 Milvus에서 찾아옵니다.
3.  **Reasoner (추론 및 생성)**: 찾아낸 청크를 바탕으로 질문에 대한 답변을 생성합니다. (GPT-4o-mini 사용으로 추론 능력 강화)
4.  **Synthesizer (정제)**: 생성된 답변을 읽기 좋은 마크다운 포맷으로 다듬습니다.
5.  **Guardrail (보안)**: 답변에 포함된 개인정보(전화번호, 주민번호 등)를 마스킹합니다.

### 5️⃣ 버전 관리

- 동일 파일 재업로드 시 버전 자동 증가
- 이전 버전 `is_latest=False`, `status=archived` 처리
- 검색 시 최신 버전만 반환

### 6️⃣ 비용 관리

크기별 일일 저장 비용 (인세븐 대비 50~70% 절감):

| 크기 | 기준 | 일일 비용 |
|------|------|----------|
| 소형 | < 50KB | 0.3원 |
| 중형 | 50~500KB | 0.5원 |
| 대형 | > 500KB | 1.0원 |

### 7️⃣ 개인정보 보호

업로드/저장 시 자동 감지 및 차단:

| 항목 | 처리 |
|------|------|
| 주민등록번호 | 무조건 차단 |
| 전화번호 | 차단 |
| 이메일 | 차단 |
| 계좌번호 | 차단 |
| 신용카드번호 | 차단 |

---

## 📡 API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/documents/upload` | 파일 업로드 |
| POST | `/documents/chat-save` | 채팅 결과 저장 |
| POST | `/documents/agent-save` | 에이전트 결과 저장 |
| GET | `/documents` | 문서 목록 조회 |
| GET | `/documents/{doc_id}` | 문서 상세 조회 |
| GET | `/documents/{doc_id}/versions` | 버전 히스토리 조회 |
| DELETE | `/documents/{doc_id}` | 문서 삭제 (archived) |
| POST | `/documents/search` | RAG 검색 |
| POST | `/documents/{doc_id}/chat` | 문서별 채팅 |

---

## 🗄️ 데이터베이스 스키마

### PostgreSQL

**documents 테이블**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| doc_id | UUID (PK) | 문서 ID |
| title | VARCHAR(255) | 제목 |
| description | TEXT | 상세 설명 |
| creator_id | UUID | 작성자 ID |
| creator_department | VARCHAR(100) | 작성자 부서 |
| created_at | TIMESTAMP | 생성일 |
| modified_at | TIMESTAMP | 수정일 |
| visibility | VARCHAR(20) | 공개범위 (team/company/confidential) |
| status | VARCHAR(20) | 상태 (pending/processing/active/archived) |
| file_size | INTEGER | 파일 크기 (bytes) |
| file_type | VARCHAR(50) | 파일 형식 |
| filename | VARCHAR(255) | 원본 파일명 |
| file_path | VARCHAR(500) | 저장 경로 |
| version | INTEGER | 버전 번호 |
| parent_doc_id | UUID | 이전 버전 ID |
| is_latest | BOOLEAN | 최신 버전 여부 |
| tags | JSONB | 태그 배열 |
| keywords | JSONB | 키워드 배열 |
| doc_type | VARCHAR(50) | 문서 유형 |
| source_type | VARCHAR(20) | 출처 (file/chat/agent) |
| chunk_count | INTEGER | 청크 수 |

**activity_logs 테이블**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| log_id | UUID (PK) | 로그 ID |
| user_id | UUID | 사용자 ID |
| user_name | VARCHAR(100) | 사용자 이름 |
| doc_id | UUID | 문서 ID |
| action | VARCHAR(50) | 행동 (upload/search/chat/delete) |
| timestamp | TIMESTAMP | 시간 |
| success | BOOLEAN | 성공 여부 |
| ip_address | VARCHAR(45) | IP 주소 |
| details | JSONB | 상세 정보 |
| duration_ms | INTEGER | 처리 시간 (ms) |

**cost_logs 테이블**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| cost_id | UUID (PK) | 비용 로그 ID |
| user_id | UUID | 사용자 ID |
| doc_id | UUID | 문서 ID |
| operation | VARCHAR(50) | 작업 (embedding/tagging/storage/chat) |
| tokens_used | INTEGER | 사용 토큰 |
| cost_usd | DECIMAL(10,6) | 비용 (USD) |
| cost_krw | DECIMAL(10,2) | 비용 (KRW) |
| model_name | VARCHAR(50) | 사용 모델 |
| timestamp | TIMESTAMP | 시간 |

### Milvus

**ai_drive_documents 컬렉션**

| 필드 | 타입 | 설명 |
|------|------|------|
| id | INT64 (PK) | 자동 생성 ID |
| doc_id | VARCHAR(50) | 문서 ID |
| chunk_text | VARCHAR(5000) | 청크 텍스트 |
| embedding | FLOAT_VECTOR(1536) | 임베딩 벡터 |
| visibility | VARCHAR(20) | 공개범위 |
| creator_department | VARCHAR(100) | 작성자 부서 |
| version | INT64 | 버전 |
| is_latest | BOOL | 최신 버전 여부 |
| status | VARCHAR(20) | 상태 |

**인덱스**: IVF_FLAT, COSINE, nlist=1024

---

## 🔧 환경 변수

`.env` 파일 설정:

```env
# OpenAI (임베딩)
OPENAI_API_KEY=sk-xxx

# Gemini (태깅/제목 생성)
GOOGLE_API_KEY=xxx

# PostgreSQL
POSTGRES_URL=postgresql://aiagent:aiagent123@localhost:5432/ai_drive

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

---

## 💻 실행 방법

```bash
# 1. 사전 설치 (Mac)
brew install libmagic

# 2. Docker 실행
cd ~/AI-agent/services/ai_drive
docker-compose up -d

# 3. API 서버 실행
python -m routers.documents

# 4. API 문서 확인
# http://localhost:8001/docs
```

---

## ⏰ 스케줄러

아카이브 문서 자동 삭제 (30일 경과 시):
```bash
# 테스트 실행
python scheduler.py --test

# 프로덕션 실행 (매일 새벽 2시)
nohup python scheduler.py > scheduler.log 2>&1 &
```

---


## 🤝 오케스트레이터 연동

```python
# 오케스트레이터에서 호출
from services.ai_drive.core.rag_search import RAGSearcher

searcher = RAGSearcher()
results = searcher.search(
    query="마케팅 전략",
    user_department="개발팀",
    top_k=5
)
searcher.close()

# 반환 형식
[
    {
        "doc_id": "문서 ID",
        "content": "청크 텍스트",
        "source": "문서 제목",
        "score": 0.95,
        "author": "작성자",
        "department": "부서",
        "date": "2026-01-31"
    },
    ...
]
```

---

## 🧪 테스트

테스트 관련 상세 내용은 [tests/README.md](./tests/README.md)를 참고하세요.

```bash
python -m tests.test_integration
```

---

## 📋 TODO (팀 논의 필요)

- [ ] 채팅 저장 시 문서화 방식 결정 (원본 vs AI 정돈)
- [ ] 문서 미리보기 API 필요 여부
- [ ] 대용량 파일 스트리밍 처리
- [ ] Milvus 인덱스 최적화 (HNSW)

---

## 📚 참고 자료

- [메인 README](../../README.md)
- AI 드라이브 기획서 (Notion)
- 총정리 (Notion)
