# TypeScript Type Definitions (frontend/types)

애플리케이션 전반에서 사용되는 데이터 모델과 인터페이스를 정의한 디렉토리입니다.

## 📂 파일 설명

### `api.ts`
백엔드 API의 요청(Request) 및 응답(Response) 형식을 정의합니다.
- `LoginRequest`, `AuthResponse`: 로그인/회원가입 관련
- `ChatRequest`, `ChatResponse`: 채팅 메시지 관련
- `Document`: AI Drive 문서 정보
- `Agent`: AI 에이전트 정보

### `agent.ts`
프론트엔드 UI/비즈니스 로직에서 사용되는 에이전트 객체의 상세 타입을 정의합니다. (일부 `api.ts`와 겹칠 수 있으나, UI 전용 속성이 추가될 수 있음)

> **Tip**: 백엔드 Pydantic 모델 변경 시, 이 곳의 타입 정의도 함께 업데이트하여 동기화를 유지해야 합니다.
