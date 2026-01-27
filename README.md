# AI-agent  
🚀 on7 기반 비용 최적화형 AI 에이전트 프로토타입  
기존 '인세븐(IN7)'의 업무 워크플로우를 벤치마킹하여, 초저비용 오케스트레이션과 고효율 RAG 엔진을 결합한 차세대 AI 업무 환경 프로토타입입니다.  

💡 Project Background & Goal  
단순히 똑똑한 AI를 만드는 것을 넘어, **'운영 원가 절감'**과 **'실무 적용성'**에 집중했습니다.  
비용 혁신: 기존 모델 공급사 대비 높은 운영 마진 체계를 개선하여, 운영 비용을 30% 이상 추가 절감합니다.  

모델 슬림화: 21종의 복잡한 모델 라인업을 '티어별 라우팅'으로 최적화하여 관리 효율을 극대화합니다.  
에이전틱 워크플로우: 단순 챗봇을 넘어 [분석-작성-검수] 과정을 스스로 수행하는 시스템을 지향합니다.  

🏗️ Core System Architecture  
본 프로젝트는 4가지 핵심 모듈로 구성됩니다.  
Orchestrator (The Brain): 작업의 복잡도를 판단하고 최적의 LLM을 배분하는 지능형 엔진입니다.

Custom AI Agent (Agent Hub): 사용자가 대화만으로 자신만의 에이전트를 생성하고 팀원과 공유하는 저장소입니다.

AI Drive (Knowledge Base): 문서 관리와 지식 처리를 통합 수행하며, RAG 검색의 기반이 되는 중앙 저장소입니다.

Admin Dashboard: 전체 서비스의 사용량과 비용 로그를 실시간으로 통합 관리합니다.  

🛠️ Key Technical Features  
1. 5단계 레이어드 파이프라인  
모든 요청은 성능과 비용을 모두 잡기 위해 설계된 5단계 레이어를 거칩니다.

Step 1. Router: 의도 분류 및 복잡도 판단.  

Step 2. Researcher: RAG 기반 문서 검색 및 정보 인출.  

Step 3. Reasoner & Verification: 논리적 답변 생성 및 CoT 기반 팩트체크.  

Step 4. Synthesizer: 표준 레이아웃 적용 및 최종 렌더링.  

Step 5. Guardrail: 개인정보 마스킹 및 최종 안전 검증.  

2. 지능형 분기 전략 (Intelligent Branching)  
질문의 복잡도에 따라 비용을 다르게 씁니다.  

Simple: 단순 조회는 Gemini Flash 단독 처리 (0.72초 초고속 응답).  

Complex: 정밀 분석이 필요할 때만 고성능 모델(GPT-5, Claude 4.5 등) 투입.  

Bulk: 대량 문서 분석을 위한 병렬 처리 모드.  

💻 Tech Stack  
LLM/SLM: Gemini 2.0 Flash/Pro, GPT-5.2, Claude 4.5, DeepSeek-R1, Llama 4.  
Embeddings: OpenAI text-embedding-3-small.  
Database: PostgreSQL 15+ (메타데이터), Milvus 2.3+ (벡터 검색).  
Infrastructure: Naver Cloud Platform (NCP).  

## �️ 개발 매뉴얼 (Development Manual)

### 1. 가상환경 설정 (Virtual Environment Setup)
git pull 후 즉시 작업에 착수할 수 있도록 아래 명령어를 실행해주세요.

**Mac/zsh**
```bash
python -m venv venv && source venv/bin/activate
```

**Windows**
```bash
python -m venv venv && .\venv\Scripts\activate
```

### 2. 담당 파트 및 작업 경로 (Roles & Paths)
- **권영민** (`app/core/`): LLM 오케스트레이션 엔진 및 5단계 라우팅 로직 개발.
- **이지석** (`app/services/agent_hub/`): 에이전트 생성 및 계층형 관리 허브 시스템 구축.
- **윤호성** (`app/services/ai_drive/`): AI 드라이브 RAG 시스템 및 통합 운영 관리 시스템 구축.

### 3. 서버 및 데이터베이스 정보 (Server & DB Info)
- **Status**: 현재 테스트는 로컬 환경 및 NCP Standard 서버를 활용함.
- **Plan**: MVP 구축 후 회사 내부 서버로 이관 예정.

## 🤝 우리 팀 협업 가이드라인 (Ground Rules)

### 1. 보안 및 지갑 사수 (Security & Cost) 🔐
- **.env 파일 업로드 절대 금지**: 어떤 이유에서든 실제 API 키가 포함된 `.env` 파일을 깃허브에 올리지 않습니다.

### 2. 깃 워크플로우 준수 (Git Strategy) 🛠️
- **직접 Push 금지**: `develop` 브랜치나 `main` 브랜치에 직접 코드를 밀어넣지 마세요.
- **PR 및 리뷰 필수**: 반드시 본인의 `feature/기능명` 브랜치에서 작업 후 `develop`으로 PR을 날려야 하며, 팀원 1명 이상의 승인(Approve)이 있어야 머지할 수 있습니다.
- **커밋 메시지 규칙**:
    - 모든 커밋 메시지는 **한국어**로 작성합니다.
    - 제목과 수정 사항은 제3자가 봐도 이해할 수 있도록 최대한 자세하게 기술해 주세요.
    - 예: `feat: 오케스트레이터 Router 레이어 의도 분류 로직 추가`

### 3. 개발 환경 일관성 (Environment) 💻
- **가상환경 필수 사용**: 로컬에 직접 라이브러리를 설치하지 말고 반드시 `venv` 안에서 작업하세요. 운영체제 간 환경 충돌을 방지하기 위함입니다.
- **라이브러리 추가 시 공지**: 새로운 라이브러리를 설치했다면 반드시 `pip freeze > requirements.txt`를 실행해 파일을 업데이트하고 팀원들에게 즉시 공유해야 합니다.

### 4. 인터페이스 우선 설계 (Contract First) 🤝
- **독자 노선 금지**: 본인이 맡은 파트(`agent_hub`, `ai_drive`, `core`)의 함수 이름이나 주고받는 데이터 형식(JSON Schema 등)을 변경하고 싶다면, 반드시 관련 담당자(지석, 호성, 영민)와 상의 후 **'인터페이스 규격'**부터 업데이트해야 합니다.
