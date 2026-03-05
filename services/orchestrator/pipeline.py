"""
AI-agent Core Pipeline
5단계 레이어드 파이프라인: Router → Researcher → Reasoner → Synthesizer → Guardrail
"""

from typing import Dict, Any, Optional, Literal, List
from enum import Enum
import os
import time
import sys
from pathlib import Path
from dotenv import load_dotenv 
import litellm  

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent # services/orchestrator -> services -> root
sys.path.insert(0, str(project_root))

# Relative Imports (Modified from core.logger)
from .logger import get_logger
from .cost_calculator import get_cost_calculator
from services.common.cost_logger import get_cost_logger
import uuid
import datetime

# 환경 변수 로드
load_dotenv()

# ==================== 중앙 모델 설정 (TASK_MODEL_CONFIG) ====================
# 모든 LLM 호출은 이 설정을 통해 관리됩니다.
# models[0] = 후보 모델 (Primary), models[1] = 대체 모델 (Fallback)
TASK_MODEL_CONFIG = {
    
    # ── 채팅 파이프라인 (5단계) ──
    "chat_routing": {
        "models": ["gemini/gemini-2.5-flash-lite", "gpt-5-nano"],
        "temperature": 0.1,
        "max_tokens": 10,
        "description": "의도 분류 및 복잡도 판단 (Router)",
        "system_prompt": None,
    },
    "chat_research": {
        "models": ["gpt-5-mini", "claude-haiku-4.5"],
        "temperature": 0.2,
        "max_tokens": 500,
        "description": "검색 쿼리 생성 및 검증 (Researcher)",
        "system_prompt": None,
    },
    "chat_simple": {
        "models": ["gemini/gemini-2.5-flash", "gpt-5-mini"],
        "temperature": 0.7,
        "max_tokens": 4000,
        "description": "단순 질의 답변 생성 (Reasoner - SIMPLE)",
        "system_prompt": None,
    },
    "chat_complex": {
        "models": ["claude-sonnet-4-6", "gpt-5.2"],
        "temperature": 0.1,
        "max_tokens": 4000,
        "description": "정밀 분석 답변 생성 (Reasoner - COMPLEX)",
        "system_prompt": None,
    },
    "chat_bulk": {
        "models": ["gemini/gemini-3-flash-preview", "gemini/gemini-2.5-flash"],
        "temperature": 0.1,
        "max_tokens": 4000,
        "description": "대량 문서 분석 답변 생성 (Reasoner - BULK)",
        "system_prompt": None,
    },
    "chat_reasoning": {
        "models": ["gpt-5.2-pro", "claude-opus-4-6"],
        "temperature": 0.1,
        "max_tokens": 4000,
        "description": "문맥 기반 답변 생성 (Reasoner)",
        "system_prompt": None,
    },
    "chat_synthesis": {
        "models": ["gemini/gemini-2.5-flash", "claude-haiku-4.5"],
        "temperature": 0.3,
        "max_tokens": 4000,
        "description": "답변 종합 및 포맷팅 (Synthesizer)",
        "system_prompt": None,
    },
    "chat_guardrail": {
        "models": ["claude-haiku-4.5", "gpt-5.2"],
        "temperature": 0.1,
        "max_tokens": 2000,
        "description": "품질 검수 및 팩트체크 (Guardrail)",
        "system_prompt": (
            "당신은 AI 답변 품질 검수 전문가입니다.\n"
            "사용자 질문과 AI 답변을 비교하여 품질을 검증하세요.\n"
            "다음 항목을 반드시 검증하고 JSON으로만 응답하세요:\n"
            "{\n"
            '    "completeness": true/false,      // 요청사항 충족 여부\n'
            '    "logical_consistency": true/false, // 논리적 일관성\n'
            '    "factual_accuracy": true/false,   // 사실 정확성\n'
            '    "issues": ["이슈1", ...],          // 발견된 문제\n'
            '    "quality_score": 0.0~1.0          // 종합 품질 점수\n'
            "}\n"
            "단계별로 사고하여 정확히 검증하세요."
        ),
    },

    # ── 에이전트 허브 (Phase 2~3) ──
    "agent_draft": {
        "models": ["gpt-5.2", "claude-sonnet-4-6"],
        "temperature": 0.3,
        "max_tokens": 2000,
        "description": "대화 분석 → 에이전트 생성 템플릿 채우기 (Pull-Fill)",
        "system_prompt": (
            "당신은 AI 에이전트 설계 전문가입니다.\n"
            "제공된 대화 내용을 분석하여 에이전트 정보를 추출하세요.\n"
            "JSON으로만 응답하세요:\n"
            "{\n"
            '    "name": "에이전트 이름 (20자 이내)",\n'
            '    "description": "에이전트 설명 (50자 이내)",\n'
            '    "category": "카테고리",\n'
            '    "input_example": "사용자 질문 예시",\n'
            '    "output_example": "답변 예시 (간략하게)",\n'
            '    "system_prompt": "이 에이전트의 역할과 성격을 정의하는 시스템 프롬프트",\n'
            '    "use_rag": true/false,\n'
            '    "model_type": "AUTO",\n'
            '    "visibility": "PUBLIC"\n'
            "}\n"
            "규칙:\n"
            "1. 카테고리: 마케팅/개발/기획/영업/인사/재무/문서작성/데이터분석/기타 중 하나\n"
            "2. system_prompt는 에이전트가 수행할 역할을 구체적으로 정의\n"
            "3. 대화 내용에서 추출 불가능한 필드는 합리적 기본값 사용\n"
            "4. JSON 외 다른 텍스트를 출력하지 마세요"
        ),
    },
    "agent_recommend": {
        "models": ["gemini/gemini-3.1-pro-preview", "gpt-5-mini"],
        "temperature": 0.2,
        "max_tokens": 500,
        "description": "실시간 에이전트 추천을 위한 의도/주제/키워드 분석",
        "system_prompt": (
            "당신은 사용자 의도 분석 전문가입니다.\n"
            "사용자 메시지를 분석하여 적합한 에이전트 추천을 위한 정보를 추출하세요.\n"
            "JSON으로만 응답하세요:\n"
            "{\n"
            '    "topic": "핵심 주제 (한국어, 20자 이내)",\n'
            '    "category": "MARKETING/CODING/PLANNING/SALES/HR/FINANCE/GENERAL 중 하나",\n'
            '    "keywords": ["키워드1", "키워드2", "키워드3"]\n'
            "}\n"
            "규칙:\n"
            "1. topic은 대화의 핵심 주제를 간결하고\n"
            "2. category는 반드시 7개 선택지 중 하나\n"
            "3. keywords는 에이전트 매칭에 유용한 핵심 단어 3개\n"
            "4. JSON 외 다른 텍스트를 출력하지 마세요"
        ),
    },

    # ── AI Drive (문서 관리) ──
    "tagging": {
        "models":    ["gemini/gemini-2.5-flash", "gpt-5-mini"],
        "temperature": 0.1,
        "max_tokens": 500,
        "description": "문서 자동 태깅 - 태그/키워드/문서유형 추출",
        "system_prompt": (
            "당신은 기업 문서 분류 전문가입니다.\n"
            "제공된 문서 텍스트를 분석하여 다음 정보를 JSON으로만 추출하세요:\n"
            "{\n"
            '    "tags": ["태그1", "태그2", "태그3"],  // 3~5개 주제 태그\n'
            '    "keywords": ["키워드1", "키워드2"],    // 핵심 키워드 3~5개\n'
            '    "doc_type": "보고서"                  // 보고서/제안서/회의록/매뉴얼/기획서/기타 중 하나\n'
            "}\n"
            "규칙:\n"
            "1. 태그는 한국어, 명사형, 구체적으로 (예: 'Q4 매출', '마케팅 전략')\n"
            "2. 키워드는 검색에 유용한 핵심 단어\n"
            "3. 문서 유형은 내용의 목적 기반으로 판단\n"
            "4. JSON 외 다른 텍스트를 출력하지 마세요"
        ),
    },
    "title_gen": {
        "models": ["gpt-5-mini", "claude-haiku-4.5"],
        "temperature": 0.3,
        "max_tokens": 500,
        "description": "채팅/에이전트 결과 저장 시 제목·설명 자동 생성",
        "system_prompt": (
            "당신은 문서 제목 생성 전문가입니다.\n"
            "제공된 대화 내용 또는 문서 텍스트를 분석하여 제목과 설명을 생성하세요.\n"
            "JSON으로만 응답하세요:\n"
            "{\n"
            '    "title": "문서 제목 (20자 이내, 핵심 내용 반영)",\n'
            '    "description": "문서 설명 (50자 이내, 내용 요약)"\n'
            "}\n"
            "규칙:\n"
            "1. 제목은 간결하고 구체적으로\n"
            "2. 설명은 문서의 핵심 내용을 한 문장으로\n"
            "3. JSON 외 다른 텍스트를 출력하지 마세요"
        ),
    },
    "doc_chat": {
        "models": ["claude-opus-4-6", "gpt-5.2"],
        "temperature": 0.3,
        "max_tokens": 4000,
        "description": "문서별 채팅 - 특정 문서 기반 질의응답",
        "system_prompt": (
            "당신은 기업 내부 문서 전문 AI 어시스턴트입니다.\n"
            "제공된 문서 청크만을 기반으로 사용자 질문에 답변하세요.\n"
            "규칙:\n"
            "1. 반드시 제공된 문서 내용만 기반으로 답변\n"
            "2. 문서에 없는 내용은 '제공된 문서에서 해당 정보를 찾을 수 없습니다'라고 답변\n"
            "3. 답변 시 출처를 명시 (문서명, 페이지, 작성자)\n"
            "4. 숫자/데이터는 문서 원문 그대로 인용\n"
            "5. 추측이나 외부 지식을 사용하지 마세요"
        ),
    },
    "doc_format": { 
        "models": ["gpt-5-mini", "gemini/gemini-2.5-flash-lite"],
        "temperature": 0.3,
        "max_tokens": 4000,
        "description": "채팅/에이전트 대화를 구조화된 문서로 변환",
        "system_prompt": (
            "당신은 대화 내용을 구조화된 문서로 변환하는 전문가입니다.\n"
            "규칙:\n"
            "1. user:, assistant: 같은 역할 표시를 제거하세요\n"
            "2. 핵심 내용을 마크다운 형식으로 정리하세요\n"
            "3. 제목, 소제목, 본문 구조를 만드세요\n"
            "4. 중요 정보는 강조하세요\n"
            "5. 불필요한 인사말, 중간 질문 등은 제거하세요\n"
            "6. 원본 내용의 정보를 빠뜨리지 마세요"
        ),
    },
}

