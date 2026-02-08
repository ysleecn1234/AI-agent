"""
간단한 Pipeline 테스트 스크립트
pytest 없이 직접 실행
"""
import sys
sys.path.insert(0, '.')

from core.pipeline import Pipeline, ComplexityLevel, IntentType


def test_pipeline_initialization():
    """Pipeline 초기화 테스트"""
    print("\n[TEST 1] Pipeline 초기화 테스트...")
    try:
        pipeline = Pipeline(use_rag=False)
        assert pipeline is not None
        assert pipeline.router is not None
        assert pipeline.researcher is not None
        assert pipeline.reasoner is not None
        assert pipeline.synthesizer is not None
        assert pipeline.guardrail is not None
        print("[PASS] Pipeline 초기화 성공")
        return True
    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_router_classification():
    """Router 의도 분류 테스트"""
    print("\n[TEST 2] Router 의도 분류 테스트...")
    try:
        pipeline = Pipeline(use_rag=False)
        
        test_cases = [
            "안녕하세요",
            "AI Drive가 뭐야?",
            "마케팅 전략을 분석해줘"
        ]
        
        for user_input in test_cases:
            routing_result = pipeline.router.route(user_input)
            assert routing_result is not None
            assert "intent" in routing_result
            assert "complexity" in routing_result
            print(f"  ✓ '{user_input}' → Intent: {routing_result['intent']}, Complexity: {routing_result['complexity']}")
        
        print("✅ PASS: Router 의도 분류 성공")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_researcher_mock():
    """Researcher Mock 모드 테스트"""
    print("\n[TEST 3] Researcher Mock 모드 테스트...")
    try:
        pipeline = Pipeline(use_rag=False)
        
        query = "AI Drive 기능"
        documents = pipeline.researcher.search_documents(query, top_k=3)
        
        assert documents is not None
        assert isinstance(documents, list)
        print(f"  ✓ Mock 문서 {len(documents)}개 반환")
        
        if documents:
            print(f"  ✓ 첫 번째 문서: {documents[0].get('source', 'N/A')}")
        
        print("✅ PASS: Researcher Mock 모드 성공")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """전체 Pipeline 테스트 (Mock 모드, LLM 호출 없음)"""
    print("\n[TEST 4] 전체 Pipeline 테스트 (구조 검증)...")
    try:
        pipeline = Pipeline(use_rag=False)
        
        # 간단한 입력으로 구조만 확인
        user_input = "테스트"
        
        # Router만 테스트
        routing_result = pipeline.router.route(user_input)
        assert routing_result is not None
        print(f"  ✓ Router: Intent={routing_result['intent']}, Complexity={routing_result['complexity']}")
        
        # Researcher 테스트
        documents = pipeline.researcher.search_documents(user_input, top_k=3)
        assert documents is not None
        print(f"  ✓ Researcher: {len(documents)}개 문서 반환")
        
        print("✅ PASS: Pipeline 구조 검증 성공")
        print("\n⚠️  참고: 실제 LLM 호출 테스트는 API 키 설정 후 가능합니다.")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Feature-Y Pipeline 통합 테스트")
    print("=" * 60)
    
    results = []
    
    # 테스트 실행
    results.append(("Pipeline 초기화", test_pipeline_initialization()))
    results.append(("Router 의도 분류", test_router_classification()))
    results.append(("Researcher Mock", test_researcher_mock()))
    results.append(("전체 Pipeline 구조", test_full_pipeline()))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n총 {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
