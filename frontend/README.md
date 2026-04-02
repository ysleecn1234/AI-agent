# AI-Agent Frontend

이 디렉토리는 AI-Agent 프로젝트의 사용자 인터페이스를 담당하는 Next.js 애플리케이션입니다.

## 🛠️ 기술 스택
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS, Shadcn/UI
- **Icons**: Lucide React

## 📂 폴더 구조 및 주요 변경 사항

현재까지 구현된 주요 기능과 파일 구조에 대한 설명입니다.

### 1. `app/` (페이지)
- **`/auth`**: 로그인 및 회원가입 페이지
  - `login/page.tsx`: 이메일/비밀번호 로그인 폼 (백엔드 API 연동 준비)
  - `register/page.tsx`: 회원가입 폼
- **`/chat`**: 메인 채팅 인터페이스 (핵심 기능)
  - `page.tsx`:
    - 사이드바(Sheet) 네비게이션 구현
    - 메시지 버블 UI (User/AI 구분)
    - 모델 선택 기능 (GPT-5, Claude 등)
    - '드라이브 저장', '에이전트 생성' 퀵 액션 버튼 추가
- **`/drive`**: AI Drive (RAG 문서 관리)
  - `page.tsx`: 업로드된 문서 목록 조회 및 검색
  - `documents/[id]/page.tsx`: 문서 상세 보기 및 문서 기반 Q&A (Split View)
- **`/agents`**: Agent Hub
  - `page.tsx`: 사용 가능한 에이전트 목록 카드 뷰
  - `create/`: 에이전트 생성 마법사 (Step 1, 2)
- **`/settings`**: 설정 페이지
  - `page.tsx`: 개인정보 보호 및 계정 설정 관리

### 2. `components/` (UI 컴포넌트)
- **`ui/`**: Shadcn/UI 기반의 재사용 가능한 원자(Atomic) 컴포넌트들
  - `button.tsx`, `input.tsx`, `card.tsx` 등
- **`chat-action-modals.tsx`**: 채팅 화면에서 사용되는 팝업 모달
  - `SaveToDriveModal`: 대화 내용을 문서로 저장하는 모달
  - `CreateAgentModal`: 대화 내용을 바탕으로 에이전트를 생성하는 모달

### 3. `lib/` (유틸리티 및 통신)
- **`api.ts`** (New!): 백엔드 API와의 통신을 담당하는 클라이언트 모듈
  - 인증 토큰 자동 관리
  - 로그인, 채팅, 드라이브, 에이전트 관련 API 메서드 제공
- **`utils.ts`**: 클래스 이름 병합(cn) 등 유틸리티 함수

### 4. `types/` (타입 정의)
- **`api.ts`**: API 요청/응답 데이터의 타입 인터페이스 정의
- **`agent.ts`**: 에이전트 관련 타입 정의

## 🚀 실행 방법

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)으로 접속하여 확인하세요.

## ✅ 최근 작업 내역 (Changelog)

- **feat: 문서 메타데이터 수정 기능 추가 (2026-02-12)**
  - API 클라이언트에 updateDocumentMetadata() 메서드 추가
    - `PATCH /drive/documents/{id}` 연동
  - 문서 상세 페이지에 수정 버튼 추가
  - 수정 모달 구현
    - 제목, 설명, 공개범위, 태그 수정 가능
    - 실시간 수정 반영
  - UpdateDocumentMetadataRequest 타입 정의 추가
- **refactor: 프론트엔드 로직을 백엔드 API 호출로 교체 (2026-02-12)**
  - API 클라이언트에 새로운 엔드포인트 추가
    - `POST /generate/document-metadata` - 문서 제목/설명 생성
    - `POST /generate/agent-metadata` - Agent 정보 생성
    - `GET /agents/recommend?query={query}` - Agent 추천
  - 모달에서 하드코딩된 로직 제거
    - LLM 제목/설명 생성 → API 호출로 교체
    - 카테고리 감지 로직 → API 호출로 교체
    - Fallback 로직 유지 (API 실패 시)
  - Agent 추천 로직 개선
    - 백엔드 추천 API 우선 사용
    - API 실패 시 클라이언트 필터링 Fallback
  - 프론트엔드 역할 명확화
    - UI/UX + API 연동만 담당
    - 비즈니스 로직은 백엔드로 이동
