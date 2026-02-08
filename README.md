# AI-agent  
🚀 on7 기반 비용 최적화형 AI 에이전트 프로토타입  
기존 '인세븐(IN7)'의 업무 워크플로우를 벤치마킹하여, 초저비용 오케스트레이션과 고효율 RAG 엔진을 결합한 차세대 AI 업무 환경 프로토타입입니다.  

💡 Project Background & Goal  
단순히 똑똑한 AI를 만드는 것을 넘어, **'운영 원가 절감'**과 **'실무 적용성'**에 집중했습니다.  
비용 혁신: 기존 모델 공급사 대비 높은 운영 마진 체계를 개선하여, 운영 비용을 30% 이상 추가 절감합니다.  

모델 슬림화: 21종의 복잡한 모델 라인업을 '티어별 라우팅'으로 최적화하여 관리 효율을 극대화합니다.  
에이전틱 워크플로우: 단순 챗봇을 넘어 [분석-작성-검수] 과정을 스스로 수행하는 시스템을 지향합니다.  

## 🏗️ Core System Architecture  
본 프로젝트는 3가지 핵심 마이크로서비스 모듈로 구성됩니다. 각 폴더의 **README.md**에서 상세 로직을 확인할 수 있습니다.

1.  **[Orchestrator (The Brain)](./services/orchestrator/README.md)**:  
    *   사용자의 의도를 분석하고 `AI Hub` 또는 `AI Drive`로 작업을 분배하는 중앙 제어 장치입니다.
    *   **핵심 기능**: Intent Analysis, Dynamic Routing, JSON Schema Generation.

2.  **[AI Hub (Agent Service)](./services/ai_hub/README.md)**:  
    *   나만의 에이전트를 생성(Draft -> Publish)하고 검색(RAG)하는 플랫폼입니다.
    *   **핵심 기능**: Agent Creation Wizard, Vector Search, Metadata Management.

3.  **[AI Drive (Knowledge Base)](./services/ai_drive/README.md)**:  
    *   문서를 업로드하고 RAG 기반으로 질의응답을 수행하는 지식 저장소입니다.
    *   **핵심 기능**: 5-Step SLM Pipeline (Router -> Researcher -> Reasoner -> Synthesizer -> Guardrail).

4.  **Admin Dashboard**: 전체 서비스의 사용량과 비용 로그를 실시간으로 통합 관리합니다.  

---

## 🛠️ Key Technical Features  

### 1. 5단계 레이어드 파이프라인 (SLM Pipeline)
모든 문서 질의 요청은 성능과 비용 최적화를 위해 설계된 5단계 레이어를 거칩니다. (`ai_drive/core/doc_chat.py`)

*   **Step 1. Router**: 의도 분류 및 복잡도 판단 (Gemini Flash).
*   **Step 2. Researcher**: Milvus 기반 벡터 검색 및 관련 청크 추출.
*   **Step 3. Reasoner**: GPT-4o-mini를 활용한 정밀 답변 생성.
*   **Step 4. Synthesizer**: 마크다운 포맷팅 및 답변 정제.
*   **Step 5. Guardrail**: 개인정보 마스킹 및 최종 안전 검증.

### 2. 지능형 에이전트 생성 (Agent Wizard)
사용자와의 대화를 통해 에이전트 명세서를 자동으로 완성합니다. (`ai_hub/core/agent/manager.py`)

*   **Analyze**: 사용자의 자연어 요청을 Orchestrator가 분석하여 JSON 스키마로 변환.
*   **Vectorize**: 에이전트 특성을 임베딩하여 의미 기반 검색 지원.

---

## 💻 Tech Stack  
*   **LLM/SLM**: Gemini 1.5 Flash (Router/Draft), GPT-4o-mini (Reasoner).
*   **Embeddings**: OpenAI text-embedding-3-small.  
*   **Database**: PostgreSQL 15+ (Metadata), Milvus 2.3+ (Vector Attributes).  
*   **Infrastructure**: Docker Compose (Microservices Architecture).

---

## 👨‍💻 개발 매뉴얼 (Development Manual)

### 1. 가상환경 설정 (Virtual Environment Setup)
```bash
# Mac/Limit
python3 -m venv venv && source venv/bin/activate

# Windows
python -m venv venv && .\venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 담당 파트 및 작업 경로 (Roles & Paths)
*   **권영민** (`services/orchestrator/`): LLM 오케스트레이션 엔진 및 라우팅 로직.
*   **이지석** (`services/ai_hub/`): 에이전트 생성 마법사 및 허브 검색 시스템.
*   **송호성** (`services/ai_drive/`): RAG 시스템 및 문서 관리 파이프라인.

---

## 🚀 빠른 시작 (Quick Start)

### 1. Docker 실행 (필수)
DB(Postgres, Milvus, Redis)를 실행합니다.
```bash
./deploy.sh
# 또는
docker-compose up -d
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 API 키를 입력하세요.
```bash
cp .env.template .env
# OPENAI_API_KEY, GOOGLE_API_KEY 입력
```

### 3. 서버 실행
```bash
python -m application.main
```
*   **API 문서**: [http://localhost:8000/docs](http://localhost:8000/docs)

> **💡 참고: Mock 모드**  
> API 키가 없거나 DB 연결 실패 시, 시스템은 자동으로 **Mock Mode(테스트 모드)**로 동작하여 개발 편의성을 제공합니다.
> (단, 실제 RAG 품질 확인을 위해서는 API 키 설정이 필수입니다.)

---

## 🏗️ Project Infrastructure Files (Root)

이 프로젝트를 실행하고 배포하기 위한 핵심 인프라 파일들입니다.

*   **`deploy.sh`**: [Deployment Script] 서버에서 Git Pull -> Docker Build -> Docker Up 과정을 한 번에 수행하는 배포 자동화 스크립트입니다.
*   **`docker-compose.yml`**: [Container Orchestration] App, PostgreSQL, Redis, Milvus(Standalone) 컨테이너를 정의하고 네트워크로 연결하는 설정 파일입니다.
*   **`Dockerfile`**: [App Image] Python 3.11 환경에서 Fastapi 서버를 실행하기 위한 도커 이미지 빌드 명세서입니다.
*   **`requirements.txt`**: [Dependencies] 프로젝트 실행에 필요한 Python 패키지 목록입니다. (Litellm, Fastapi, Pymilvus 등 포함)

---

## 🚀 How to Run (실행 방법)

서버를 실행하려면 다음 단계를 따라주세요.

1.  **Docker 실행:** Mac의 `Applications` > `Docker` 앱을 클릭하여 실행합니다. (상단 메뉴바에 고래 아이콘 확인)
2.  **배포 스크립트 실행:** 터미널에서 다음 명령어를 입력하세요.
    ```bash
    ./deploy.sh
    ```
3.  **접속:** 잠시 후 로그가 멈추면 브라우저에서 아래 주소로 접속합니다.
    *   **API 문서:** [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **헬스 체크:** [http://localhost:8000/health](http://localhost:8000/health)

---
