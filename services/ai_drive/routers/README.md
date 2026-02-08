# Routers 모듈

AI 드라이브의 API 엔드포인트를 담당하는 모듈입니다.

## 📂 파일 구조
```
routers/
└── documents.py   # 문서 관련 API
```

## 📄 파일별 설명

### documents.py
- **역할**: 문서 업로드/조회/삭제/검색 API

## 🔗 API 엔드포인트

### 문서 업로드
```
POST /api/drive/documents/upload
- 파일 업로드 → 파싱 → 청킹 → 임베딩 → 저장
- 개인정보 포함 시 차단
```

### 문서 목록 조회
```
GET /api/drive/documents/
- 부서/상태/공개범위 필터링
```

### 문서 상세 조회
```
GET /api/drive/documents/{doc_id}
```

### 문서 삭제
```
DELETE /api/drive/documents/{doc_id}
- Soft Delete (상태를 archived로 변경)
```

### RAG 검색
```
POST /api/drive/documents/search
- 자연어 쿼리 → 유사 문서 검색
```

### 문서별 채팅
```
POST /api/drive/documents/{doc_id}/chat
- 특정 문서에 대한 질문/답변
```

### 채팅 결과 저장
```
POST /api/drive/documents/save-chat
```

### 에이전트 결과 저장
```
POST /api/drive/documents/save-agent
```