- **feat: 문서/Agent 생성 모달 개선 (2026-02-12)**
  - 문서 저장 모달 향상
    - LLM 자동 제목/설명 생성 (백엔드 API)
    - 편집 가능한 제목/설명 필드
    - 공개 범위 선택 (나만/팀/전체)
    - 미리보기 토글 (접기/펼치기)
    - 저장 범위 선택 (이 답변/전체 대화)
  - Agent 생성 모달 향상
    - LLM 자동 정보 생성 (이름, 설명, 카테고리)
    - 8개 카테고리 선택 (생산성/마케팅/개발 등)
    - 공개 범위 선택
    - 학습 데이터 미리보기
    - 학습 범위 선택 (이 답변/전체 대화)
  - 모달 UI/UX 개선
    - 최대 높이 제한 + 스크롤
    - 로딩 상태 표시 (Loader2 spinner)
    - 필수 필드 유효성 검사
- **feat: Agent 활성화 및 실시간 추천 기능 구현 (2026-02-12)**
  - Agent 활성화 체크박스 추가
  - 500ms 디바운스로 실시간 Agent 추천
    - 입력 없을 때: TOP 5 Agent 표시
    - 입력 있을 때: 키워드 기반 관련 Agent 추천
  - Agent 선택 UI
    - 선택한 Agent는 입력창 위에 배지로 표시
    - X 버튼으로 선택 해제 가능
  - Agent 추천 카드 (pill 형태 버튼)
    - 선택된 Agent는 파란색 배경으로 강조
- **feat: 채팅 메시지 인터랙션 개선 (2026-02-12)**
  - 복사 버튼 추가 (클립보드 복사 + 2초 피드백)
  - 좋아요 버튼 추가 (토글 기능, 파란색 하이라이트)
  - RAG 참조 문서 표시
    - 문서 제목, 유사도 점수 표시
    - 클릭 시 문서 상세 페이지로 이동
  - 액션 버튼 레이아웃 개선 (복사/좋아요/저장/Agent생성)
- **feat: Agent Hub 개선 및 프리미엄 모델 지원 추가 (2026-02-12)**
  - Agent 목록 실제 API 연동 (GET /agents)
  - Agent 삭제 기능 구현 (DELETE /agents/{id})
  - 카테고리 필터 추가 (생산성, 마케팅, 개발, 기획, 영업, 인사, 재무, 기타)
  - Agent 카드 UI 개선 (카테고리 배지, 공개범위 표시)
  - 채팅 페이지에 프리미엄 모델 선택 추가
    - GPT 5.4 Pro (Thinking), Gemini 3.1 Pro, Perplexity Sonar Pro, Claude Opus 4.6
  - User 메뉴 추가 (헤더 우측 상단)
- **merge: develop 브랜치 병합 (2026-02-12)**
  - 백엔드 최신 업데이트 반영 (프리미엄 모델, 문서 메타데이터 수정 등)
- **feat: 설정 페이지 구현 (2026-02-12)**
  - 개인정보 보호 설정 (자동 차단/마스킹 선택)
  - 감지 항목 체크박스 (주민번호, 전화번호, 이메일, 신용카드, 계좌번호, 주소)
  - 계정 설정 (이름, 이메일, 부서 표시 및 수정)
  - API 연동 준비 (GET /settings, PUT /settings)
- **fix: 채팅 페이지 사이드바 네비게이션 개선 (2026-02-11)**
  - 아카이브 메뉴 추가 (AI Drive와 Agent Hub 사이)
  - 현재 활성 페이지 강조 표시 (채팅 페이지 bg-blue-50)
  - Archive 아이콘 import 추가
- **feat: 프론트엔드 초기 구조 세팅**
  - Next.js + Tailwind CSS + Shadcn/UI 환경 설정
  - 주요 페이지(Chat, Drive, Agents, Auth) 라우팅 및 껍데기(UI) 구현
- **feat: API 클라이언트 모듈 구현 (`lib/api.ts`)**
  - 백엔드와 통신하기 위한 Axios 대체(Fetch API) 래퍼 구현
  - 토큰 기반 인증 로직 추가
- **docs: 프로젝트 문서화**
  - README.md 한글화 및 구조 상세 설명 추가
- **feat: 채팅 화면 API 연동**
  - 메시지 전송(sendMessage), 드라이브 저장(saveChatToDrive), 에이전트 생성(createAgentDraft) API 연결
  - 로그인 정보(localStorage)를 활용한 사용자 컨텍스트 주입
- **feat: AI Drive (문서 관리) 백엔드 연동**
  - 문서 목록 조회(GET) 및 삭제(DELETE) 실제 API 연결
  - 파일 업로드(POST) 기능 구현 및 연동 (`upload-modal.tsx`)
