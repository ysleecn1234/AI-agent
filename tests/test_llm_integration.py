#!/usr/bin/env python3
"""
Router 및 Reasoner LLM 연동 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pipeline import Router, Reasoner

def test_router():
    """Router LLM 테스트"""
    print("=" * 50)
    print("Router LLM 테스트")
    print("=" * 50)
    
    router = Router()
    
    test_inputs = [
        "마케팅 전략 문서 찾아줘",
        "지난 분기 매출 데이터 분석해줘",
        "신제품 소개 자료 만들어줘",
        "회사 정책이 뭐야?"
    ]
    
    for user_input in test_inputs:
        print(f"\n입력: {user_input}")
        intent = router.classify_intent(user_input)
        print(f"의도: {intent.value}")

def test_reasoner():
    """Reasoner LLM 테스트"""
    print("\n" + "=" * 50)
    print("Reasoner LLM 테스트")
    print("=" * 50)
    
    reasoner = Reasoner()
    
    context = {
        "complexity": "simple",
        "user_input": "AI 에이전트가 뭐야?",
        "retrieved_documents": [
            {"content": "AI 에이전트는 자율적으로 작업을 수행하는 인공지능 시스템입니다."}
        ]
    }
    
    print(f"\n입력: {context['user_input']}")
    response, model = reasoner.generate_response(context)
    print(f"모델: {model}")
    print(f"답변: {response[:200]}...")

if __name__ == "__main__":
    print("LLM 연동 테스트 시작\n")
    print("주의: 이 테스트는 실제 API 키가 필요합니다.")
    print(".env 파일에 GOOGLE_API_KEY와 OPENAI_API_KEY를 설정하세요.\n")
    
    try:
        test_router()
        test_reasoner()
        print("\n✅ 모든 테스트 완료!")
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
