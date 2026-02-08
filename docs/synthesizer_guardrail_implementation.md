# Synthesizer & Guardrail LLM 연동 구현 계획

**작성일:** 2026-02-08  
**작성자:** Kwon (feature-Y)

---

## 🎯 목표

Router와 Reasoner에 이어 나머지 Pipeline 컴포넌트의 LLM 연동 완료:
1. **Synthesizer** - 답변 정리 및 포맷팅 (Claude 4.5)
2. **Guardrail** - 품질 검수 및 안전성 검증 (DeepSeek-R1)

---

## 📋 현재 상태

### ✅ 완료된 컴포넌트
- **Router** - Gemini 2.0 Flash (의도 분류)
- **Researcher** - AI Drive 연동 (RAG 검색)
- **Reasoner** - GPT-5.2 (답변 생성)

### ⏳ 구현 필요
- **Synthesizer** - Mock 구현 (Line 590-621)
- **Guardrail** - Mock 구현 (Line 625-771)

---

## 🛠️ Synthesizer 구현 계획

### 역할 (기획서 기준)
- **모델:** Claude 4.5 (`claude-sonnet-4-5-20250514`)
- **선정 사유:** 일관성, JSON 스키마 준수 능력
- **작업:** 답변을 사용자 친화적인 마크다운 형식으로 정리

### 현재 Mock 코드

```python
# Line 597-612
def format_response(self, reasoning_result: Dict[str, Any]) -> str:
    """응답 포맷팅"""
    response = reasoning_result["response"]
    confidence = reasoning_result["confidence"]
    
    # 마크다운 형식으로 포맷팅
    formatted = f"""
## 답변

{response}

---
**신뢰도**: {confidence * 100:.1f}%
**모델**: {reasoning_result.get('complexity', 'unknown')}
"""
    return formatted.strip()
```

### 개선 계획

```python
def format_response(self, reasoning_result: Dict[str, Any]) -> str:
    """Claude 4.5를 사용한 응답 포맷팅"""
    import litellm
    
    response = reasoning_result["response"]
    user_input = reasoning_result.get("user_input", "")
    intent = reasoning_result.get("intent", "")
    
    # Claude 4.5에게 포맷팅 요청
    prompt = f"""다음 AI 답변을 사용자 친화적인 마크다운 형식으로 정리해주세요.

사용자 질문: {user_input}
의도: {intent}
원본 답변:
{response}

요구사항:
1. 명확한 구조 (제목, 본문, 요약)
2. 가독성 높은 마크다운 포맷
3. 중요 정보 강조 (볼드, 이탤릭)
4. 필요시 리스트나 표 사용

마크다운 형식으로만 답변해주세요."""

    try:
        result = litellm.completion(
            model="claude-sonnet-4-5-20250514",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # 일관성 중시
            max_tokens=2000
        )
        formatted = result.choices[0].message.content
        print(f"  ✓ Synthesizer (Claude 4.5) 포맷팅 완료")
        return formatted
        
    except Exception as e:
        print(f"  [!] Synthesizer 실패: {e}, Fallback 사용")
        # Fallback: 기본 포맷팅
        return self._format_fallback(reasoning_result)

def _format_fallback(self, reasoning_result: Dict[str, Any]) -> str:
    """Fallback 포맷팅 (LLM 실패 시)"""
    response = reasoning_result["response"]
    confidence = reasoning_result["confidence"]
    
    formatted = f"""## 답변

{response}

---
**신뢰도**: {confidence * 100:.1f}%
**모델**: {reasoning_result.get('model_used', 'unknown')}
"""
    return formatted.strip()
```

---

## 🛡️ Guardrail 구현 계획

### 역할 (기획서 기준)
- **모델:** DeepSeek-R1 (`deepseek/deepseek-r1`)
- **선정 사유:** CoT 기반 논리 검증, 팩트체크 특화
- **작업:** 품질 검수, 논리적 일관성 검증, 안전성 검사

### 현재 Mock 코드

```python
# Line 712-738
def _check_completeness(self, user_input: str, response: str, intent: str) -> bool:
    """요청사항 충족도 검증"""
    # TODO: LLM을 사용한 정교한 검증 구현
    # 현재는 간단한 길이 기반 체크
    if intent == IntentType.ANALYSIS.value:
        return len(response) > 100
    elif intent == IntentType.GENERATION.value:
        return len(response) > 50
    return True
```

### 개선 계획

