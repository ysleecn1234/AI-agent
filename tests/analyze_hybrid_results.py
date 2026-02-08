"""
하이브리드 Router 테스트 결과 분석
"""

print("=" * 80)
print("하이브리드 Router 테스트 결과 분석")
print("=" * 80)

results = [
    {"test": 1, "input": "AI 에이전트가 뭐야?", "confidence": 0.30, "method": "LLM", "intent": "query"},
    {"test": 2, "input": "간단히 설명해줘", "confidence": 0.30, "method": "LLM", "intent": "query"},
    {"test": 3, "input": "핵심만 알려줘", "confidence": 0.80, "method": "키워드", "intent": "search"},
    {"test": 4, "input": "최근 프로젝트 문서에서 비용 최적화 관련 내용을 자세히 분석해줘", "confidence": 0.67, "method": "LLM", "intent": "analysis"},
    {"test": 5, "input": "우리 시스템의 성능 문제를 다각도로 검토하고 개선 방안을 제시해줘", "confidence": 0.67, "method": "LLM", "intent": "analysis"},
    {"test": 6, "input": "경쟁사 대비 우리 제품의 장단점을 비교 분석해줘", "confidence": 1.00, "method": "키워드", "intent": "analysis"},
    {"test": 7, "input": "지난 1년간의 모든 프로젝트 데이터를 종합 분석하고...", "confidence": 1.00, "method": "키워드", "intent": "analysis"},
    {"test": 8, "input": "최신 AI 모델을 검색해줘", "confidence": 0.80, "method": "키워드", "intent": "search"},
    {"test": 9, "input": "이 데이터의 추세를 분석해줘", "confidence": 0.80, "method": "키워드", "intent": "analysis"},
    {"test": 10, "input": "새로운 기능 명세서를 작성해줘", "confidence": 0.80, "method": "키워드", "intent": "generation"},
]

print("\n[신뢰도 분포]")
keyword_count = sum(1 for r in results if r["method"] == "키워드")
llm_count = sum(1 for r in results if r["method"] == "LLM")

print(f"  키워드 분류: {keyword_count}건 ({keyword_count/len(results)*100:.0f}%)")
print(f"  LLM 분류: {llm_count}건 ({llm_count/len(results)*100:.0f}%)")

print("\n[비용 절감 효과]")
print(f"  키워드 분류 비용: $0 (무료)")
print(f"  LLM 분류 비용: ~$0.0001/건 (Gemini 2.0 Flash)")
print(f"  예상 총 비용: ${llm_count * 0.0001:.4f}")
print(f"  만약 모두 LLM 사용 시: ${len(results) * 0.0001:.4f}")
print(f"  절감률: {(1 - llm_count/len(results))*100:.0f}%")

print("\n[신뢰도별 분류]")
high_conf = [r for r in results if r["confidence"] >= 0.8]
mid_conf = [r for r in results if 0.5 <= r["confidence"] < 0.8]
low_conf = [r for r in results if r["confidence"] < 0.5]

print(f"  높음 (>=0.8): {len(high_conf)}건 -> 키워드만 사용")
print(f"  중간 (0.5-0.8): {len(mid_conf)}건 -> LLM 사용")
print(f"  낮음 (<0.5): {len(low_conf)}건 -> LLM 사용")

print("\n[주요 개선 사항]")
print("  1. 명확한 키워드가 있는 경우 -> 즉시 분류 (비용 0)")
print("  2. 애매한 경우만 LLM 사용 -> 정확도 향상")
print("  3. 전체 비용 60% 절감 (10건 중 4건만 LLM 사용)")

print("\n[다음 단계]")
print("  - API 연동 후 LLM 분류 활성화")
print("  - 신뢰도 임계값 조정 (현재 0.7)")
print("  - 복잡도 판단에도 하이브리드 적용 고려")

print("=" * 80)
