# ISOR — 비용 최적화형 RAG·AI 에이전트 플랫폼

사용자의 질문 의도와 복잡도에 따라 **적절한 등급의 언어모델로 요청을 동적으로 라우팅**하고, 사내 문서를 검색해 답변하는 **RAG(검색 증강 생성) 기반 AI 에이전트 플랫폼**입니다. 기업 과제로 진행한 팀 프로젝트의 프로토타입입니다.

> RAG(Retrieval-Augmented Generation): 언어모델이 답을 생성하기 전에 관련 문서를 먼저 검색해 근거로 활용하는 방식. 최신 정보 반영과 환각(hallucination) 감소에 쓰입니다.

---

## 배경 / 문제 정의

기업의 AI 시스템은 모든 요청을 고성능·고비용 모델로 처리하면 API 비용이 빠르게 늘어납니다. ISOR은 이 문제에 초점을 맞춰, 요청의 의도와 복잡도를 먼저 분석한 뒤 간단한 요청은 경량 모델로, 복잡한 요청은 고성능 모델로 나눠 보내는 구조를 실험했습니다. 여기에 사내 문서를 검색해 답하는 RAG 파이프라인과, 자연어로 특화 에이전트를 만드는 기능을 결합했습니다.

## 사용 기술

- **백엔드 / API**: Python 3.11, FastAPI
- **데이터베이스**: PostgreSQL(회원·권한·메타데이터), Milvus(문서 임베딩을 저장·검색하는 벡터 데이터베이스)
- **임베딩 / LLM 연동**: OpenAI `text-embedding-3-small`(문서·질문을 벡터로 변환), 요청 성격에 따라 경량 모델과 고성능 모델을 나눠 호출하는 다중 LLM 라우팅
- **의도 분류**: scikit-learn 기반 의도 분류 모델(학습 데이터·적대적 테스트셋 포함, `services/orchestrator/`)
- **프론트엔드**: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui
- **인프라**: Docker, Docker Compose 기반 컨테이너 환경

## 프로젝트 구조

세 개의 마이크로서비스로 분리되어 있으며, 요청은 Orchestrator를 거쳐 처리됩니다.

```
services/
  ├─ orchestrator/     # ① 중앙 제어: 의도 분류 + 모델 라우팅
  │    ├─ pipeline.py         # 5단계 처리 파이프라인
  │    ├─ models/             # 학습된 의도 분류 모델(.pkl)
  │    └─ data/               # 의도 분류 학습·테스트 데이터
  ├─ ai_hub/           # ② 에이전트 플랫폼: 자연어로 에이전트 생성·검색
  │    └─ core/agent/         # 에이전트 생성·스키마·관리
  └─ ai_drive/         # ③ 지식 저장소(RAG): 문서 처리·벡터 검색
       └─ core/                # 청킹·임베딩·RAG 검색·PII 탐지·자동 태깅

api/                   # FastAPI 엔드포인트(chat, agents, drive, auth 등)
application/           # 서비스 계층(usecases: ai_agent, ai_drive, ai_hub, orchestrator)
frontend/              # Next.js 웹 UI(채팅, 에이전트 생성, 문서 관리, 관리자)
docker/                # Dockerfile · docker-compose
tests/                 # 통합 테스트
```

**핵심 처리 흐름 — Orchestrator의 5단계 파이프라인** (`services/orchestrator/pipeline.py`)

1. **Router** — 요청의 의도와 복잡도(단순/복잡)를 판단해 처리할 모델을 결정
2. **Researcher** — AI Drive(Milvus)에서 질문과 의미적으로 가까운 문서를 검색
3. **Reasoner** — 검색된 문서를 근거로 답변 초안을 작성(환각 억제)
4. **Synthesizer** — 초안을 읽기 좋은 마크다운·표 형태로 정리
5. **Guardrail** — 주민번호 등 개인정보(PII) 마스킹, 유해 콘텐츠 차단(정규표현식 기반 자체 검사)

> 세부 실행·배포 방법은 저장소 내 `docker/`와 각 서비스의 `README.md` 문서를 참고하세요.

## 결과 / 산출물

기업 과제로 제출을 완료한 **동작하는 프로토타입**입니다. 이번 단계의 목표는 비용 절감률이나 정확도 같은 특정 지표 달성이 아니라, **"의도 기반 모델 라우팅 + RAG + 에이전트 생성"을 결합한 시스템을 팀이 실제로 구현하고 배포까지 할 수 있는가**를 검증하는 것이었습니다.

- 세 개 마이크로서비스(Orchestrator / AI Hub / AI Drive)와 웹 UI를 갖춘 전체 시스템을 구현하고, Docker 컨테이너 환경으로 통합해 **배포·시연**했습니다.
- 5단계 파이프라인, 벡터 검색 기반 RAG, 자연어 에이전트 생성, PII 마스킹 등 핵심 기능이 실제로 연동되어 동작함을 확인했습니다.
- 정량적 성능 지표(비용 절감·분류 정확도 등) 측정은 이번 프로토타입 범위에 포함하지 않았으며, 향후 과제로 남겨두었습니다.

 ## **현재 안전성을 위해서 develop 브렌치에 작업물이 있습니다.**
