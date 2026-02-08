# Documentation

AI-agent 프로젝트의 모든 문서를 모아놓은 폴더입니다.

## 📚 문서 목록

### LLM 연동 관련
- **[llm_api_integration.md](./llm_api_integration.md)** - LLM API 통합 가이드
  - 기획서 역할 매핑
  - 모델별 사용 사례
  - API 키 설정 방법

- **[orchestrator_sequence_diagrams.md](./orchestrator_sequence_diagrams.md)** - Orchestrator 시퀀스 다이어그램
  - User Request Processing (5-Layer Pipeline)
  - Agent Recommendation (실시간 추천)
  - Agent Creation (Draft 생성)

- **[orchestrator_flow_diagram.md](./orchestrator_flow_diagram.md)** - Orchestrator 전체 흐름도
  - 3가지 주요 Flow 설명
  - 컴포넌트별 역할
  - 데이터 흐름

### 구현 계획
- **[synthesizer_guardrail_implementation.md](./synthesizer_guardrail_implementation.md)** - Synthesizer & Guardrail 구현 계획
  - Claude 4.5 연동 (Synthesizer)
  - DeepSeek-R1 연동 (Guardrail)
  - Fallback 전략

### 분석 및 비교
- **[branch_comparison.md](./branch_comparison.md)** - Feature-A-1 vs feature-Y 브랜치 비교
  - Mock vs 실제 LLM 연동 비교
  - 노션 TODO 검증 결과

- **[ai_drive_analysis.md](./ai_drive_analysis.md)** - AI Drive 분석
- **[orchestrator_agent_features.md](./orchestrator_agent_features.md)** - Orchestrator Agent 기능
- **[development_status.md](./development_status.md)** - 개발 상태
- **[integration_walkthrough.md](./integration_walkthrough.md)** - 통합 가이드

---

## 🎯 빠른 시작

### 1. LLM 연동 이해하기
1. [llm_api_integration.md](./llm_api_integration.md)를 읽고 전체 구조 파악
2. [orchestrator_sequence_diagrams.md](./orchestrator_sequence_diagrams.md)로 시퀀스 확인
3. [orchestrator_flow_diagram.md](./orchestrator_flow_diagram.md)로 상세 흐름 이해

### 2. 구현 내용 확인
1. [branch_comparison.md](./branch_comparison.md)로 구현 차이 확인
2. [synthesizer_guardrail_implementation.md](./synthesizer_guardrail_implementation.md)로 최신 구현 확인

---

## 📝 문서 작성 규칙

- **Markdown 형식** 사용
- **Mermaid 다이어그램** 활용 (시퀀스, 플로우차트)
- **코드 예시** 포함
- **한글** 우선, 기술 용어는 영문 병기

---

## 🔗 관련 문서

- [메인 README](../README.md) - 프로젝트 전체 개요
- [Core Module README](../core/README.md) - Pipeline 상세 설명
- [App README](../app/README.md) - 웹 서버 구현 계획
