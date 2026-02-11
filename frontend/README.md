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
