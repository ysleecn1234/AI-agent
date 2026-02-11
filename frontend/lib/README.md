# Utilities & Services (frontend/lib)

애플리케이션 전반에서 사용되는 유틸리티 함수와 비즈니스 로직(서비스)을 모아둔 디렉토리입니다.

## 📂 파일 설명

### `api.ts`
백엔드 API와의 통신을 전담하는 클라이언트 모듈입니다.
- `fetch` API 기반 래퍼 클래스 (`ApiClient`)
- JWT 토큰 기반 인증 관리 (자동 헤더 주입)
- `login`, `sendMessage`, `saveChatToDrive` 등 주요 API 메서드 제공

### `utils.ts`
범용 유틸리티 함수들의 모음입니다.
- `cn`: Tailwind CSS 클래스 조건부 병합 (clsx + tailwind-merge)
- 날짜 포맷팅 등 헬퍼 함수

### `services.ts` (Legacy)
초기 프로토타입 단계에서 사용되던 Mock 데이터 서비스입니다. 현재는 `api.ts`로 대체되어 실제 백엔드 연동에 사용되지 않을 수 있습니다.
