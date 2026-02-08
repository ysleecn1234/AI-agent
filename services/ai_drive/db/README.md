# DB 모듈

AI 드라이브의 데이터베이스 연동을 담당하는 모듈입니다.

## 📂 파일 구조
```
db/
├── postgres_client.py   # PostgreSQL 클라이언트
└── milvus_client.py     # Milvus 벡터DB 클라이언트
```

## 📄 파일별 설명

### 1. postgres_client.py
- **역할**: 문서 메타데이터, 활동/비용 로그 관리
- **테이블**:
  - `documents` - 문서 메타데이터
  - `activity_logs` - 활동 로그 (업로드/삭제)
  - `cost_logs` - 비용 로그 (임베딩/저장/채팅)
- **주요 메서드**:
  - `create_document()` - 문서 생성
  - `get_document()` - 문서 조회
  - `update_document_status()` - 상태 업데이트
  - `log_activity()` - 활동 로그 기록
  - `log_cost()` - 비용 로그 기록

### 2. milvus_client.py
- **역할**: 문서 벡터 저장 및 유사도 검색
- **컬렉션**: `ai_drive_documents`
- **주요 메서드**:
  - `insert()` - 청크/벡터 저장
  - `search()` - 유사도 검색 (권한 필터 포함)
  - `search_by_doc_id()` - 특정 문서 내 검색
  - `delete_by_doc_id()` - 문서 삭제

## 🗄️ 데이터베이스 구성

### PostgreSQL (메타데이터)
```
포트: 5432
DB명: in7platform
유저: in7user
```

### Milvus (벡터DB)
```
포트: 19530
컬렉션: ai_drive_documents
차원: 1536 (OpenAI embedding)
인덱스: IVF_FLAT, COSINE
```

## 🔗 Docker 컨테이너
```bash
# 프로젝트 루트에서 실행
./deploy.sh

# 상태 확인
docker ps
```
