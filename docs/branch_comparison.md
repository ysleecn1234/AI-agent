# Feature-A-1 vs feature-Y 브랜치 교차검증 보고서

**검증 일시:** 2026-02-08  
**비교 대상:** `app/core/orchestrator.py`

---

## 🔍 핵심 발견사항

### Feature-A-1: Mock 구현 (노션 TODO의 지적 대상)
### feature-Y: 완전한 LLM 연동 구현 (노션 TODO 해결 완료)

---

## 📊 브랜치별 코드 비교

### 1. `analyze_for_draft` 메서드 비교

#### Feature-A-1 (Mock 구현) ❌

```python
# Feature-A-1: app/core/orchestrator.py:28-37
async def analyze_for_draft(self, messages: List[Dict]) -> Dict:
    """
    Analyzes conversation history to generate an Agent Draft.
    """
    # Mock logic
    return {
        "name": "Generated Agent (Draft)",
        "description": "Auto-generated description based on chat.",
        "system_prompt": "You are a helpful assistant...",
        "input_example": "Help me with...",
        "output_example": "Here is the answer..."
    }
```

**문제점:**
- ❌ 하드코딩된 고정 값 반환
- ❌ 대화 내용 분석 없음
- ❌ LLM 연동 없음
- ❌ JSON 스키마 정확도 낮음

**노션 지적사항과 일치:**
> "현재 상태: analyze_for_draft 메서드가 하드코딩된 로직으로 동작합니다."

---

#### feature-Y (LLM 연동 완료) ✅

```python
# feature-Y: app/core/orchestrator.py:147-250
async def analyze_for_draft(self, messages: List[Dict]) -> Dict:
    """
    Agent 생성을 위한 대화 분석 (Pull-Fill 패턴)
    1. Agent Hub에서 템플릿 가져오기 (Pull)
    2. 대화 분석으로 템플릿 채우기 (Fill)
    """
    # 1. PULL: Agent Hub에서 템플릿 가져오기
    template = self._get_agent_template()
    
    # 2. FILL: 대화 분석으로 템플릿 채우기
    filled_data = await self._analyze_conversation(messages, template)
    
    # 3. 템플릿과 분석 결과 병합
    draft_data = {**template, **filled_data}
    
    return draft_data

async def _analyze_conversation(self, messages: List[Dict], template: Dict) -> Dict:
    # 대화 내용 결합
    conversation_text = "\n".join([
        f"{msg.get('role', 'user')}: {msg.get('content', '')}"
        for msg in messages
    ])
    
    # 구조화된 JSON 프롬프트
    prompt = f"""다음 대화 내용을 분석하여 AI 에이전트를 생성하기 위한 정보를 추출해주세요.

대화 내용:
{conversation_text}

다음 JSON 형식으로 답변해주세요:
{{
    "name": "에이전트 이름 (간단명료하게, 최대 50자)",
    "description": "에이전트의 역할과 목적 (1-2문장)",
    "system_prompt": "에이전트가 사용할 상세한 시스템 프롬프트",
    "input_example": "사용자 입력 예시",
    "output_example": "에이전트 출력 예시",
    "category": "MARKETING, CODING, HR, SALES, GENERAL 중 하나"
}}
"""
    
    # Pipeline으로 분석
    result = self.pipeline_without_rag.process(user_input=prompt, user_id=None)
    response_text = result.get("final_response", result.get("response", ""))
    
    # JSON 파싱 시도
    try:
        import json
        import re
        
        # JSON 부분 추출
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            # 템플릿에 정의된 필드만 반환
            return {k: v for k, v in parsed.items() if k in template}
    except Exception as e:
        print(f"[Orchestrator] JSON parsing failed: {e}")
    
    # 파싱 실패 시 기본값
    return {
        "name": "Generated Agent",
        "description": "Auto-generated from conversation",
        "system_prompt": response_text[:500] if response_text else "You are a helpful assistant.",
        "input_example": "Help me with...",
        "output_example": "Here is the answer...",
        "category": "GENERAL"
    }
```

**개선사항:**
- ✅ LLM 연동 (Pipeline 사용)
- ✅ Pull-Fill 패턴 구현
- ✅ 구조화된 JSON 프롬프트
- ✅ JSON 파싱 로직
- ✅ Fallback 메커니즘
- ✅ 대화 내용 실제 분석

---

### 2. `recommend_agents` 메서드 비교

#### Feature-A-1 ❌

```python
# Feature-A-1: 메서드 없음
# recommend_agents 메서드가 존재하지 않음
```

**문제점:**
- ❌ 기능 자체가 구현되지 않음
- ❌ 실시간 Agent 추천 불가능

**노션 지적사항과 일치:**
> "현재 상태: ❌ 구현 안 됨"

---

#### feature-Y (LLM 연동 완료) ✅

