from typing import Dict

def get_standard_template() -> Dict:
    """
    새로운 에이전트를 위한 표준 JSON 스키마/템플릿을 반환합니다.
    이는 AI Hub와 Orchestrator 간의 계약(Contract) 역할을 합니다.
    """
    return {
        # Step 1: 개념 정의 (Concept)
        "name": "",             # [O] 제목
        "description": "",      # [O] 자동 생성된 초기 설명
        "input_example": "",    # [O] 입력 예시
        "output_example": "",   # [O] 출력 예시
        
        # Step 2: 설정 (Config)
        "category": "기타",     # [O] 카테고리 (Default: 기타)
        "use_rag": True,        # [O] 참조 문서 활용 여부 (Toggle)
        "visibility": "PUBLIC", # [O] 공개 범위 (전체 공개/나만 보기)
        
        # Hidden (Orchestrator Generated)
        "system_prompt": "",    # Orchestrator가 분석하여 자동 생성
        "model_type": "AUTO"    # AUTO: Orchestrator가 상황에 맞게 판단 (Default)
    }
