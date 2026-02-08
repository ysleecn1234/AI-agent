
# Core 모듈

AI 드라이브의 핵심 비즈니스 로직을 담당하는 모듈입니다.

## 📂 파일 구조
```
core/
├── embedding.py      # 임베딩 생성
├── auto_tagger.py    # AI 자동 태깅
├── doc_chat.py       # 문서별 채팅
├── rag_search.py     # RAG 검색
├── pii_detector.py   # 개인정보 탐지
└── cost_manager.py   # 비용 계산
```

## 📄 파일별 설명

### 1. embedding.py
- **역할**: 텍스트를 벡터로 변환
- **모델**: OpenAI text-embedding-3-small (1536차원)
- **주요 메서드**:
  - `create(text)` - 단일 텍스트 임베딩
  - `create_batch(texts)` - 배치 임베딩

### 2. auto_tagger.py
- **역할**: 문서 내용 기반 자동 태그/키워드 생성
- **모델**: Gemini Flash
- **주요 메서드**:
  - `generate_tags(text, title)` - 태그, 키워드, 문서유형 생성

### 3. doc_chat.py
- **역할**: 특정 문서에 대한 질문/답변
- **모델**: GPT-4o-mini (답변 생성)
- **주요 메서드**:
  - `chat(doc_id, question, user_id)` - 문서별 채팅

### 4. rag_search.py
- **역할**: 전체 문서에서 RAG 기반 검색
- **주요 메서드**:
  - `search(query, department, top_k)` - 유사도 검색

### 5. pii_detector.py
- **역할**: 개인정보 탐지 및 업로드 차단
- **탐지 항목**: 주민등록번호, 전화번호, 이메일, 계좌번호, 신용카드
- **주요 메서드**:
  - `contains_critical_pii(text)` - 업로드 차단 여부 판단
  - `detect(text)` - 상세 탐지 결과 반환

### 6. cost_manager.py
- **역할**: 저장 비용 계산
- **주요 메서드**:
  - `calculate_daily_cost(file_size)` - 일일 저장 비용 계산

## 🔗 의존성
```
embedding.py → OpenAI API
auto_tagger.py → Google Gemini API
doc_chat.py → OpenAI API, db/milvus_client.py
rag_search.py → db/milvus_client.py, embedding.py
pii_detector.py → (외부 의존성 없음)
cost_manager.py → (외부 의존성 없음)
```
