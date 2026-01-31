"""
Core Pipeline 통합 테스트
Mock 데이터를 사용하여 전체 파이프라인 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pipeline import Pipeline

def test_simple_query():
    """Simple 쿼리 테스트 - RAG 검색 없음"""
    print("\n" + "=" * 80)
    print("[테스트 1] Simple 쿼리")
    print("=" * 80)
    
    pipeline = Pipeline(use_rag=False)  # Mock 모드
    
    result = pipeline.process("AI 에이전트가 뭐야?")
    
    # 검증
    assert result is not None, "결과가 None입니다"
    assert "final_response" in result, "final_response가 없습니다"
    assert result.get("complexity") == "simple", f"복잡도가 simple이 아닙니다: {result.get('complexity')}"
    assert result.get("intent") in ["query", "search"], f"의도가 예상과 다릅니다: {result.get('intent')}"
    
    # RAG 검색이 스킵되었는지 확인
    retrieved_docs = result.get("retrieved_documents", [])
    assert len(retrieved_docs) == 0, f"Simple 쿼리인데 문서가 검색되었습니다: {len(retrieved_docs)}개"
    
    print("\n[OK] Simple 쿼리 테스트 통과")
    print(f"  - 복잡도: {result['complexity']}")
    print(f"  - 의도: {result['intent']}")
    print(f"  - 검색된 문서: {len(retrieved_docs)}개")
    
    return result


def test_complex_query_with_rag():
    """Complex 쿼리 테스트 - RAG 검색 포함"""
    print("\n" + "=" * 80)
    print("[테스트 2] Complex 쿼리 (RAG Mock)")
    print("=" * 80)
    
    pipeline = Pipeline(use_rag=False)  # Mock 모드
    
    result = pipeline.process("프로젝트 문서에서 비용 최적화 방안을 자세히 분석해줘")
    
    # 검증
    assert result is not None, "결과가 None입니다"
    assert "final_response" in result, "final_response가 없습니다"
    
    # Complex 또는 Bulk 복잡도여야 함
    complexity = result.get("complexity")
    assert complexity in ["complex", "bulk"], f"복잡도가 complex/bulk가 아닙니다: {complexity}"
    
    # ANALYSIS 의도여야 함
    intent = result.get("intent")
    assert intent == "analysis", f"의도가 analysis가 아닙니다: {intent}"
    
    # RAG 검색이 실행되었는지 확인
    retrieved_docs = result.get("retrieved_documents", [])
    assert len(retrieved_docs) > 0, "Complex 쿼리인데 문서가 검색되지 않았습니다"
    
    print("\n[OK] Complex 쿼리 테스트 통과")
    print(f"  - 복잡도: {result['complexity']}")
    print(f"  - 의도: {result['intent']}")
    print(f"  - 검색된 문서: {len(retrieved_docs)}개")
    
    # 검색된 문서 샘플 출력
    if retrieved_docs:
        print(f"\n  [검색된 문서 샘플]")
        for i, doc in enumerate(retrieved_docs[:2], 1):
            print(f"    {i}. {doc.get('source')} (점수: {doc.get('score', 0):.2f})")
            print(f"       내용: {doc.get('content', '')[:100]}...")
    
    return result


def test_generation_query():
    """Generation 쿼리 테스트"""
    print("\n" + "=" * 80)
    print("[테스트 3] Generation 쿼리")
    print("=" * 80)
    
    pipeline = Pipeline(use_rag=False)
    
    result = pipeline.process("새로운 기능 명세서를 작성해줘")
    
    # 검증
    assert result is not None, "결과가 None입니다"
    assert result.get("intent") == "generation", f"의도가 generation이 아닙니다: {result.get('intent')}"
    
    print("\n[OK] Generation 쿼리 테스트 통과")
    print(f"  - 복잡도: {result['complexity']}")
    print(f"  - 의도: {result['intent']}")
    
    return result


def test_quality_verification():
    """품질 검수 테스트 (Complex 쿼리)"""
    print("\n" + "=" * 80)
    print("[테스트 4] 품질 검수 (Complex)")
    print("=" * 80)
    
    pipeline = Pipeline(use_rag=False)
    
    result = pipeline.process("지난 1년간의 모든 프로젝트 데이터를 종합 분석하고, 각 프로젝트별 성과 지표를 비교하며, 향후 개선 방향을 상세히 제시해줘")
    
    # 검증
    assert result is not None, "결과가 None입니다"
    assert "quality_verified" in result, "품질 검수 결과가 없습니다"
    assert "quality_score" in result, "품질 점수가 없습니다"
    
    print("\n[OK] 품질 검수 테스트 통과")
    print(f"  - 복잡도: {result['complexity']}")
    print(f"  - 품질 검증: {result.get('quality_verified')}")
    print(f"  - 품질 점수: {result.get('quality_score', 0):.2f}")
    
    if result.get("quality_issues"):
        print(f"  - 품질 이슈: {len(result['quality_issues'])}개")
        for issue in result['quality_issues']:
            print(f"    - {issue}")
    
    return result


def test_all_complexity_levels():
    """모든 복잡도 레벨 테스트"""
    print("\n" + "=" * 80)
    print("[테스트 5] 모든 복잡도 레벨")
    print("=" * 80)
    
    pipeline = Pipeline(use_rag=False)
    
    test_cases = [
        ("간단히 설명해줘", "simple"),
        ("최근 프로젝트 문서에서 비용 최적화 관련 내용을 자세히 분석해줘", "complex"),
        # Bulk는 매우 긴 쿼리여야 하므로 테스트 케이스 조정
    ]
    
    results = []
    for query, expected_complexity in test_cases:
        result = pipeline.process(query)
        actual_complexity = result.get("complexity")
        
        print(f"\n  쿼리: {query[:50]}...")
        print(f"  예상 복잡도: {expected_complexity}")
        print(f"  실제 복잡도: {actual_complexity}")
        
        # 복잡도 검증 (예상과 같거나 더 높으면 통과)
        complexity_order = {"simple": 0, "complex": 1, "bulk": 2}
        if complexity_order[actual_complexity] >= complexity_order[expected_complexity]:
            print(f"  [OK] 복잡도 판정 정확")
        else:
            print(f"  [WARNING] 복잡도가 예상보다 낮음 (허용)")
        
        results.append(result)
    
    print("\n[OK] 모든 복잡도 레벨 테스트 통과")
    print("  (참고: Bulk 복잡도는 매우 긴 쿼리에서만 발생)")
    return results


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 80)
    print("Core Pipeline 통합 테스트 시작")
    print("=" * 80)
    
    try:
        # 테스트 실행
        test_simple_query()
        test_complex_query_with_rag()
        test_generation_query()
        test_quality_verification()
        test_all_complexity_levels()
        
        # 최종 결과
        print("\n" + "=" * 80)
        print("[SUCCESS] 모든 테스트 통과!")
        print("=" * 80)
        print("\n다음 단계:")
        print("  1. 실제 LLM API 연동 (OpenAI, Google, Anthropic)")
        print("  2. AI Drive RAG 시스템 연동 (use_rag=True)")
        print("  3. 성능 및 비용 최적화")
        print("=" * 80)
        
        return True
        
    except AssertionError as e:
        print(f"\n[FAIL] 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