```python
def verify_quality(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
    """DeepSeek-R1을 사용한 품질 검수"""
    import litellm
    
    complexity = synthesis_result.get("complexity")
    
    # SIMPLE 작업은 품질 검수 스킵
    if complexity == ComplexityLevel.SIMPLE.value:
        return {
            "quality_verified": True,
            "quality_score": 1.0,
            "quality_issues": [],
            "needs_regeneration": False
        }
    
    # COMPLEX, BULK 작업은 DeepSeek-R1로 검수
    print("  → DeepSeek-R1 품질 검수 중...")
    
    user_input = synthesis_result.get("user_input", "")
    response = synthesis_result.get("response", "")
    intent = synthesis_result.get("intent", "")
    
    # DeepSeek-R1에게 검수 요청 (CoT 활용)
    prompt = f"""다음 AI 답변의 품질을 검수해주세요.

사용자 질문: {user_input}
의도: {intent}
AI 답변:
{response}

다음 항목을 검증하고 JSON 형식으로 답변해주세요:
{{
    "completeness": true/false,  // 요청사항 충족 여부
    "logical_consistency": true/false,  // 논리적 일관성
    "factual_accuracy": true/false,  // 사실 정확성
    "issues": ["이슈1", "이슈2", ...],  // 발견된 문제점
    "quality_score": 0.0-1.0  // 전체 품질 점수
}}

단계별로 사고하여 정확히 검증해주세요."""

    try:
        result = litellm.completion(
            model="deepseek/deepseek-r1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # 정확성 중시
            max_tokens=1500
        )
        response_text = result.choices[0].message.content
        
        # JSON 파싱
        import json
        import re
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            quality_data = json.loads(json_match.group())
            
            quality_score = quality_data.get("quality_score", 0.8)
            issues = quality_data.get("issues", [])
            
            print(f"  ✓ DeepSeek-R1 검수 완료 (점수: {quality_score:.2f})")
            
            return {
                "quality_verified": quality_score >= 0.7,
                "quality_score": quality_score,
                "quality_issues": issues,
                "needs_regeneration": quality_score < 0.6
            }
    
    except Exception as e:
        print(f"  [!] DeepSeek-R1 검수 실패: {e}, Fallback 사용")
    
    # Fallback: 기본 검수
    return self._verify_fallback(synthesis_result)

def _verify_fallback(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback 검수 (LLM 실패 시)"""
    user_input = synthesis_result.get("user_input", "")
    response = synthesis_result.get("response", "")
    intent = synthesis_result.get("intent", "")
    
    quality_issues = []
    
    # 기본 검증
    if intent == IntentType.ANALYSIS.value and len(response) < 100:
        quality_issues.append("분석 답변이 너무 짧습니다.")
    
    if intent == IntentType.GENERATION.value and len(response) < 50:
        quality_issues.append("생성 답변이 너무 짧습니다.")
    
    quality_score = max(0.0, 1.0 - (len(quality_issues) * 0.3))
    
    return {
        "quality_verified": len(quality_issues) == 0,
        "quality_score": quality_score,
        "quality_issues": quality_issues,
        "needs_regeneration": quality_score < 0.6
    }
```

---

## 📊 구현 순서

### Phase 1: Synthesizer 구현 (30분)
1. `format_response()` 메서드에 Claude 4.5 연동
2. Fallback 로직 추가
3. 에러 처리

### Phase 2: Guardrail 구현 (45분)
1. `verify_quality()` 메서드에 DeepSeek-R1 연동
2. JSON 파싱 로직 추가
3. Fallback 로직 추가
4. 에러 처리

### Phase 3: 테스트 (30분)
1. 전체 Pipeline 통합 테스트
2. 각 컴포넌트 단위 테스트
3. Fallback 시나리오 테스트

### Phase 4: 문서화 (15분)
1. API 통합 가이드 업데이트
2. 흐름도 업데이트
3. 커밋 및 푸시

---

## 🔑 필요한 API 키

- `ANTHROPIC_API_KEY` - Claude 4.5 (Synthesizer)
- `DEEPSEEK_API_KEY` - DeepSeek-R1 (Guardrail)

---

## ⚠️ 주의사항

1. **비용 관리**
   - Synthesizer는 모든 요청에 실행됨
   - Guardrail은 COMPLEX/BULK만 실행
   - 비용 추적 필수

2. **Fallback 전략**
   - LLM 실패 시 기본 로직으로 폴백
   - 시스템 안정성 확보

3. **성능 최적화**
   - temperature 낮게 설정 (일관성)
   - max_tokens 적절히 제한

---

## ✅ 완료 기준

- [ ] Synthesizer Claude 4.5 연동
- [ ] Synthesizer Fallback 구현
- [ ] Guardrail DeepSeek-R1 연동
- [ ] Guardrail Fallback 구현
- [ ] 전체 Pipeline 테스트
- [ ] 문서 업데이트
- [ ] 커밋 및 푸시
