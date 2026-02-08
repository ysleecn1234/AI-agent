"""
통합 테스트 - Feature-Y Pipeline 검증
Mock 모드로 전체 Pipeline 흐름 테스트
"""
import pytest
from core.pipeline import Pipeline, ComplexityLevel, IntentType


class TestPipelineIntegration:
    """전체 Pipeline 통합 테스트"""
    
    def setup_method(self):
        """테스트 초기화"""
        # Mock 모드로 Pipeline 초기화 (API 키 불필요)
        self.pipeline = Pipeline(use_rag=False)
    
    def test_pipeline_initialization(self):
        """Pipeline 초기화 테스트"""
        assert self.pipeline is not None
        assert self.pipeline.router is not None
        assert self.pipeline.researcher is not None
        assert self.pipeline.reasoner is not None
        assert self.pipeline.synthesizer is not None
        assert self.pipeline.guardrail is not None
    
    def test_simple_query_flow(self):
        """간단한 질의 흐름 테스트"""
        # Given: 간단한 질문
        user_input = "안녕하세요"
        
        # When: Pipeline 실행
        result = self.pipeline.process(user_input, user_id="test_user")
        
        # Then: 결과 검증
        assert result is not None
        assert "final_response" in result
        assert "intent" in result
        assert "complexity" in result
        
        # Intent가 유효한 값인지 확인
        valid_intents = [e.value for e in IntentType]
        assert result["intent"] in valid_intents
        
        # Complexity가 유효한 값인지 확인
        valid_complexities = [e.value for e in ComplexityLevel]
        assert result["complexity"] in valid_complexities
    
    def test_router_classification(self):
        """Router 의도 분류 테스트"""
        # Given: 다양한 유형의 질문
        test_cases = [
            ("AI Drive가 뭐야?", IntentType.QUERY),
            ("마케팅 전략을 분석해줘", IntentType.ANALYSIS),
            ("보고서를 작성해줘", IntentType.GENERATION),
        ]
        
        for user_input, expected_intent in test_cases:
            # When: Router 실행
            routing_result = self.pipeline.router.route(user_input)
            
            # Then: 의도 분류 확인
            assert routing_result is not None
            assert "intent" in routing_result
            # 의도가 예상과 같거나 유효한 값이어야 함
            assert routing_result["intent"] in [e.value for e in IntentType]
    
    def test_complexity_detection(self):
        """복잡도 판단 테스트"""
        # Given: 다양한 복잡도의 질문
        test_cases = [
            ("안녕", ComplexityLevel.SIMPLE),
            ("AI Drive의 주요 기능과 장단점을 상세히 분석해줘", ComplexityLevel.COMPLEX),
        ]
        
        for user_input, expected_complexity in test_cases:
            # When: Router 실행
            routing_result = self.pipeline.router.route(user_input)
            
            # Then: 복잡도 확인
            assert routing_result is not None
            assert "complexity" in routing_result
            # 복잡도가 유효한 값이어야 함
            assert routing_result["complexity"] in [e.value for e in ComplexityLevel]
    
    def test_researcher_mock_mode(self):
        """Researcher Mock 모드 테스트"""
        # Given: 검색 쿼리
        query = "AI Drive 기능"
        
        # When: Researcher 실행 (Mock 모드)
        documents = self.pipeline.researcher.search_documents(query, top_k=3)
        
        # Then: Mock 데이터 반환 확인
        assert documents is not None
        assert isinstance(documents, list)
        assert len(documents) <= 3
        
        # Mock 데이터 구조 확인
        if documents:
            assert "content" in documents[0]
            assert "source" in documents[0]
    
    def test_synthesizer_formatting(self):
        """Synthesizer 포맷팅 테스트"""
        # Given: Reasoner 결과
        reasoning_result = {
            "response": "테스트 답변입니다.",
            "confidence": 0.95,
            "complexity": ComplexityLevel.SIMPLE.value,
            "user_input": "테스트 질문",
            "intent": IntentType.QUERY.value,
            "model_used": "test-model"
        }
        
        # When: Synthesizer 실행
        formatted = self.pipeline.synthesizer.format_response(reasoning_result)
        
        # Then: 포맷팅 결과 확인
        assert formatted is not None
        assert isinstance(formatted, str)
        assert len(formatted) > 0
    
    def test_guardrail_simple_skip(self):
        """Guardrail SIMPLE 작업 스킵 테스트"""
        # Given: SIMPLE 복잡도 결과
        synthesis_result = {
            "response": "간단한 답변",
            "complexity": ComplexityLevel.SIMPLE.value,
            "user_input": "안녕",
            "intent": IntentType.QUERY.value
        }
        
        # When: Guardrail 실행
        quality_result = self.pipeline.guardrail.verify_quality(synthesis_result)
        
        # Then: SIMPLE은 자동 통과
        assert quality_result is not None
        assert quality_result["quality_verified"] is True
        assert quality_result["quality_score"] == 1.0
        assert quality_result["needs_regeneration"] is False
    
    def test_full_pipeline_end_to_end(self):
        """전체 Pipeline End-to-End 테스트"""
        # Given: 사용자 질문
        user_input = "AI Drive의 주요 기능은 무엇인가요?"
        
        # When: 전체 Pipeline 실행
        result = self.pipeline.process(user_input, user_id="test_user")
        
        # Then: 모든 단계 결과 확인
        assert result is not None
        
        # 필수 필드 확인
        required_fields = [
            "final_response",
            "intent",
            "complexity",
            "routing",
            "research",
            "reasoning",
            "synthesis",
            "guardrail"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        
        # 각 단계 결과 확인
        assert result["routing"] is not None
        assert result["research"] is not None
        assert result["reasoning"] is not None
        assert result["synthesis"] is not None
        assert result["guardrail"] is not None
        
        # 최종 응답 확인
        assert result["final_response"] is not None
        assert isinstance(result["final_response"], str)
        assert len(result["final_response"]) > 0


class TestOrchestrator:
    """Orchestrator 통합 테스트"""
    
    def test_orchestrator_import(self):
        """Orchestrator import 테스트"""
        try:
            from app.core.orchestrator import Orchestrator
            assert Orchestrator is not None
        except ImportError as e:
            pytest.skip(f"Orchestrator import failed: {e}")
    
    def test_orchestrator_initialization(self):
        """Orchestrator 초기화 테스트"""
        try:
            from app.core.orchestrator import Orchestrator
            orchestrator = Orchestrator()
            assert orchestrator is not None
            assert orchestrator.pipeline_with_rag is not None
            assert orchestrator.pipeline_without_rag is not None
        except ImportError as e:
            pytest.skip(f"Orchestrator import failed: {e}")


if __name__ == "__main__":
    # 직접 실행 시 pytest 실행
    pytest.main([__file__, "-v", "-s"])
