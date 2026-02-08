# Core Pipeline 개발 현황

> **최종 업데이트**: 2026-01-31  
> **담당자**: 권영민  
> **브랜치**: feature-Y

---

## ✅ 완료된 작업

### 1. Core Pipeline (5단계 레이어) 구현 완료
**기간**: 2026-01-30 ~ 2026-01-31

#### Router (Step 1)
- ✅ 하이브리드 의도 분류 (키워드 + LLM)
- ✅ 다차원 복잡도 판단 (길이, 의도, 키워드, 구조)
- ✅ 신뢰도 기반 LLM 호출 최적화

#### Researcher (Step 2)
- ✅ RAG 검색 인터페이스 구현
- ✅ `use_rag` 플래그 추가 (Mock/실제 RAG 전환)
- ✅ Mock 검색 기능 (API 없이 테스트 가능)
- ✅ 실제 RAG 검색 로직 (AI Drive 연동 준비)
- ✅ 에러 핸들링 및 폴백 메커니즘

#### Reasoner (Step 3)
- ✅ 복잡도별 모델 매핑 (Simple: Gemini Flash, Complex: GPT-5, Bulk: Claude 4)
- ✅ Fallback 메커니즘 (모델별 우선순위)
- ✅ 팩트체크 및 검증 로직

#### Synthesizer (Step 4)
- ✅ 마크다운 기반 응답 포맷팅
- ✅ 신뢰도 및 모델 정보 표시

#### Guardrail (Step 5)
- ✅ 민감 정보 마스킹 (전화번호, 주민등록번호)
- ✅ 품질 검수 (Complex/Bulk 쿼리)
- ✅ 안전성 검사

---

### 2. 지원 시스템

#### Logger
- ✅ 세션 기반 로깅
- ✅ 단계별 처리 시간 추적
- ✅ 모델 사용 로그
- ✅ 에러 로깅

#### Cost Calculator
- ✅ 모델별 비용 계산
- ✅ IN7 대비 절감액 계산
- ✅ 토큰 수 기반 비용 추정

---

### 3. AI Drive 연동 준비

#### Feature-H 분석
- ✅ AI Drive 파트 구조 분석 완료
- ✅ 핵심 컴포넌트 분석 (파싱, 청킹, 임베딩, DB)
- ✅ 분석 리포트 작성 ([ai_drive_analysis.md](./ai_drive_analysis.md))

#### Researcher 개선
- ✅ `use_rag` 플래그로 Mock/실제 RAG 전환 가능
- ✅ Mock 검색 기능 (테스트용 더미 데이터)
- ✅ 실제 RAG 검색 로직 (Milvus + 임베딩)
- ✅ 에러 시 Mock으로 폴백

---

### 4. 테스트

#### 통합 테스트
- ✅ 테스트 코드 작성 (`tests/test_pipeline_integration.py`)
- ✅ 5개 테스트 케이스 작성 및 통과
  - Simple 쿼리 (RAG 검색 스킵)
  - Complex 쿼리 (Mock 검색 실행)
  - Generation 쿼리
  - 품질 검수 (Complex)
  - 복잡도 레벨 판정

**테스트 결과**:
```
[SUCCESS] 모든 테스트 통과!
- Simple 쿼리: ✓
- Complex 쿼리: ✓ (Mock 검색 2개 문서)
- Generation 쿼리: ✓
- 품질 검수: ✓
- 복잡도 레벨: ✓
```

---

## 🚧 진행 중

### 1. 실제 LLM API 연동
**상태**: 대기 중 (API 키 필요)

**작업 내용**:
- [ ] `.env` 파일 생성 및 API 키 설정
- [ ] Reasoner에서 실제 LiteLLM 호출
- [ ] Fallback 메커니즘 테스트
- [ ] 비용 추적 검증

### 2. AI Drive RAG 시스템 연동
**상태**: 준비 완료 (Docker 환경 필요)

**작업 내용**:
- [ ] Docker Compose 실행 (Milvus + PostgreSQL)
- [ ] `use_rag=True`로 실제 RAG 검색 테스트
- [ ] 검색 품질 검증
- [ ] 권한 필터링 테스트

---

## 📋 다음 단계

### Phase 1: API 연동 (1-2일)
1. **환경 설정**
   - [ ] `.env` 파일 생성
   - [ ] API 키 설정 (OpenAI, Google, Anthropic)
   - [ ] 환경 변수 로드 확인

2. **LLM 연동**
   - [ ] Reasoner에서 실제 API 호출
   - [ ] 각 모델별 테스트 (Gemini, GPT, Claude)
   - [ ] Fallback 메커니즘 검증
   - [ ] 에러 핸들링 테스트

3. **비용 추적**
   - [ ] 실제 토큰 수 계산
   - [ ] 비용 로그 검증
   - [ ] IN7 대비 절감액 확인

### Phase 2: RAG 연동 (1일)
1. **Docker 환경**
   - [ ] `docker-compose up -d` 실행
   - [ ] Milvus 연결 확인
   - [ ] PostgreSQL 연결 확인

2. **RAG 테스트**
   - [ ] 테스트 문서 업로드
   - [ ] `use_rag=True`로 검색 테스트
   - [ ] 검색 결과 품질 확인
   - [ ] 권한 필터링 검증

### Phase 3: 통합 테스트 (1일)
1. **전체 플로우**
   - [ ] Simple 쿼리 (실제 LLM)
   - [ ] Complex 쿼리 (실제 RAG + LLM)
   - [ ] Bulk 쿼리 (대량 문서 처리)

2. **성능 측정**
   - [ ] 응답 시간 측정
   - [ ] 비용 분석
   - [ ] 병목 지점 파악

### Phase 4: 최적화 (1-2일)
1. **성능 개선**
   - [ ] 캐싱 전략 (동일 쿼리 재검색 방지)
   - [ ] 배치 처리 최적화
   - [ ] 병렬 처리 개선

2. **비용 최적화**
   - [ ] 불필요한 LLM 호출 제거
   - [ ] 모델 선택 로직 개선
   - [ ] 토큰 사용량 최적화

---

## 📊 기술 스택

### Core Pipeline
- **언어**: Python 3.14+
- **LLM 오케스트레이션**: LiteLLM
- **로깅**: 커스텀 Logger
- **비용 계산**: 커스텀 Cost Calculator

### AI Drive (Feature-H)
- **임베딩**: OpenAI text-embedding-3-small
- **벡터 DB**: Milvus 2.3.4
- **메타데이터 DB**: PostgreSQL 15
- **파일 파싱**: PyMuPDF, python-docx, python-pptx
- **텍스트 처리**: tiktoken

### 테스트
- **프레임워크**: Python unittest
- **Mock 데이터**: 커스텀 Mock 검색

---

## 🔗 관련 문서

- [AI Drive 분석 리포트](./ai_drive_analysis.md)
- [Core-AI Drive 연동 계획](../brain/4a54172d-0007-46ac-879c-67b4168cb9db/implementation_plan.md)
- [프로젝트 README](../README.md)

---

## 📝 변경 이력

### 2026-01-31
- ✅ Researcher 클래스 리팩토링 (use_rag 플래그 추가)
- ✅ Mock 검색 기능 구현
- ✅ 통합 테스트 코드 작성 및 실행
- ✅ README 업데이트 (Mock 검색 설명 추가)
- ✅ 개발 현황 문서 분리

### 2026-01-30
- ✅ Core Pipeline 5단계 레이어 구현
- ✅ Logger 시스템 구현
- ✅ Cost Calculator 구현
- ✅ Router 단위 테스트 작성