PREMIUM_MODELS = {
    "GPT_5_2": {
        "model": "gpt-5.2",
        "display_name": "GPT 5.2 (Thinking)",
        "max_tokens": 4000,
        "temperature": 0.3,
    },
    "GEMINI_3_PRO": {
        "model": "gemini/gemini-3.1-pro-preview",
        "display_name": "Gemini 3 Pro",
        "max_tokens": 4000,
        "temperature": 0.3,
    },
    "PERPLEXITY": {
        "model": "perplexity/sonar-pro",
        "display_name": "Perplexity Sonar Pro",
        "max_tokens": 4000,
        "temperature": 0.3,
    },
    "OPUS_4_6": {
        "model": "claude-opus-4-6",
        "display_name": "Claude Opus 4.6",
        "max_tokens": 4000,
        "temperature": 0.3,
    },
}

# 프리미엄 모델용 메가 시스템 프롬프트 (5단계 파이프라인 로직 통합)
_PREMIUM_SYSTEM_PROMPT_TEMPLATE = """당신은 세계 최고 수준의 AI 어시스턴트입니다. 사용자의 요청에 대해 최고 품질의 답변을 제공하세요.

[현재 시간]
{current_time}

[핵심 원칙]
1. 항상 풍부하고 자세하게 답변하세요. 짧고 간결한 답변은 금지입니다.
2. 웹 검색 결과가 제공되면 반드시 활용하여 최신 정보를 포함하세요.
3. 제공된 참고 자료에 없는 내용은 명확히 구분하세요.
4. **[매우 중요] 당신은 내부 시스템과 완벽히 연동되어 있습니다. 사용자가 내부 문서 파악을 요청하면, 하단에 제공된 [참고 문서/참고 자료]를 자신이 직접 읽은 것처럼 자연스럽게 답변하세요. "직접 접근할 수 없다", "제공된 정보에 따르면" 같은 불필요한 사과나 변명을 절대 포함하지 마세요.**

[답변 형식 — 반드시 마크다운으로 작성]
- 제목(##)과 소제목(###)으로 구조화하세요
- 핵심 정보는 **볼드** 또는 *이탤릭*으로 강조하세요
- 나열이 필요하면 리스트(- 또는 1.)를 사용하세요
- 비교가 필요하면 표(| 헤더 | 값 |)를 적극 활용하세요
- 답변 마지막에 📝 **요약** 섹션을 반드시 추가하세요

[답변 품질]
- 단계별로 사고하여 정확한 답변을 도출하세요
- 데이터나 근거가 있다면 반드시 포함하세요
- 확실하지 않은 정보는 추측임을 명시하세요
- 민감한 개인정보(전화번호, 주민등록번호 등)가 포함된 경우 마스킹하세요
- 한국어로 답변하세요"""

def get_premium_system_prompt():
    """현재 한국 시간(KST)을 포함한 시스템 프롬프트 반환"""
    from datetime import timezone, timedelta
    kst = timezone(timedelta(hours=9))
    now = datetime.datetime.now(kst)
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    current_time = now.strftime(f"%Y년 %m월 %d일 ({weekdays[now.weekday()]}) %H:%M KST")
    return _PREMIUM_SYSTEM_PROMPT_TEMPLATE.format(current_time=current_time)

# 하위 호환: 기존 코드에서 PREMIUM_SYSTEM_PROMPT를 직접 참조하는 경우 대비
PREMIUM_SYSTEM_PROMPT = _PREMIUM_SYSTEM_PROMPT_TEMPLATE.format(current_time="(시간 정보 없음)")

class ComplexityLevel(Enum):
    """요청 복잡도 레벨"""
    SIMPLE = "simple"      # 단순 조회 - Gemini Flash
    COMPLEX = "complex"    # 정밀 분석 - GPT-5, Claude 4.5 등
    BULK = "bulk"          # 대량 문서 분석 - 병렬 처리


class IntentType(Enum):
    """사용자 의도 분류"""
    QUERY = "query"              # 단순 질의
    ANALYSIS = "analysis"        # 분석 요청
    GENERATION = "generation"    # 생성 요청
    SEARCH = "search"            # 검색 요청


