# 🚀 ISOR (Intelligent System for Optimized RAG)
> **비용 최적화형 차세대 AI 에이전트 및 RAG 파이프라인 플랫폼**

**ISOR**은 기존 엔터프라이즈 AI 시스템의 비효율적인 구조를 개선하여, **초저비용 오케스트레이션**과 **고효율 RAG 엔진**을 결합한 차세대 업무 환경 플랫폼입니다. 단순한 챗봇을 넘어, 사용자의 의도를 시스템 스스로 분석하고 최적의 가성비 모델 위치로 동적 라우팅하여 가장 합리적인 비용으로 고품질의 응답을 제공합니다.

---

## 💡 Project Background & Core Goals

단순히 똑똑한 AI를 구축하는 것을 넘어, **'운영 원가 절감(Cost-efficiency)'**과 **'실무 적용성(Practicality)'**에 기술적 초점을 두었습니다.

- 💰 **압도적인 비용 혁신**: 모든 텍스트 요청을 고비용 최신 모델로만 처리하는 기존 방식을 탈피했습니다.
- 🎯 **동적 모델 라우팅 (Model Slimming)**: 질문의 의도와 복잡도에 따라 경량 모델(Gemini Flash-lite 등)과 추론 모델(DeepSeek-R1, GPT-4o 등)을 동적으로 매핑하여 불필요한 API 과금을 획기적으로 차단합니다.
- 🤖 **에이전틱 워크플로우**: 단순 질의응답을 뛰어넘어 `[의도 분석 ➜ 전략 수립 ➜ 문서 검색 ➜ 생성 ➜ 검수]`의 파이프라인을 자율적으로 통과하는 에이전트 모델을 지향합니다.

---

## 🏗️ Core System Architecture

ISOR 시스템은 세 가지 핵심 마이크로서비스 모듈로 완벽하게 분리되어 유기적으로 동작합니다.

### 1. 🧠 Orchestrator (중앙 제어 시스템)
사용자의 최초 요청을 수신하고 의도(Intent)와 복잡도(Complexity)를 파악해 최적의 경로를 배차(Dispatch)하는 지능형 컨트롤 타워.
- **주요 기능**: Intent Classification, Dynamic Model Routing, Agent Schema Draft.

### 2. 🤖 AI Hub (에이전트 서비스 플랫폼)
목적에 맞는 특화된 사내 AI 에이전트를 자연어로 손쉽게 제작, 저장, 검색할 수 있는 플랫폼.
- **주요 기능**: 대화형 에이전트 생성 마법사(Agent Creation Wizard), Vector 기반 유사 에이전트 추천.

### 3. 📂 AI Drive (통합 지식 저장소 & RAG)
PDF, TXT 등 기업의 문서 데이터를 밀리초 단위로 파악하는 지식 저장소 및 SLM 파이프라인 구동계.
- **주요 기능**: Chunking & Embedding, Vector Semantic Search (Milvus).

---

## 🛠️ 5-Step SLM Pipeline (핵심 정보 처리 과정)

ISOR의 가장 특징적인 로직은 답변 무결성과 비용 낭비 최소화를 위해 설계된 **5단계의 치밀한 검증 레이어**(`services/orchestrator/pipeline.py`)입니다.

1. 🔀 **Router**: 요청의 성격을 분석하고, 복잡도(SIMPLE, COMPLEX) 계산을 통해 맞춤형 모델 분배.
2. 🔍 **Researcher**: AI Drive(Milvus)에 접근하여 질문과 의미적으로 근접한 최상위 관련 문서 확보.
3. ⚙️ **Reasoner**: 추출된 문서를 기반으로 질문에 대한 구체적이고 논리적인 답변 초안 작성 (환각 방지 기술 적용).
4. ✍️ **Synthesizer**: 로우 데이터를 가독성 높은 맞춤형 마크다운 및 표 형태로 최종 디자인 렌더링.
5. 🛡️ **Guardrail**: 주민번호 등 PII 데이터 블라인드 마스킹, 유해 콘텐츠 차단 및 메타 정보 노출 방지 (API 비용 0원의 자체 Regex 기반 검사 연동).

---

## 💻 Tech Stack

- **LLM/SLM**: Gemini 1.5 Flash-lite (고속 라우팅 및 Guardrail), GPT-4o-mini (주요 답변), DeepSeek-R1 (고난도 추론)
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Backend / API**: FastAPI (Python 3.11)
- **Database**: 
  - **PostgreSQL 15+** : 메타데이터 및 회원/권한 관리 RDBMS
  - **Milvus 2.3+** : 초고속 Vector 임베딩 데이터 쿼리용 Standalone DB
- **Infrastructure**: Docker & Docker Compose (완전한 컨테이너 환경 격리 및 배포)

---

## 🚀 Quick Start (빠른 실행 가이드)

ISOR 프로젝트는 도커 환경으로 컨테이너화되어 있어 누구나 쉽게 실행할 수 있습니다.

### 1. 환경 변수 설정
프로젝트 최상단 디렉토리에 `.env` 파일을 복사하여 생성하고, 필수 API 키를 입력합니다.
```bash
cp .env.template .env
# 편집기로 .env 파일을 열고 OPENAI_API_KEY, GOOGLE_API_KEY 등 입력
```

### 2. 인프라 실행 (DB 및 서버 전체 배포)
디바이스 내 Docker가 실행되어 있는 상태에서, 내장된 쉘 스크립트를 통해 시스템 로딩을 시작합니다.
```bash
# 실행 권한 부여 후 배포 처리
chmod +x deploy.sh
./deploy.sh
```

### 3. 접속 및 테스트
- **API 도큐먼트 (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **서버 헬스 체크**: [http://localhost:8000/health](http://localhost:8000/health)

> **💡 개발 / Mock Mode 관련 안내**  
> 인프라나 DB(Milvus 등) 연결이 단절되거나 실패하는 상황에서는, 프론트 서버 다운을 방지하기 위해 자체적인 예외 처리를 뱉고 빈 문서를 활용해서라도 시스템 자율 지식 기반으로 답변하도록 방어 로직이 갖춰져 있습니다.


