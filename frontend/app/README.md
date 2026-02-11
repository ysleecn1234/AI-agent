# App Router (frontend/app)

Next.js 13+ App Router 기반의 페이지 및 라우팅 구조를 정의하는 디렉토리입니다.

## 📂 폴더 구조

```
app/
├── auth/           # 인증 관련 페이지
│   ├── login/      # 로그인 페이지
│   └── register/   # 회원가입 페이지
├── chat/           # 메인 채팅 인터페이스 페이지
├── drive/          # AI Drive (RAG 문서 관리) 페이지
│   └── documents/  # 문서 상세 및 채팅 페이지
├── agents/         # AI Agent Hub 페이지
├── settings/       # 사용자 설정 페이지
├── layout.tsx      # 전역 레이아웃 (폰트, 메타데이터 등)
├── globals.css     # 전역 스타일 (Tailwind CSS)
└── page.tsx        # 루트 페이지 (현재 로그인 페이지로 리다이렉트)
```

## 📝 주요 파일 설명

### `layout.tsx`
애플리케이션의 공통 레이아웃을 정의합니다. `Geist Sans`, `Geist Mono` 폰트를 로드하고 전역 스타일을 적용합니다.

### `chat/page.tsx`
핵심 기능인 **채팅 인터페이스**가 구현된 페이지입니다.
- 모델 선택 (GPT-5, Claude 등)
- 실시간 메시지 송수신 (API 연동 완료)
- 드라이브 저장 및 에이전트 생성 액션 제공

### `drive/page.tsx`
업로드된 문서 목록 조회, 검색 및 삭제(아카이브) 기능을 제공하며, RAG(검색 증강 생성) 채팅의 진입점입니다.