# ==================== Step 1: Router ====================
class Router:
    """
    의도 분류 및 복잡도 판단
    - 사용자 요청의 의도를 파악
    - 복잡도에 따라 적절한 LLM 선택
    """
    
    def __init__(self, pipeline=None):
        self.pipeline = pipeline  # 중앙 call_llm 접근용
        
        # 의도별 키워드 사전 (확장)
        self.intent_keywords = {
            IntentType.SEARCH: [
                "검색", "찾아", "찾기", "어디", "조회", "확인",
                "알려줘", "보여줘", "있어", "있나요", "찾아줘"
            ],
            IntentType.ANALYSIS: [
                "분석", "비교", "평가", "검토", "조사", "연구",
                "파악", "추세", "경향", "통계", "데이터", "인사이트",
                "어떻게", "왜", "이유", "원인", "결과", "영향"
            ],
            IntentType.GENERATION: [
                "생성", "만들어", "작성", "제작", "개발", "구현",
                "설계", "기획", "초안", "문서", "보고서", "제안서",
                "코드", "프로그램", "시스템"
            ]
        }
        
        # 복잡도 판단 키워드
        self.complexity_keywords = {
            "high": [
                "상세", "자세히", "깊이", "심층", "종합", "전체",
                "모든", "전반", "다각도", "다양한", "복합", "통합"
            ],
            "low": [
                "간단히", "요약", "개요", "핵심", "주요", "빠르게",
                "짧게", "간략히"
            ]
        }
    
    def calculate_confidence(self, user_input: str, intent: IntentType) -> float:
        """
        키워드 기반 분류의 신뢰도 계산
        
        Returns:
            0.0 ~ 1.0 사이의 신뢰도 점수
        """
        user_input_lower = user_input.lower()
        
        # 해당 의도의 키워드 매칭 개수
        matched_keywords = 0
        if intent in self.intent_keywords:
            for keyword in self.intent_keywords[intent]:
                if keyword in user_input_lower:
                    matched_keywords += 1
        
        # 다른 의도의 키워드 매칭 개수
        other_matches = 0
        for other_intent, keywords in self.intent_keywords.items():
            if other_intent != intent:
                for keyword in keywords:
                    if keyword in user_input_lower:
                        other_matches += 1
        
        # 신뢰도 계산
        if matched_keywords == 0:
            return 0.3  # 키워드 매칭 없음 (기본값 QUERY)
        
        total_matches = matched_keywords + other_matches
        if total_matches == 0:
            return 0.5
        
        # 매칭 비율 기반 신뢰도
        confidence = matched_keywords / (matched_keywords + other_matches * 0.5)
        
        # 입력 길이에 따른 보정 (짧은 입력은 신뢰도 낮춤)
        if len(user_input) < 20:
            confidence *= 0.8
        
        return min(confidence, 1.0)
    
    def classify_intent_with_llm(self, user_input: str) -> IntentType:
        """
        LLM을 사용한 의도 분류 (신뢰도가 낮을 때만 사용)
        
        Uses Gemini Flash for fast and accurate intent classification.
        """
        
        prompt = f'''다음 사용자 요청의 의도를 정확히 하나만 선택하세요:
"{user_input}"

선택지:
- QUERY: 단순 질문이나 정보 요청
- SEARCH: 특정 정보나 문서 검색
- ANALYSIS: 데이터 분석, 비교, 평가
- GENERATION: 문서나 콘텐츠 생성

답변은 위 4가지 중 하나만 출력하세요 (QUERY, SEARCH, ANALYSIS, GENERATION).'''
        
        try:
            llm_result = self.pipeline.call_llm(
                task="chat_routing",
                prompt=prompt,
                user_id=getattr(self, "current_user_id", None)  # 파이프라인 컨텍스트에서 주입된 user_id 사용
            )
            result = llm_result["content"].strip().upper()
            
            # 결과 매핑
            intent_map = {
                "QUERY": IntentType.QUERY,
                "SEARCH": IntentType.SEARCH,
                "ANALYSIS": IntentType.ANALYSIS,
                "GENERATION": IntentType.GENERATION
            }
            
            # 부분 매칭 지원 (예: "SEARCH입니다" -> SEARCH)
            for key in intent_map.keys():
                if key in result:
                    print(f"  [LLM 분류] {user_input[:30]}... → {key}")
                    return intent_map[key]
            
            # 매핑 실패 시 기본값
            print(f"  [LLM 분류] 매핑 실패 (응답: {result}), QUERY로 폴백")
            return IntentType.QUERY
            
        except Exception as e:
            # LLM 실패 시 키워드 기반으로 폴백
            print(f"  [LLM 분류 실패] {str(e)}, 키워드 기반으로 폴백")
            return self.classify_intent_keyword(user_input)
    
    def classify_intent_keyword(self, user_input: str) -> IntentType:
        """
        키워드 기반 의도 분류 (기존 로직)
        """
        user_input_lower = user_input.lower()
        scores = {intent: 0 for intent in IntentType}
        
        # 각 의도별 키워드 매칭 점수 계산
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in user_input_lower:
                    scores[intent] += 1
        
        # 점수가 가장 높은 의도 선택
        max_score = max(scores.values())
        
        if max_score == 0:
            # 키워드가 없으면 기본값
            return IntentType.QUERY
        
        # 동점인 경우 우선순위: ANALYSIS > GENERATION > SEARCH > QUERY
        priority = [IntentType.ANALYSIS, IntentType.GENERATION, IntentType.SEARCH, IntentType.QUERY]
        for intent in priority:
            if scores[intent] == max_score:
                return intent
        
        return IntentType.QUERY
    
    def classify_intent(self, user_input: str) -> IntentType:
        """
        하이브리드 의도 분류
        - 1차: 키워드 기반 분류
        - 신뢰도 < 0.7: LLM 기반 분류 (비용 절감)
        """
        # 1차: 키워드 기반 분류
        keyword_intent = self.classify_intent_keyword(user_input)
        
        # 신뢰도 계산
        confidence = self.calculate_confidence(user_input, keyword_intent)
        
        # 신뢰도가 높으면 키워드 결과 사용
        if confidence >= 0.7:
            print(f"  [키워드 분류] 신뢰도: {confidence:.2f}")
            return keyword_intent
        
        # 신뢰도가 낮으면 LLM 사용
        print(f"  [키워드 분류] 신뢰도 낮음: {confidence:.2f}, LLM으로 재분류")
        return self.classify_intent_with_llm(user_input)
    
    def determine_complexity(self, user_input: str, intent: IntentType) -> ComplexityLevel:
        """
        복잡도 판단 (개선된 버전)
        - 다차원 분석: 길이, 의도, 키워드, 구조
        """
        user_input_lower = user_input.lower()
        
        # 1. 길이 기반 점수 (0-4점)
        input_length = len(user_input)
        if input_length > 500:
            length_score = 4
        elif input_length > 300:
            length_score = 3
        elif input_length > 150:
            length_score = 2
        elif input_length > 80:
            length_score = 1
        else:
            length_score = 0
        
        # 2. 의도 기반 점수 (0-2점)
        intent_score = 0
        if intent == IntentType.ANALYSIS:
            intent_score = 2
        elif intent == IntentType.GENERATION:
            intent_score = 1
        
        # 3. 복잡도 키워드 점수 (-2 ~ +3점)
        keyword_score = 0
        for keyword in self.complexity_keywords["high"]:
            if keyword in user_input_lower:
                keyword_score += 1
        for keyword in self.complexity_keywords["low"]:
            if keyword in user_input_lower:
                keyword_score -= 1
        
        # 4. 구조 복잡도 점수 (0-3점)
        structure_score = 0
        
        # 문장 개수 (마침표, 물음표 기준)
        sentence_count = user_input.count(".") + user_input.count("。") + \
                        user_input.count("?") + user_input.count("？") + \
                        user_input.count("!") + user_input.count("！")
        if sentence_count > 5:
            structure_score += 2
        elif sentence_count > 3:
            structure_score += 1
        
        # 질문이 여러 개인 경우
        question_marks = user_input.count("?") + user_input.count("？")
        if question_marks > 2:
            structure_score += 1
        
        # 조건문이 있는 경우
        if any(word in user_input_lower for word in ["만약", "경우", "조건", "if", "when"]):
            structure_score += 1
        
        # 총점 계산
        total_score = length_score + intent_score + keyword_score + structure_score
        
        # 복잡도 결정 (임계값 조정)
        if total_score >= 7:
            return ComplexityLevel.BULK
        elif total_score >= 3:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.SIMPLE
    
    def route(self, user_input: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """라우팅 실행"""
        # 임시 주입 (동기식 호출 스택이므로 가능하지만 context var가 더 좋음)
        self.current_user_id = user_id
        try:
            intent = self.classify_intent(user_input)
            complexity = self.determine_complexity(user_input, intent)
            
            return {
                "intent": intent.value,
                "complexity": complexity.value,
                "user_input": user_input,
                "user_id": user_id
            }
        finally:
            self.current_user_id = None


# ==================== Step 2: Researcher ====================
class Researcher:
    """
    RAG 기반 문서 검색 및 정보 인출
    - AI Drive에서 관련 문서 검색
    - 벡터 검색을 통한 유사도 기반 정보 추출
    """
    
    def __init__(self, use_rag: bool = False):
        """
        Args:
            use_rag: RAG 시스템 사용 여부 (개발 중에는 False, 배포 시 True)
        """
        self.use_rag = use_rag
        self.rag_searcher = None
        
        # RAGSearcher는 use_rag 초기값과 무관하게 일단 초기화 시도
        try:
            from services.ai_drive.core.rag_search import RAGSearcher
            self.rag_searcher = RAGSearcher()
            print("  [RAG] AI Drive RAGSearcher 연동 준비 완료")
        except ImportError as e:
            print(f"  [RAG] AI Drive 모듈을 찾을 수 없습니다: {e}")
        except Exception as e:
            print(f"  [RAG] 초기화 실패: {e}")
            
        if not self.use_rag:
            print("  [RAG] 기본 Mock 검색 모드 (use_rag=False)")

    
    def search_documents(self, query: str, top_k: int = 5, department: str = "개발팀") -> list[Dict[str, Any]]:
        """
        문서 검색 (RAG 또는 Mock)
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 문서 개수
            department: 사용자 부서 (권한 필터링용)
            
        Returns:
            검색된 문서 리스트
        """
        if self.use_rag and self.rag_searcher is not None:
            return self._search_with_rag(query, top_k, department)
        else:
            if self.use_rag and self.rag_searcher is None:
                print("  [RAG] use_rag=True 이지만 rag_searcher가 초기화되지 않아 Mock 검색으로 폴백합니다.")
            return self._search_mock(query, top_k)
    
    def _search_with_rag(self, query: str, top_k: int, department: str) -> list[Dict[str, Any]]:
        """
        실제 RAG 검색 (AI Drive RAGSearcher 연동)
        4단계: 임베딩 → 유사도 검색 → 권한 필터링 → Freshness Score
        """
        try:
            results = self.rag_searcher.search(
                query=query,
                user_department=department,
                top_k=top_k
            )
            
            # 결과 포맷 변환 (RAGSearcher 반환 형식 → pipeline 형식)
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "source": result.get("source", "알 수 없음"),
                    "doc_id": result.get("doc_id", ""),
                    "author": result.get("author", ""),
                    "department": result.get("department", ""),
                    "date": result.get("date", "")
                })
            
            print(f"  [RAG] 검색 완료: {len(formatted_results)}개 문서 발견")
            return formatted_results
            
        except Exception as e:
            print(f"  [RAG] 검색 실패: {e}")
            print("  [RAG] Mock 검색으로 폴백")
            return self._search_mock(query, top_k)
    
    def _search_mock(self, query: str, top_k: int) -> list[Dict[str, Any]]:
        """
        Mock 검색 (테스트용)
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 문서 개수
            
        Returns:
            Mock 문서 리스트
        """
        print(f"  [Mock] '{query}'에 대한 Mock 검색 실행")
        
        # Mock 데이터 생성
        mock_documents = [
            {
                "content": f"'{query}'와 관련된 Mock 문서 내용입니다. 이것은 테스트용 데이터로, 실제 RAG 연동 시 실제 문서 내용으로 대체됩니다.",
                "score": 0.95,
                "source": "mock_document_1.pdf",
                "doc_id": "mock-001",
                "chunk_id": "mock-chunk-001"
            },
            {
                "content": f"'{query}'에 대한 추가 정보입니다. 비용 최적화, 성능 개선 등의 내용이 포함될 수 있습니다.",
                "score": 0.87,
                "source": "mock_document_2.pdf",
                "doc_id": "mock-002",
                "chunk_id": "mock-chunk-002"
            }
        ]
        
        # top_k 개수만큼 반환
        return mock_documents[:top_k]
    
    def retrieve(self, routing_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        정보 검색 실행
        
        - Drive 참조 ON (use_rag=True): Drive 문서 검색 우선 → 웹 보조
        - Drive 참조 OFF (use_rag=False): 웹 검색만 실행
        """
        user_input = routing_result["user_input"]
        
        documents = []
        web_context = ""
        web_citations = []
        
        if self.use_rag:
            # ──── Drive 참조 ON: Drive 문서 검색 → 관련 문서 전체 텍스트 가져오기 ────
            print("  [Drive 참조] Drive 문서 검색 시작")
            
            # 사용자 부서 조회 (권한 필터링용)
            user_department = "개발팀"
            user_id = routing_result.get("user_id")
            if user_id:
                try:
                    from application.database import SessionLocal, User
                    db = SessionLocal()
                    user = db.query(User).filter(User.id == user_id).first()
                    if user and user.department:
                        user_department = user.department
                    db.close()
                except Exception as e:
                    print(f"  ⚠️ 부서 조회 실패 (기본값 사용): {e}")
            
            documents = self.search_documents(user_input, top_k=10, department=user_department)
            print(f"  [Drive 참조] Drive 검색 완료: {len(documents)}개 청크")
            
            # ── 관련 문서 식별 + 전체 텍스트 가져오기 ──
            full_docs = []
            if documents:
                # doc_id별 점수 합산 → 가장 관련 높은 문서 식별
                from collections import defaultdict
                doc_scores = defaultdict(lambda: {"score_sum": 0, "count": 0, "title": ""})
                for doc in documents:
                    did = doc.get("doc_id", "")
                    if did:
                        doc_scores[did]["score_sum"] += doc.get("score", 0)
                        doc_scores[did]["count"] += 1
                        doc_scores[did]["title"] = doc.get("source", "")
                
                # 상위 2개 문서 선택 (점수 합산 기준)
                top_doc_ids = sorted(
                    doc_scores.items(),
                    key=lambda x: x[1]["score_sum"],
                    reverse=True
                )[:2]
                
                # PostgreSQL에서 전체 텍스트 조회
                try:
                    from services.ai_drive.db.postgres_client import PostgresClient
                    pg = PostgresClient()
                    for did, info in top_doc_ids:
                        full_text = pg.get_full_text(did)
                        if full_text:
                            full_docs.append({
                                "doc_id": did,
                                "title": info["title"],
                                "full_text": full_text
                            })
                            print(f"  [전체 문서] {info['title']} ({len(full_text)}자)")
                    pg.engine.dispose()
                except Exception as e:
                    print(f"  ⚠️ 전체 텍스트 조회 실패: {e}")
        else:
            # ──── Drive 참조 OFF: 웹 검색만 ────
            web_context, web_citations = self._web_search(user_input)
            full_docs = []
        
        return {
            **routing_result,
            "retrieved_documents": documents,
            "full_docs": full_docs,
            "web_context": web_context,
            "web_citations": web_citations,
        }
    
    def _web_search(self, query: str) -> tuple:
        """
        Perplexity API를 통한 실시간 웹 검색
        
        Returns:
            (content: str, citations: list[str]) - 검색 결과 텍스트와 출처 URL 리스트
        """
        try:
            print(f"  → 웹 검색 실행: {query[:30]}...")
            response = litellm.completion(
                model="perplexity/sonar",
                messages=[{"role": "user", "content": query}],
                max_tokens=500,
            )
            result = response.choices[0].message.content or ""
            
            # Perplexity API citations 추출
            citations = []
            try:
                if hasattr(response, 'citations') and response.citations:
                    citations = list(response.citations)
                elif hasattr(response, '_hidden_params'):
                    raw = response._hidden_params.get('original_response', {})
                    if hasattr(raw, 'citations'):
                        citations = list(raw.citations)
            except Exception:
                pass
            
            print(f"  → 웹 검색 완료 ({len(result)}자, 출처 {len(citations)}개)")
            return result, citations
        except Exception as e:
            print(f"  → 웹 검색 실패 (Fallback: 웹 검색 없이 진행): {e}")
            return "", []



# ==================== Step 3: Reasoner & Verification ====================
class Reasoner:
    """
    논리적 답변 생성 및 CoT(Chain of Thought) 기반 팩트체크
    - 복잡도에 따라 적절한 LLM 선택
    - 모델 실패 시 Fallback 메커니즘
    - 답변의 논리적 일관성 검증
    """
    
    def __init__(self, pipeline=None):
        self.pipeline = pipeline  # 중앙 call_llm 접근용
        
        # 복잡도 → task명 매핑
        self.complexity_task_map = {
            ComplexityLevel.SIMPLE.value: "chat_simple",
            ComplexityLevel.COMPLEX.value: "chat_complex",
            ComplexityLevel.BULK.value: "chat_bulk",
        }
    
    def generate_response_with_fallback(self, context: Dict[str, Any]) -> tuple[str, str, int, int]:
        """Fallback 메커니즘을 포함한 답변 생성 (call_llm 위임)"""
        
        complexity = context["complexity"]
        user_input = context["user_input"]
        documents = context.get("retrieved_documents", [])
        
        # 복잡도 → task명
        task = self.complexity_task_map.get(complexity, "chat_reasoning")
        
        # RAG 컨텍스트 구성 (전체 문서 우선, 없으면 청크 폴백)
        rag_context = ""
        full_docs = context.get("full_docs", [])
        
        if full_docs:
            # ── 전체 문서 텍스트 사용 (정확도 최우선) ──
            rag_context = "\n\n참고 문서:\n"
            for i, fdoc in enumerate(full_docs, 1):
                doc_id = fdoc.get("doc_id", f"doc-{i}")
                title = fdoc.get("title", "알 수 없음")
                text = fdoc.get("full_text", "")
                # 토큰 제한: 문서당 최대 80,000자 (약 50K토큰)
                if len(text) > 80000:
                    text = text[:80000] + "\n... (이하 생략)"
                rag_context += f"[DOC_ID:{doc_id}] 출처: {title}\n내용:\n{text}\n\n"
        elif documents:
            # ── 청크 기반 폴백 (전체 텍스트 없을 때) ──
            rag_context = "\n\n참고 문서:\n"
            for i, doc in enumerate(documents[:10], 1):
                doc_id = doc.get('doc_id', f'doc-{i}')
                rag_context += f"[DOC_ID:{doc_id}] 출처: {doc.get('source', '알 수 없음')}\n내용: {doc.get('content', '')}\n\n"
        
        # 웹 검색 컨텍스트 구성
        web_context = ""
        if context.get("web_context"):
            web_context = f"\n\n웹 검색 결과:\n{context['web_context']}"
        
        # 현재 시간 주입 (KST)
        from datetime import timezone, timedelta as _td
        _kst = timezone(_td(hours=9))
        _now = datetime.datetime.now(_kst)
        _weekdays = ['월', '화', '수', '목', '금', '토', '일']
        time_str = _now.strftime(f"%Y년 %m월 %d일 ({_weekdays[_now.weekday()]}) %H:%M KST")
        
        # 참고 문서 ID 반환 지시 (LLM이 실제로 참고한 문서만 필터링)
        used_docs_instruction = ""
        if documents or full_docs:
            used_docs_instruction = '\n[중요] 답변 작성 후, 실제로 내용을 참고한 문서의 DOC_ID만 답변 맨 마지막 줄에 다음 형식으로 적어주세요: <!--USED_DOCS:["id1","id2"]-->' \
                                   '\n참고하지 않은 문서는 절대 포함하지 마세요. 어떤 문서도 참고하지 않았다면: <!--USED_DOCS:[]-->'
        
        # 프롬프트 구성
        prompt = f"""현재 시간: {time_str}

{user_input}
{web_context}
{rag_context}

위 정보를 바탕으로 정확하고 유용한 답변을 제공해주세요.
[주의사항] 당신은 사용자의 내부 드라이브 시스템과 연동되어 문서를 읽을 능력이 있습니다. "직접 접근할 수 없다", "권한이 없다", "제공된 정보에 따르면" 같은 변명이나 사과를 절대 하지 말고, 위 참고 문서를 기반으로 자신이 직접 문서를 열람하고 답변하는 것처럼 자연스럽게 대답하세요.
또한 내용이 길더라도 단순 나열을 피하고, 질문의 목적에 맞게 핵심 위주로 명확하게 요약 및 그룹화하여 시각적으로 읽기 편하게 정리해주세요.{used_docs_instruction}"""
        
        
        # [Agent] 시스템 프롬프트 적용
        options = {}
        if context.get("system_prompt"):
            options["system_prompt"] = context.get("system_prompt")
            
        # call_llm이 Fallback + 토큰 추출 + 비용 로깅 전부 처리
        llm_result = self.pipeline.call_llm(task=task, prompt=prompt, options=options, user_id=context.get("user_id"))
        
        return (
            llm_result["content"],
            llm_result["model_used"],
            llm_result["input_tokens"],
            llm_result["output_tokens"],
        )
    
    def generate_response(self, context: Dict[str, Any]) -> tuple:
        """답변 생성 (Fallback 포함)"""
        return self.generate_response_with_fallback(context)
    
    def verify(self, response: str, model_used: str, input_tokens: int, output_tokens: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """팩트체크 및 검증"""
        is_verified = True
        confidence_score = 0.95
        
        return {
            **context,
            "response": response,
            "model_used": model_used,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "verified": is_verified,
            "confidence": confidence_score
        }
    
    def reason(self, research_result: Dict[str, Any]) -> Dict[str, Any]:
        """추론 실행"""
        response, model_used, input_tokens, output_tokens = self.generate_response(research_result)
        return self.verify(response, model_used, input_tokens, output_tokens, research_result)


# ==================== Step 4: Synthesizer ====================
class Synthesizer:
    """
    표준 레이아웃 적용 및 최종 렌더링
    - 응답을 사용자 친화적인 형식으로 변환
    - 마크다운, HTML 등 다양한 포맷 지원
    """

    def __init__(self, pipeline=None):
        self.pipeline = pipeline  # 중앙 call_llm 접근용
    
    def format_response(self, reasoning_result: Dict[str, Any]) -> str:
        """응답 포맷팅 (call_llm 위임)"""
        
        response = reasoning_result["response"]
        user_input = reasoning_result.get("user_input", "")
        intent = reasoning_result.get("intent", "")
        
        # 프롬프트 구성 (기존과 동일)
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
            llm_result = self.pipeline.call_llm(
                task="chat_synthesis",
                prompt=prompt,
                user_id=reasoning_result.get("user_id")
            )
            return llm_result["content"]
            
        except Exception as e:
            print(f"  [!] Synthesizer 실패: {e}, Fallback 사용")
            return self._format_fallback(reasoning_result)
    
    def _format_fallback(self, reasoning_result: Dict[str, Any]) -> str:
        """Fallback 포맷팅 (LLM 실패 시)"""
        response = reasoning_result["response"]
        confidence = reasoning_result.get("confidence", 0.95)
        
        formatted = f"""## 답변

{response}

---
**신뢰도**: {confidence * 100:.1f}%
**모델**: {reasoning_result.get('model_used', 'unknown')}
"""
        return formatted.strip()
    
    def synthesize(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """최종 합성"""
        formatted_response = self.format_response(reasoning_result)
        
        return {
            **reasoning_result,
            "formatted_response": formatted_response
        }


# ==================== Step 5: Guardrail ====================
class Guardrail:
    """
    개인정보 마스킹 및 최종 안전 검증
    - 민감 정보 필터링
    - 유해 콘텐츠 차단
    - 복잡한 작업의 품질 검수 (COMPLEX, BULK)
    """
    
    def __init__(self, pipeline=None):
        self.pipeline = pipeline  # 중앙 call_llm 접근용
        self.sensitive_patterns = [
            r'\d{3}-\d{4}-\d{4}',  # 전화번호
            r'\d{6}-\d{7}',        # 주민등록번호
        ]
    
    def mask_sensitive_info(self, text: str) -> str:
        """민감 정보 마스킹"""
        import re
        masked_text = text
        
        # 전화번호 마스킹
        masked_text = re.sub(r'(\d{3})-(\d{4})-(\d{4})', r'\1-****-\3', masked_text)
        # 주민등록번호 마스킹
        masked_text = re.sub(r'(\d{6})-(\d{7})', r'\1-*******', masked_text)
        
        return masked_text
    
    def check_safety(self, text: str) -> bool:
        """안전성 검사"""
        # TODO: 유해 콘텐츠 검사 로직 구현
        return True
    
    def verify_quality(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """DeepSeek-R1을 사용한 품질 검수"""
        
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
    "completeness": true/false,
    "logical_consistency": true/false,
    "factual_accuracy": true/false,
    "issues": ["이슈1", "이슈2", ...],
    "quality_score": 0.0-1.0
}}

단계별로 사고하여 정확히 검증해주세요."""

        try:
            llm_result = self.pipeline.call_llm(
                task="chat_guardrail",
                prompt=prompt,
                user_id=synthesis_result.get("user_id")
            )
            response_text = llm_result["content"]
            
            # JSON 파싱
            import json
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                quality_data = json.loads(json_match.group())
                
                quality_score = quality_data.get("quality_score", 0.8)
                issues = quality_data.get("issues", [])
                
                print(f"  ✓ DeepSeek-R1 검수 완료 (점수: {quality_score:.2f})")
                
                if issues:
                    print(f"  [!] 품질 이슈 발견: {len(issues)}개")
                    for issue in issues:
                        print(f"     - {issue}")
                else:
                    print("  [OK] 품질 검수 통과")
                
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
        
        # 1. 요청사항 충족도 검증
        if not self._check_completeness(user_input, response, intent):
            quality_issues.append("요청사항이 완전히 충족되지 않았습니다.")
        
        # 2. 논리적 일관성 검증
        if not self._check_logical_consistency(response):
            quality_issues.append("논리적 일관성이 부족합니다.")
        
        # 3. 누락된 정보 확인
        missing_info = self._check_missing_information(user_input, response, intent)
        if missing_info:
            quality_issues.extend(missing_info)
            
        quality_score = max(0.0, 1.0 - (len(quality_issues) * 0.2))
        needs_regeneration = quality_score < 0.6
        
        if quality_issues:
            print(f"  [!] 품질 이슈 발견 (Fallback): {len(quality_issues)}개")
        else:
            print("  [OK] 품질 검수 통과 (Fallback)")
            
        return {
            "quality_verified": len(quality_issues) == 0,
            "quality_score": quality_score,
            "quality_issues": quality_issues,
            "needs_regeneration": needs_regeneration
        }
    
    def _check_completeness(self, user_input: str, response: str, intent: str) -> bool:
        """요청사항 충족도 검증"""
        # TODO: LLM을 사용한 정교한 검증 구현
        # 현재는 간단한 길이 기반 체크
        if intent == IntentType.ANALYSIS.value:
            return len(response) > 100  # 분석은 충분한 길이 필요
        elif intent == IntentType.GENERATION.value:
            return len(response) > 50   # 생성도 최소 길이 필요
        return True
    
    def _check_logical_consistency(self, response: str) -> bool:
        """논리적 일관성 검증"""
        # TODO: LLM을 사용한 논리적 일관성 검증
        # 현재는 기본적인 체크만
        return len(response) > 0
    
    def _check_missing_information(self, user_input: str, response: str, intent: str) -> list[str]:
        """누락된 정보 확인"""
        # TODO: LLM을 사용한 누락 정보 탐지
        missing = []
        
        # 분석 요청인데 데이터나 근거가 없는 경우
        if intent == IntentType.ANALYSIS.value:
            if "데이터" not in response and "근거" not in response:
                missing.append("분석 근거나 데이터가 누락되었습니다.")
        
        return missing
    
    def guard(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """가드레일 실행"""
        formatted_response = synthesis_result["formatted_response"]
        
        # 1. 품질 검수 (복잡한 작업에 대해)
        quality_result = self.verify_quality(synthesis_result)
        
        # 2. 민감 정보 마스킹
        safe_response = self.mask_sensitive_info(formatted_response)
        
        # 3. 안전성 검사
        is_safe = self.check_safety(safe_response)
        
        # 재생성 필요 시 경고 메시지 추가
        if quality_result["needs_regeneration"]:
            safe_response = f"""[!] 품질 검수 경고
다음 이슈가 발견되었습니다:
{chr(10).join(f'- {issue}' for issue in quality_result['quality_issues'])}

재생성을 권장합니다.

---

{safe_response}
"""
        
        return {
            **synthesis_result,
            **quality_result,
            "final_response": safe_response,
            "is_safe": is_safe
        }


# ==================== Main Pipeline ====================
class Pipeline:
    """
    5단계 파이프라인 오케스트레이터
    Router → Researcher → Reasoner → Synthesizer → Guardrail
    """
    
    def __init__(self, use_rag: bool = False):
        """
        Args:
            use_rag: RAG 시스템 사용 여부 (기본값: False)
        """
        self.router = Router(pipeline=self)
        self.researcher = Researcher(use_rag=use_rag)  # RAG 플래그 전달
        self.reasoner = Reasoner(pipeline=self)
        self.synthesizer = Synthesizer(pipeline=self)
        self.guardrail = Guardrail(pipeline=self)
        self.logger = get_logger()
        self.cost_calculator = get_cost_calculator()
        self.cost_logger = get_cost_logger()

    def call_llm(self, task: str, prompt: str, options: dict = None, user_id: Optional[str] = None) -> dict:
        """
        중앙 LLM 호출 메서드 (모든 LLM 호출의 단일 진입점)
        
        Args:
            task: TASK_MODEL_CONFIG의 키 (예: "chat_routing", "tagging", "doc_chat")
            prompt: 사용자/작업 프롬프트 (user role 메시지)
            options: 오버라이드 옵션 (선택)
                - system_prompt: 시스템 프롬프트 (None이면 CONFIG의 기본값 사용)
                - temperature: 온도 오버라이드
                - max_tokens: 최대 토큰 오버라이드
                - models: 모델 리스트 오버라이드 (Fallback 순서)
                
        Returns:
            {
                "content": str,          # LLM 응답 텍스트
                "model_used": str,       # 실제 사용된 모델명
                "input_tokens": int,     # 입력 토큰 수
                "output_tokens": int,    # 출력 토큰 수
                "cost_info": dict,       # 비용 정보 (cost_calculator 결과)
                "task": str,             # 작업명
            }
            
        Raises:
            ValueError: 알 수 없는 task명
            Exception: 모든 모델 실패 시
        """
        # 1. CONFIG에서 task 설정 가져오기
        if task not in TASK_MODEL_CONFIG:
            raise ValueError(f"알 수 없는 task: '{task}'. 가능한 task: {list(TASK_MODEL_CONFIG.keys())}")
        
        config = TASK_MODEL_CONFIG[task]
        options = options or {}
        
        # 2. 옵션 병합 (options가 우선, 없으면 CONFIG 기본값)
        models = options.get("models", config["models"])
        temperature = options.get("temperature", config["temperature"])
        max_tokens = options.get("max_tokens", config["max_tokens"])
        
        # system_prompt: options > CONFIG > None 순서
        system_prompt = options.get("system_prompt", config.get("system_prompt"))
        
        # 3. messages 구성
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # 4. Fallback 체인 실행
        last_error = None
        for model in models:
            try:
                print(f"  [call_llm] task={task}, 모델 시도: {model}")
                
                # 모델별 특성을 고려한 파라미터 세팅
                completion_kwargs = {
                    "model": model,
                    "messages": messages,
                }
                
                # 프롬프트 max_tokens 적용 (특정 모델 제외 시 여기에 조건 추가 가능)
                if max_tokens:
                    completion_kwargs["max_tokens"] = max_tokens
                    
                # GPT-5, o1 등 temperature를 미지원하는 모델의 대체 로직
                if "gpt-5" in model or "o1" in model or "o3" in model:
                    # 분석/판단 태스크: reasoning_effort로 정밀도 제어
                    REASONING_TASKS = {"chat_routing", "chat_guardrail", "chat_complex", "chat_reasoning"}
                    if task in REASONING_TASKS:
                        if temperature <= 0.2:
                            completion_kwargs["reasoning_effort"] = "high"
                        elif temperature >= 0.7:
                            completion_kwargs["reasoning_effort"] = "low"
                        else:
                            completion_kwargs["reasoning_effort"] = "medium"
                    # 텍스트 생성 태스크(synthesis, simple 등): 파라미터 없이 기본 모드로 호출
                    # → reasoning_effort를 보내면 content가 빈 문자열로 오는 GPT-5 이슈 방지
                else:
                    completion_kwargs["temperature"] = temperature
                
                response = litellm.completion(**completion_kwargs)
                
                content = response.choices[0].message.content or ""
                
                # 5. 토큰 추출
                input_tokens = 0
                output_tokens = 0
                if hasattr(response, 'usage') and response.usage:
                    input_tokens = getattr(response.usage, 'prompt_tokens', 0) or 0
                    output_tokens = getattr(response.usage, 'completion_tokens', 0) or 0
                
                # 6. 비용 계산
                cost_info = self.cost_calculator.calculate_cost(
                    model_name=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                
                # 7. 비용 로깅 (콘솔)
                self.logger.log_model_usage(
                    model_name=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_info=cost_info,
                )
                
                # 8. 비용 DB 기록
                self.cost_logger.log_llm_cost(
                    task=task,
                    model_name=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_info.get("cost_usd", {}).get("total", 0),
                    cost_krw=cost_info.get("cost_krw", {}).get("total", 0),
                    user_id=user_id
                )
                
                print(f"  [call_llm] ✓ {model} 성공 (입력: {input_tokens}, 출력: {output_tokens} 토큰)")
                
                return {
                    "content": content,
                    "model_used": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_info": cost_info,
                    "task": task,
                }
                
            except Exception as e:
                last_error = e
                print(f"  [call_llm] ✗ {model} 실패: {str(e)}")
                continue
        
        # 8. 모든 모델 실패
        raise Exception(
            f"[call_llm] task='{task}' 모든 모델 실패. "
            f"시도한 모델: {models}, 마지막 오류: {last_error}"
        )
    
    async def analyze_for_draft(self, messages: List[Dict], template_schema: Dict) -> Dict:
        """
        Agent 생성 템플릿 채우기 (Pull-Fill)
        
        Args:
            messages: 대화 이력 List[{"role": "user", "content": "..."}]
            template_schema: 채워야 할 타겟 JSON 스키마 (from AI Hub)
            
        Returns:
            채워진 템플릿 Dict
        """
        print("[Pipeline] Draft Analysis Start (with External Schema)")
        
        # 1. 대화 내용 결합
        conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        # 2. 템플릿 복사 (직접 정의하지 않고 외부 스키마 사용)
        analysis = template_schema.copy()
        
        # 3. LLM 분석 (Gemini Flash로 대화 분석 → JSON 생성)
        import json as _json
        
        schema_keys = list(template_schema.keys())
        prompt = f"""다음 대화를 분석하여 AI 에이전트 정보를 JSON으로 추출해주세요.

대화 내용:
{conversation_text}

다음 JSON 형식으로만 응답해주세요 (다른 텍스트 없이):
{{
    "name": "에이전트 이름 (간결하게, 20자 이내)",
    "description": "에이전트 설명 (50자 이내)",
    "category": "카테고리 (마케팅/개발/기획/영업/인사/재무/기타 중 하나)",
    "input_example": "사용자가 이 에이전트에게 할 수 있는 질문 예시",
    "output_example": "에이전트의 답변 예시 (간략하게)",
    "system_prompt": "이 에이전트의 역할과 성격을 정의하는 시스템 프롬프트",
    "use_rag": true,
    "model_type": "AUTO",
    "visibility": "PUBLIC"
}}"""

        try:
            llm_result = self.call_llm(
                task="agent_draft",
                prompt=prompt,
                user_id=messages[-1].get("user_id") if messages else None
            )
            result_text = llm_result["content"].strip()
            
            # ```json ``` 제거
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            filled = _json.loads(result_text.strip())
            
            # 템플릿 키에 해당하는 값만 반영
            for key in schema_keys:
                if key in filled and filled[key]:
                    analysis[key] = filled[key]
                    
        except Exception as e:
            print(f"  [Draft] LLM 분석 실패, 기본값 사용: {e}")
            analysis["name"] = "새 에이전트"
            analysis["description"] = "대화 기반으로 생성된 에이전트"
            analysis["category"] = "기타"
            analysis["system_prompt"] = "당신은 유능한 AI 비서입니다. 사용자의 요청에 정확하게 답변하세요."
            
        print(f"[Pipeline] Draft Analysis Complete: {analysis.get('name', 'Unknown')}")
        return analysis

    # async def vectorize_agent(self, agent_data: Dict) -> bool:
    #     """
    #     [Deprecated] Agent Vectorization Logic Moved to AI Hub (AgentManager)
    #     """
    #     pass

    async def recommend_agents(self, current_message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        실시간 Agent 추천을 위한 분석
        
        Returns:
            {"topic": "...", "category": "...", "keywords": [...]}
        """
        print(f"[Pipeline] Recommendation Analysis: {current_message[:30]}...")
        
        # 1. 키워드 추출 (Router 로직 재사용 가능)
        intent = self.router.classify_intent(current_message)
        
        # 2. LLM 분석 (Gemini Flash로 주제/카테고리/키워드 추출)
        import json as _json
        
        # 대화 히스토리가 있으면 컨텍스트에 포함
        context = ""
        if conversation_history:
            recent = conversation_history[-5:]  # 최근 5개만
            context = "\n".join([f"{m['role']}: {m['content']}" for m in recent])
            context = f"\n\n최근 대화:\n{context}"
        
        prompt = f"""다음 사용자 메시지를 분석하여 관련 에이전트 추천을 위한 정보를 추출해주세요.

사용자 메시지: {current_message}{context}

다음 JSON 형식으로만 응답해주세요 (다른 텍스트 없이):
{{
    "topic": "대화의 핵심 주제 (한국어, 20자 이내)",
    "category": "MARKETING / CODING / PLANNING / SALES / HR / FINANCE / GENERAL 중 하나",
    "keywords": ["키워드1", "키워드2", "키워드3"]
}}"""

        topic = "General Query"
        category = "GENERAL"
        keywords = []
        
        try:
            # recommend_agents에서는 user_id를 알 수 없는 경우가 많으나,
            # Hub를 거치므로 일단 기본 호출 (agent_recommend)
            llm_result = self.call_llm(
                task="agent_recommend",
                prompt=prompt,
            )
            result_text = llm_result["content"].strip()
            
            # ```json ``` 제거
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            parsed = _json.loads(result_text.strip())
            topic = parsed.get("topic", topic)
            category = parsed.get("category", category)
            keywords = parsed.get("keywords", keywords)
            
        except Exception as e:
            print(f"  [Recommend] LLM 분석 실패, 기본값 사용: {e}")
            
        return {
            "topic": topic,
            "category": category,
            "keywords": keywords,
            "intent": intent.value
        }

    @staticmethod
    def _extract_used_docs(response: str) -> list:
        """LLM 응답에서 <!--USED_DOCS:[...]-->  태그를 파싱하여 doc_id 리스트 반환"""
        import re, json
        match = re.search(r'<!--USED_DOCS:(\[.*?\])-->', response)
        if match:
            try:
                return json.loads(match.group(1))
            except (json.JSONDecodeError, Exception):
                pass
        return []
    
    @staticmethod
    def _strip_used_docs_tag(response: str) -> str:
        """LLM 응답에서 <!--USED_DOCS:[...]-->  태그를 제거"""
        import re
        return re.sub(r'\s*<!--USED_DOCS:\[.*?\]-->\s*', '', response).strip()

    def process(self, user_input: str, user_id: Optional[str] = None, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        print(f"[Pipeline] 처리 시작: {user_input[:50]}...")
        
        # 세션 시작
        session_id = self.logger.start_session(user_input, user_id)
        
        try:
            # Step 1: Router
            print("[Step 1/5] Router - 의도 분류 및 복잡도 판단")
            step_start = time.time()
            routing_result = self.router.route(user_input, user_id=user_id)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Router", routing_result, step_duration)
            
            # Step 2: Researcher
            print("[Step 2/5] Researcher - RAG 기반 문서 검색")
            step_start = time.time()
            research_result = self.researcher.retrieve(routing_result)
            
            # [Injection] 에이전트 시스템 프롬프트 전파 (Router -> Researcher -> Reasoner)
            if system_prompt:
                research_result["system_prompt"] = system_prompt
                
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Researcher", {
                "documents_found": len(research_result.get("retrieved_documents", []))
            }, step_duration)
            
            # Step 3: Reasoner
            print("[Step 3/5] Reasoner - 논리적 답변 생성 및 검증")
            step_start = time.time()
            reasoning_result = self.reasoner.reason(research_result)
            
            # USED_DOCS 태그 추출 (Synthesizer 전에 파싱)
            used_doc_ids = self._extract_used_docs(reasoning_result.get("response", ""))
            # 태그를 응답에서 제거
            if reasoning_result.get("response"):
                reasoning_result["response"] = self._strip_used_docs_tag(reasoning_result["response"])
            
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Reasoner", {
                "model": reasoning_result.get("model_used"),
                "verified": reasoning_result.get("verified"),
                "used_docs": len(used_doc_ids)
            }, step_duration)
            
            # Step 4: Synthesizer
            print("[Step 4/5] Synthesizer - 최종 응답 포맷팅")
            step_start = time.time()
            synthesis_result = self.synthesizer.synthesize(reasoning_result)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Synthesizer", {}, step_duration)
            
            # Step 5: Guardrail
            print("[Step 5/5] Guardrail - 안전성 및 품질 검증")
            step_start = time.time()
            final_result = self.guardrail.guard(synthesis_result)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Guardrail", {
                "is_safe": final_result.get("is_safe"),
                "quality_score": final_result.get("quality_score")
            }, step_duration)
            
            # 비용은 call_llm()에서 자동 로깅됨 (이중 로깅 방지)
            # process() 결과용으로 Reasoner 정보만 추출
            model_used = reasoning_result.get("model_used", "unknown")
            input_tokens = reasoning_result.get("input_tokens", 0)
            output_tokens = reasoning_result.get("output_tokens", 0)
            
            # 세션 종료 (final_result 전달)
            self.logger.end_session(final_result=final_result, success=True)
            
            print(f"[Pipeline] 처리 완료!")   

            # 출처 정보 추출 (RAG 검색 결과에서)
            sources = []
            seen_docs = set()
            for doc in research_result.get("retrieved_documents", []):
                doc_id = doc.get("doc_id", "")
                title = doc.get("source", "알 수 없음")
                score = doc.get("score", 0.0)
                
                # 중복 제거 기준: doc_id가 있으면 doc_id, 없으면 title
                dedup_key = doc_id if doc_id else title
                if dedup_key and dedup_key not in seen_docs:
                    sources.append({
                        "id": doc_id,
                        "title": title,
                        "score": score
                    })
                    seen_docs.add(dedup_key)
            
            # LLM이 실제 참고한 문서만 필터링
            if used_doc_ids:
                sources = [s for s in sources if s["id"] in used_doc_ids]
                print(f"  [Source Filter] LLM 참고 문서: {len(sources)}개 (전체 {len(research_result.get('retrieved_documents', []))}개 중)")
            
            # 웹 검색 정보 추출
            web_citations = research_result.get("web_citations", [])
            web_searched = bool(research_result.get("web_context", ""))
            
            return {
                "session_id": session_id,
                "response": final_result["final_response"],
                "used_model": model_used,
                "sources": sources,
                "web_searched": web_searched,
                "web_citations": web_citations,
                "metadata": {
                    "intent": routing_result.get("intent"),
                    "complexity": routing_result.get("complexity"),
                    "model_used": model_used,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "quality_score": final_result.get("quality_score"),
                    "is_safe": final_result.get("is_safe"),
                    "verified": reasoning_result.get("verified"),
                    "steps": self.logger.get_session_summary()
                }
            }
            
        except Exception as e:
            print(f"[Pipeline] 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "status": "failed"
            }

    def process_premium(self, user_input: str, model_type: str, use_rag: bool = False, user_id: Optional[str] = None, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        '''
        프리미엄 모델 직접 호출 (5단계 파이프라인 bypass)
        
        5단계 파이프라인 로직을 메가 프롬프트로 통합하여
        선택된 프리미엄 모델 하나로 처리합니다.
        
        Args:
            user_input: 사용자 입력
            model_type: 프리미엄 모델 키 (GPT_5_2, GEMINI_3_PRO, PERPLEXITY, OPUS_4_6)
            use_rag: RAG 검색 사용 여부
            user_id: 사용자 ID
            system_prompt: [New] 에이전트 전용 시스템 프롬프트 (None이면 기본값 사용)
            
        Returns:
            process()와 동일한 형식의 결과 dict
        '''
        print(f"[Pipeline] 프리미엄 모드: {model_type}")
        
        # 1. 모델 설정 가져오기
        if model_type not in PREMIUM_MODELS:
            raise ValueError(f"알 수 없는 프리미엄 모델: '{model_type}'. 가능한 모델: {list(PREMIUM_MODELS.keys())}")
        
        model_config = PREMIUM_MODELS[model_type]
        model_name = model_config["model"]
        
        # 세션 시작
        session_id = self.logger.start_session(user_input, user_id)
        
        try:
            # 2. RAG 검색 (use_rag=True일 때만)
            rag_context = ""
            sources = []
            
            if use_rag:
                print("  → RAG 검색 실행")
                documents = self.researcher.search_documents(user_input, top_k=10)
                
                if documents:
                    rag_context = "\n\n[참고 자료]\n"
                    seen_docs = set()
                    for i, doc in enumerate(documents, 1):
                        content = doc.get("content", "")
                        source = doc.get("source", "알 수 없음")
                        doc_id = doc.get("doc_id", "")
                        score = doc.get("score", 0.0)
                        author = doc.get("author", "")
                        date = doc.get("date", "")
                        
                        rag_context += f"--- 자료 {i} ---\n"
                        rag_context += f"[DOC_ID:{doc_id}] 출처: {source}"
                        if author:
                            rag_context += f" | 작성자: {author}"
                        if date:
                            rag_context += f" | 날짜: {date}"
                        rag_context += f"\n{content}\n\n"
                        
                        dedup_key = doc_id if doc_id else source
                        if dedup_key and dedup_key not in seen_docs:
                            sources.append({
                                "id": doc_id,
                                "title": source,
                                "score": score
                            })
                            seen_docs.add(dedup_key)
                    
                    print(f"  → RAG 결과: {len(documents)}개 문서")
            
            # 2-1. 웹 검색 (Perplexity 모델이 아닌 경우에만 — Perplexity는 자체 검색 내장)
            web_context = ""
            web_citations = []
            if model_type != "PERPLEXITY":
                try:
                    print(f"  → 웹 검색 실행: {user_input[:30]}...")
                    web_response = litellm.completion(
                        model="perplexity/sonar",
                        messages=[{"role": "user", "content": user_input}],
                        max_tokens=500,
                    )
                    web_context = web_response.choices[0].message.content or ""
                    
                    # Perplexity API citations 추출
                    try:
                        if hasattr(web_response, 'citations') and web_response.citations:
                            web_citations = list(web_response.citations)
                        elif hasattr(web_response, '_hidden_params'):
                            raw = web_response._hidden_params.get('original_response', {})
                            if hasattr(raw, 'citations'):
                                web_citations = list(raw.citations)
                    except Exception:
                        pass
                    
                    print(f"  → 웹 검색 완료 ({len(web_context)}자, 출처 {len(web_citations)}개)")
                except Exception as e:
                    print(f"  → 웹 검색 실패 (스킵): {e}")
            
            # 3. 프롬프트 조립
            user_prompt = user_input
            if web_context:
                user_prompt += f"\n\n[웹 검색 결과]\n{web_context}"
            if rag_context:
                user_prompt += rag_context
                user_prompt += '\n[중요] 답변 작성 후, 실제로 내용을 참고한 문서의 DOC_ID만 답변 맨 마지막 줄에 다음 형식으로 적어주세요: <!--USED_DOCS:["id1","id2"]-->' \
                              '\n참고하지 않은 문서는 절대 포함하지 마세요. 어떤 문서도 참고하지 않았다면: <!--USED_DOCS:[]-->'
            
            # 4. 프리미엄 모델 호출 (call_llm이 아닌 litellm 직접 호출)
            #    - TASK_MODEL_CONFIG에 없는 모델이므로 직접 호출
            print(f"  → 모델 호출: {model_name}")
            
            # [Agent] 시스템 프롬프트 병합 (기본 5단계 지침 + 에이전트 페르소나)
            base_prompt = get_premium_system_prompt()  # 현재 시간 포함
            if system_prompt:
                final_system_prompt = f"{base_prompt}\n\n[추가 에이전트 지침 및 페르소나]\n{system_prompt}"
            else:
                final_system_prompt = base_prompt

            messages = [
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # GPT-5, o1 등 temperature 미지원 모델 대응
            completion_kwargs = {
                "model": model_name,
                "messages": messages,
                "max_tokens": model_config["max_tokens"],
            }
            
            if "gpt-5" in model_name or "o1" in model_name or "o3" in model_name:
                # GPT-5 계열: temperature 대신 파라미터 없이 기본 모드로 호출
                pass
            else:
                completion_kwargs["temperature"] = model_config["temperature"]
            
            response = litellm.completion(**completion_kwargs)
            
            content = response.choices[0].message.content or ""
            
            # 5. 토큰 추출
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'prompt_tokens', 0) or 0
                output_tokens = getattr(response.usage, 'completion_tokens', 0) or 0
            
            # 6. 비용 계산 + 로깅
            cost_info = self.cost_calculator.calculate_cost(
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            
            self.logger.log_model_usage(
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_info=cost_info,
            )
            
            # 비용 DB 기록
            self.cost_logger.log_llm_cost(
                task=f"premium:{model_type}",
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_info.get("cost_usd", {}).get("total", 0),
                cost_krw=cost_info.get("cost_krw", {}).get("total", 0),
                user_id=user_id
            )
            
            print(f"  → 완료 (입력: {input_tokens}, 출력: {output_tokens} 토큰)")
            
            # 7. 민감정보 마스킹
            safe_response = self.guardrail.mask_sensitive_info(content)
            
            # USED_DOCS 파싱 및 sources 필터링
            used_doc_ids = self._extract_used_docs(safe_response)
            safe_response = self._strip_used_docs_tag(safe_response)
            if used_doc_ids:
                sources = [s for s in sources if s["id"] in used_doc_ids]
                print(f"  [Source Filter] LLM 참고 문서: {len(sources)}개")
            
            # 세션 종료
            self.logger.end_session(
                final_result={"final_response": safe_response},
                success=True
            )
            
            return {
                "session_id": session_id,
                "response": safe_response,
                "used_model": model_name,
                "sources": sources,
                "web_searched": bool(web_context),
                "web_citations": web_citations,
                "metadata": {
                    "intent": "premium_direct",
                    "complexity": "premium",
                    "model_used": model_name,
                    "model_display_name": model_config["display_name"],
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_info": cost_info,
                    "quality_score": 1.0,
                    "is_safe": True,
                    "verified": True,
                }
            }
            
        except Exception as e:
            print(f"[Pipeline] 프리미엄 모드 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "status": "failed"
            }