```python
# feature-Y: app/core/orchestrator.py:68-144
async def recommend_agents(self, current_message: str, conversation_history: List[Dict] = None) -> Dict:
    """
    실시간 Agent 추천 (대화 중)
    현재 대화 내용을 분석하여 관련 Agent 2-3개 추천
    """
    # 대화 컨텍스트 구성
    if conversation_history:
        context = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation_history[-5:]  # 최근 5개만
        ])
        full_text = f"{context}\nuser: {current_message}"
    else:
        full_text = current_message
    
    # 주제 분석 프롬프트
    prompt = f"""다음 대화의 주제와 의도를 분석해주세요:

{full_text}

다음 JSON 형식으로 답변해주세요:
{{
    "topic": "대화의 핵심 주제 (1문장)",
    "category": "MARKETING, CODING, HR, SALES, GENERAL 중 하나",
    "keywords": ["관련 키워드1", "키워드2", "키워드3"]
}}
"""
    
    # Pipeline으로 분석
    result = self.pipeline_without_rag.process(user_input=prompt, user_id=None)
    response_text = result.get("final_response", result.get("response", ""))
    
    # JSON 파싱
    try:
        import json
        import re
        
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "topic": parsed.get("topic", "일반 대화"),
                "category": parsed.get("category", "GENERAL"),
                "keywords": parsed.get("keywords", [])
            }
    except Exception as e:
        print(f"[Orchestrator] Recommendation parsing failed: {e}")
    
    # 파싱 실패 시 기본값
    return {
        "topic": "일반 대화",
        "category": "GENERAL",
        "keywords": self._extract_simple_keywords(current_message)
    }

def _extract_simple_keywords(self, text: str) -> List[str]:
    """간단한 키워드 추출 (파싱 실패 시 폴백)"""
    import re
    words = re.findall(r'[가-힣a-zA-Z]{2,}', text)
    from collections import Counter
    common = Counter(words).most_common(3)
    return [word for word, count in common]
```

**개선사항:**
- ✅ LLM 연동 (Pipeline 사용)
- ✅ 대화 컨텍스트 분석
- ✅ 구조화된 JSON 프롬프트
- ✅ JSON 파싱 로직
- ✅ Fallback 메커니즘 (키워드 추출)

---

## 📋 종합 비교표

| 항목 | Feature-A-1 | feature-Y |
|------|-------------|-----------|
| **`analyze_for_draft`** | ❌ Mock (하드코딩) | ✅ LLM 연동 |
| **`recommend_agents`** | ❌ 없음 | ✅ LLM 연동 |
| **대화 내용 분석** | ❌ 없음 | ✅ 구현됨 |
| **JSON 프롬프트** | ❌ 없음 | ✅ 구조화됨 |
| **JSON 파싱** | ❌ 없음 | ✅ 정규식 + 파싱 |
| **Fallback 로직** | ❌ 없음 | ✅ 구현됨 |
| **Pipeline 연동** | ❌ 없음 | ✅ 완료 |
| **Pull-Fill 패턴** | ❌ 없음 | ✅ 구현됨 |

---

## 🎯 노션 TODO 지적사항 검증

### 노션 지적: "하드코딩된 `if "마케팅" in text:` 로직"

**Feature-A-1:**
- ✅ **노션 지적이 정확함**
- 실제로 하드코딩된 Mock 값 반환
- `"Generated Agent (Draft)"` 고정 반환

**feature-Y:**
- ✅ **노션 지적 해결 완료**
- LLM Prompting으로 완전 교체
- 하드코딩 없음

---

### 노션 지적: "LLM Prompting 로직으로 교체 필요"

**Feature-A-1:**
- ❌ Mock 상태 유지
- TODO 주석만 있음

**feature-Y:**
- ✅ **완전히 교체 완료**
- Pipeline을 통한 LLM 호출
- 구조화된 프롬프트 사용

---

### 노션 지적: "Agent 추천 기능 구현 안 됨"

**Feature-A-1:**
- ❌ `recommend_agents` 메서드 없음
- 기능 자체가 존재하지 않음

**feature-Y:**
- ✅ **완전히 구현 완료**
- 대화 주제 분석
- 카테고리 및 키워드 추출

---

## ✅ 최종 결론

### Feature-A-1 브랜치
- **상태:** Mock 구현 (Stub)
- **노션 TODO:** 지적사항이 그대로 존재
- **목적:** 팀원들이 인터페이스 테스트용으로 사용

### feature-Y 브랜치
- **상태:** 완전한 LLM 연동 구현
- **노션 TODO:** 모든 지적사항 해결 완료
- **목적:** 실제 프로덕션 로직 구현

---

## 🚀 다음 단계

1. ✅ feature-Y의 구현이 완료되었음을 확인
2. ⏳ Feature-A-1로 병합 또는 develop 브랜치로 PR
3. ⏳ Orchestrator 로직 그림 작성 (팀원 요청)

**권장사항:** feature-Y의 Orchestrator 구현을 Feature-A-1에 병합하여 팀원들이 실제 LLM 연동 기능을 사용할 수 있도록 해야 합니다.
