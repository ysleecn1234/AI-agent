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

👥 Team  
이지석: 에이전트 생성 및 관리 허브 시스템 구축.  
윤호성: AI 드라이브 및 통합 운영 관리 시스템 구축.  
권영민: LLM 오케스트레이션 엔진 및 라우팅 로직 개발.
