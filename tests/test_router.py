"""
Router 고도화 테스트
다양한 입력 패턴으로 의도 분류 및 복잡도 판단 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pipeline import Router

def test_router():
    router = Router()
    
    test_cases = [
        # SIMPLE 케이스
        "AI 에이전트가 뭐야?",
        "간단히 설명해줘",
        "핵심만 알려줘",
        
        # COMPLEX 케이스
        "최근 프로젝트 문서에서 비용 최적화 관련 내용을 자세히 분석해줘",
        "우리 시스템의 성능 문제를 다각도로 검토하고 개선 방안을 제시해줘",
        "경쟁사 대비 우리 제품의 장단점을 비교 분석해줘",
        
        # BULK 케이스
        "지난 1년간의 모든 프로젝트 데이터를 종합 분석하고, 각 프로젝트별 성과 지표를 비교하며, 향후 개선 방향을 상세히 제시해줘. 또한 팀별 기여도와 예산 집행 현황도 함께 검토해줘.",
        
        # 의도 분류 테스트
        "최신 AI 모델을 검색해줘",  # SEARCH
        "이 데이터의 추세를 분석해줘",  # ANALYSIS
        "새로운 기능 명세서를 작성해줘",  # GENERATION
    ]
    
    print("=" * 80)
    print("Router 고도화 테스트")
    print("=" * 80)
    
    for i, test_input in enumerate(test_cases, 1):
        result = router.route(test_input)
        print(f"\n[테스트 {i}]")
        print(f"입력: {test_input}")
        print(f"의도: {result['intent']}")
        print(f"복잡도: {result['complexity']}")
        print("-" * 80)

if __name__ == "__main__":
    test_router()
