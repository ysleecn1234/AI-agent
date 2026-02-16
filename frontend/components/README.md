# UI Components (frontend/components)

이 디렉토리는 애플리케이션 전반에서 사용되는 재사용 가능한 UI 컴포넌트들을 포함합니다.

## 📂 폴더 구조

```
components/
├── ui/                 # Shadcn/UI 기반 Atomic 컴포넌트
│   ├── button.tsx      # 버튼
│   ├── card.tsx        # 카드 컨테이너
│   ├── input.tsx       # 텍스트 입력 필드
│   ├── sheet.tsx       # 사이드바/모달 시트
│   └── ...
└── chat-action-modals.tsx # 채팅 관련 특수 모달 컴포넌트
```

## 📝 주요 컴포넌트 설명

### `ui/` (Shadcn/UI)
Tailwind CSS와 Radix UI를 기반으로 구축된 디자인 시스템 컴포넌트들입니다. 일관된 디자인과 접근성을 보장합니다.

### `chat-action-modals.tsx`
채팅 화면에서 사용되는 복합적인 기능을 가진 모달들입니다.
- **SaveToDriveModal**: 특정 대화 내용을 AI Drive에 문서로 저장하는 팝업
- **CreateAgentModal**: 대화 내용을 프롬프트 삼아 새로운 AI 에이전트를 생성하는 팝업
