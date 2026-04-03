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
import re

# 환경 변수 로드
load_dotenv()

# ==================== 중앙 모델 설정 (TASK_MODEL_CONFIG) ====================
# 모든 LLM 호출은 이 설정을 통해 관리됩니다.
# models[0] = 후보 모델 (Primary), models[1] = 대체 모델 (Fallback)
TASK_MODEL_CONFIG = {
    
    # ── 채팅 파이프라인 (5단계) ──
    "chat_routing": {
        "models": ["gemini/gemini-2.5-flash-lite", "gpt-5.4-nano"],
        "temperature": 0.1,
        "max_tokens": 10,
        "description": "의도 분류 및 복잡도 판단 (Router)",
        "system_prompt": (
            "당신은 사용자 의도 분류기입니다. 반드시 CASUAL, QUESTION, SEARCH, ANALYSIS, GENERATION 중 하나만 출력하세요.\n"
            "\n"
            "[판단 기준 — 위에서부터 순서대로 적용]\n"
            "1. 인사·감사·리액션만 단독으로 있을 때 → CASUAL\n"
            "2. 인사 + 질문/요청이 결합된 경우 → 인사는 무시하고 아래 기준 적용\n"
            "3. 내부 문서·파일·자료를 찾거나 조회하는 요청 → SEARCH\n"
            "4. 데이터 분석·비교·평가·원인 파악·추세 판단 → ANALYSIS\n"
            "5. 문서·코드·이메일·보고서 등 새로운 콘텐츠 생성 → GENERATION\n"
            "6. 위에 해당하지 않는 질문·추천·확인·일상 요청 → QUESTION\n"
            "\n"
            "[복합 의도 처리]\n"
            "- 여러 의도가 섞인 경우, 사용자의 최종 목적 기준으로 분류\n"
            "- 예: '매출 자료 찾아서 분석해줘' → 최종 목적은 분석 → ANALYSIS\n"
            "- 예: '매출 분석해서 보고서 만들어줘' → 최종 목적은 보고서 생성 → GENERATION\n"
            "- 예: '지난달 회의록 찾아서 요약해줘' → 최종 목적은 찾기 → SEARCH\n"
            "\n"
            "[금지] 설명, 이유, 문장 출력 금지. 단어 하나만 출력."
        ),
    },
    "casual_chat": {
        "models": ["gemini/gemini-2.5-flash-lite", "gpt-5.4-nano"],
        "temperature": 0.9,
        "max_tokens": 200,
        "description": "잡담/인사 Fast-Track 응답",
        "system_prompt": (
            "당신은 기업 내부에서 사용되는 AI 어시스턴트입니다.\n"
            "\n"
            "[톤 & 스타일]\n"
            "- 한국어 존댓말 사용. 밝고 친근한 톤\n"
            "- 1~2문장 이내로 짧고 가볍게 응대\n"
            "- 이모지 사용 금지\n"
            "\n"
            "[행동 원칙]\n"
            "- 인사에는 인사로, 감사에는 감사로, 확인에는 확인으로 응대\n"
            "- 'ㅇㅇ', '넵', 'ㅋㅋ' 같은 짧은 입력에도 자연스럽게 반응\n"
            "- 구체적인 정보나 사실을 묻는 것처럼 보이면, '궁금한 점이 있으시면 편하게 질문해주세요!'처럼 안내하세요\n"
            "\n"
            "[금지]\n"
            "- 'AI로서', '제 능력 밖' 등 AI 자기 언급 표현\n"
            "- 불필요하게 긴 답변이나 설명\n"
            "- 질문을 분석하거나 의도를 파악하려는 시도\n"
            "- 마크다운 서식 사용 금지 (볼드, 리스트, 제목 등)\n"
            "- 모르는 내용을 추측하거나 꾸며내는 행위"
        ),
    },
    "chat_research": {
        "models": ["gpt-5.4-mini", "claude-haiku-4.5"],
        "temperature": 0.2,
        "max_tokens": 500,
        "description": "검색 쿼리 생성 및 검증 (Researcher)",
        "system_prompt": (
            "사용자 질문에서 핵심 검색 쿼리를 추출하세요.\n"
            "\n"
            "[규칙]\n"
            "1. 조사·어미·인사말·감탄사를 제거하고 핵심 명사·고유명사만 추출\n"
            "2. 동의어가 있으면 가장 공식적인 용어 사용 (예: 'AI' → '인공지능' X, 'AI' 유지)\n"
            "3. 날짜·기간 표현은 보존 (예: '지난달', '2026년 1분기')\n"
            "4. 지역 미지정 시 '서울' 추가 (날씨, 교통, 맛집 등 지역 관련 질문)\n"
            "5. 출력: 키워드를 공백으로 구분한 한 줄\n"
            "\n"
            "[금지] 문장형 출력 금지. 키워드만 출력."
        ),
    },
    "chat_simple": {
        "models": ["gemini/gemini-2.5-flash", "gpt-5.4-mini"],
        "temperature": 0.7,
        "max_tokens": 4000,
        "description": "단순 질의 답변 생성 (Reasoner - SIMPLE)",
        "system_prompt": (
            "당신은 기업 내부에서 사용되는 AI 어시스턴트입니다.\n"
            "\n"
            "[톤 & 스타일]\n"
            "- 한국어 존댓말 사용. 자연스럽고 친근하되 전문적인 톤\n"
            "- 핵심을 먼저 말하고, 필요시 부연 설명 추가 (결론 우선)\n"
            "- 1-3문단 이내로 간결하게. 불필요한 서론·맺음말 제거\n"
            "\n"
            "[행동 원칙]\n"
            "- 참고 문서가 제공되면 그 내용 기반으로 답변\n"
            "- 참고 문서가 없으면 자체 지식으로 답변하되, 확실하지 않은 내용은 '정확한 확인이 필요합니다'로 안내\n"
            "- 인사·감사에는 간결하게 응대 (과도한 인사말 금지)\n"
            "- 숫자·데이터 인용 시 원문 그대로 유지\n"
            "\n"
            "[금지]\n"
            "- 'AI로서', '제 능력 밖', '죄송합니다만' 등 AI 자기 언급 표현\n"
            "- 질문을 되묻는 것 (주어진 정보 내에서 최선의 답변 제공)\n"
            "- 마크다운 과다 사용 (볼드·리스트 최소한으로)\n"
            "- '제공된 정보에 따르면', '직접 접근할 수 없다' 같은 변명 표현\n"
            "- 웹 검색 결과가 제공되면 반드시 활용하여 최신 정보를 포함하세요\n"
            "\n"
            "[웹 검색 결과 활용 규칙]\n"
            "- 검색 결과에 포함된 구체적 수치, 날짜, 고유명사는 반드시 원문 그대로 포함하세요\n"
            "- 검색 결과가 표 형태로 정리 가능하면 마크다운 표로 제공하세요\n"
            "- \"약\", \"~경\", \"일반적으로\" 같은 모호한 표현 대신 검색된 정확한 정보를 사용하세요\n"
            "- 검색 결과의 출처가 명확하면 답변 말미에 출처를 간단히 표기하세요"
        ),
    },
    "chat_complex": {
        "models": ["claude-sonnet-4-6", "gpt-5.4"],
        "temperature": 0.1,
        "max_tokens": 4000,
        "description": "정밀 분석 답변 생성 (Reasoner - COMPLEX)",
        "system_prompt": (
            "당신은 기업 내부에서 사용되는 AI 어시스턴트입니다. 정밀한 분석과 논리적 답변을 제공합니다.\n"
            "\n"
            "[사고 방식]\n"
            "- 답변 전 문제를 분해하세요: 무엇을 묻는가 → 필요한 정보는 → 논리적 결론은\n"
            "- 데이터가 있으면 데이터 기반, 없으면 논리 기반으로 답변\n"
            "- 여러 관점이 존재하면 각각 제시한 뒤 가장 합리적인 결론 도출\n"
            "\n"
            "[답변 구조]\n"
            "- 마크다운으로 구조화: ## 제목, ### 소제목, **강조**, 표, 리스트 활용\n"
            "- 비교 요청 → 반드시 표(|항목|A|B|) 사용\n"
            "- 수치 인용 시 출처 문서 명시, 계산 시 과정 포함\n"
            "- 마지막에 핵심 요약 1-2문장 제공\n"
            "\n"
            "[충돌·불확실성 처리]\n"
            "- 문서 간 정보 충돌 시: 양쪽 모두 인용하고 차이점 명시\n"
            "- 데이터가 부족하면: 가용 정보로 분석 후, 추가로 필요한 데이터 명시\n"
            "- 확실하지 않은 추론은 '~로 추정됩니다' 등으로 표현\n"
            "\n"
            "[톤]\n"
            "- 한국어 존댓말, 전문적이고 객관적인 톤\n"
            "- 'AI로서' 등 자기 언급 금지\n"
            "- 참고 문서는 직접 열람한 것처럼 자연스럽게 인용. '제공된 정보에 따르면' 금지\n"
            "- 웹 검색 결과가 제공되면 반드시 활용하여 최신 정보를 포함하세요\n"
            "\n"
            "[웹 검색 결과 활용 규칙]\n"
            "- 검색 결과에 포함된 구체적 수치, 날짜, 고유명사는 반드시 원문 그대로 포함하세요\n"
            "- 검색 결과가 표 형태로 정리 가능하면 마크다운 표로 제공하세요\n"
            "- \"약\", \"~경\", \"일반적으로\" 같은 모호한 표현 대신 검색된 정확한 정보를 사용하세요\n"
            "- 검색 결과의 출처가 명확하면 답변 말미에 출처를 간단히 표기하세요"
        ),
    },
    "chat_bulk": {
        "models": ["gemini/gemini-3.1-flash-lite-preview", "gemini/gemini-2.5-flash"],
        "temperature": 0.1,
        "max_tokens": 4000,
        "description": "대량 문서 분석 답변 생성 (Reasoner - BULK)",
        "system_prompt": (
            "당신은 기업 내부에서 사용되는 AI 어시스턴트입니다. 여러 문서를 종합하여 통합된 인사이트를 제공합니다.\n"
            "\n"
            "[다중 문서 처리 원칙]\n"
            "- 질문 목적에 관련된 문서만 활용하고, 무관한 문서는 언급하지 마세요\n"
            "- 문서 간 정보 충돌 시: 각 문서의 입장을 병기하고, 작성일이 최신인 쪽을 우선 참고\n"
            "- 여러 문서의 정보를 결합할 때는 출처별로 구분하여 인용\n"
            "- 수치·데이터는 원문 그대로 인용 (임의 반올림·변환 금지)\n"
            "\n"
            "[답변 구조]\n"
            "- 마크다운으로 구조화: ## 제목, ### 소제목, 표, 리스트\n"
            "- 비교·시계열 데이터 → 반드시 표 활용\n"
            "- 문서 간 공통점과 차이점을 명확히 구분\n"
            "- 마지막에 종합 요약 및 시사점 제공\n"
            "\n"
            "[주의]\n"
            "- 문서에 없는 내용을 추론으로 채우지 마세요\n"
            "- 긴 문서를 전체 요약하지 말고 질문에 해당하는 부분만 추출·분석\n"
            "- 한국어 존댓말, 전문적 톤\n"
            "- 'AI로서' 등 자기 언급 금지\n"
            "- 참고 문서는 직접 열람한 것처럼 자연스럽게 인용. '제공된 정보에 따르면' 금지\n"
            "- 웹 검색 결과가 제공되면 반드시 활용하여 최신 정보를 포함하세요\n"
            "\n"
            "[웹 검색 결과 활용 규칙]\n"
            "- 검색 결과에 포함된 구체적 수치, 날짜, 고유명사는 반드시 원문 그대로 포함하세요\n"
            "- 검색 결과가 표 형태로 정리 가능하면 마크다운 표로 제공하세요\n"
            "- \"약\", \"~경\", \"일반적으로\" 같은 모호한 표현 대신 검색된 정확한 정보를 사용하세요\n"
            "- 검색 결과의 출처가 명확하면 답변 말미에 출처를 간단히 표기하세요"
        ),
    },
    "chat_synthesis": {
        "models": ["gemini/gemini-2.5-flash", "claude-haiku-4.5"],
        "temperature": 0.3,
        "max_tokens": 4000,
        "description": "답변 종합 및 포맷팅 (Synthesizer)",
        "system_prompt": (
            "당신은 마크다운 포맷팅 전문가입니다. 제공된 답변의 형식만 개선하세요.\n"
            "\n"
            "[절대 규칙 — 위반 시 치명적 오류]\n"
            "1. 원본의 내용·수치·사실관계·논조를 절대 변경·추가·삭제하지 마세요\n"
            "2. 새로운 정보·의견·해석을 만들어내지 마세요\n"
            "3. 원본의 코드 블록(```)은 내부 내용 포함 100% 보존\n"
            "4. 원본의 표(|...|)는 구조와 수치 포함 100% 보존\n"
            "5. 원본보다 길어지지 마세요\n"
            "\n"
            "[포맷팅 규칙]\n"
            "- 긴 답변(5문장 이상): 제목(##), 소제목(###), 리스트(- ), 강조(**볼드**) 적용\n"
            "- 짧은 답변(1-4문장): 구조화하지 않고 원본 그대로 반환\n"
            "- 비교 내용이 있으면 표로 정리\n"
            "- 나열 항목이 3개 이상이면 리스트로 정리\n"
            "- 이미 잘 포맷된 답변은 최소한의 조정만 수행\n"
            "\n"
            "[금지]\n"
            "- '요약', '결론', '참고' 등의 섹션을 임의 추가하지 마세요\n"
            "- 원본에 없는 이모지·장식 추가 금지\n"
            "- '다음은 포맷팅된 답변입니다' 같은 메타 설명 금지\n"
            "- 마크다운만 출력하세요"
        ),
    },
    "chat_guardrail": {
        "models": ["gemini/gemini-2.5-flash-lite", "gpt-5.4-nano"],
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
        "models": ["gpt-5.4", "claude-sonnet-4-6"],
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
        "models": ["gemini/gemini-3.1-pro-preview", "gpt-5.4-mini"],
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
        "models":    ["gemini/gemini-2.5-flash", "gpt-5.4-mini"],
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
        "models": ["gpt-5.4-mini", "claude-haiku-4.5"],
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
        "models": ["claude-opus-4-6", "gpt-5.4"],
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
        "models": ["gpt-5.4-mini", "gemini/gemini-2.5-flash-lite"],
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
    "GPT_5_4_PRO": {
        "model": "gpt-5.4-pro",
        "display_name": "GPT 5.4 Pro (Thinking)",
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
    CASUAL = "casual"            # 잡담, 단순 응답
    QUESTION = "question"        # 단순 질의 (기존 QUERY 통합)
    ANALYSIS = "analysis"        # 분석 요청
    GENERATION = "generation"    # 생성 요청
    SEARCH = "search"            # 검색 요청


# ==================== Step 1: Router ====================
class Router:
    """
    ML 모델 기반 의도 분류 및 복잡도 판단
    """
    
    def __init__(self, pipeline=None):
        self.pipeline = pipeline
        self._load_model()
        self.last_confidence = 0.0  # 방금 처리한 요청의 확신도 저장

    def _load_model(self):
        """pkl 파일에서 모델 로딩"""
        import joblib
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        tfidf_path = os.path.join(base_dir, "data", "tfidf_vectorizer.pkl")
        svm_path = os.path.join(base_dir, "data", "svm_classifier.pkl")
        
        try:
            self.tfidf = joblib.load(tfidf_path)
            self.svm = joblib.load(svm_path)
            print("  [Router] ML 분류 모델 로딩 성공 (TF-IDF, SVM)")
        except Exception as e:
            print(f"  [Router] ML 모델 로드 실패: {e}")
            self.tfidf = None
            self.svm = None

    def reload_model(self):
        """재학습 후 새 모델을 메모리에 즉시 반영"""
        print("  [Router] 모델 리로딩 시작...")
        self._load_model()
        print("  [Router] 모델 리로딩 완료 → 다음 요청부터 새 모델 적용")

    def classify_intent_with_llm(self, user_input: str) -> IntentType:
        """LLM을 사용한 의도 분류 폴백 (ML 확신도 부족 시)"""
        prompt = f'''다음 사용자 요청의 의도를 하나만 선택하세요: "{user_input}"
선택지:
- CASUAL: 인사, 짧은 잡담, 리액션
- QUESTION: 단순 질문이나 짧은 정보 요청
- SEARCH: 특정 파일, 문서, 과거 기록 겁색 조회
- ANALYSIS: 데이터 분석, 비교, 평가, 추이 판단
- GENERATION: 문서나 콘텐츠, 보고서, 코드 생성

답변은 (CASUAL, QUESTION, SEARCH, ANALYSIS, GENERATION) 중 하나만 출력하세요.'''
        try:
            llm_result = self.pipeline.call_llm(
                task="chat_routing", prompt=prompt, user_id=getattr(self, "current_user_id", None)
            )
            result = llm_result["content"].strip().upper()
            
            intent_map = {
                "CASUAL": IntentType.CASUAL,
                "QUESTION": IntentType.QUESTION,
                "SEARCH": IntentType.SEARCH,
                "ANALYSIS": IntentType.ANALYSIS,
                "GENERATION": IntentType.GENERATION
            }
            for k, v in intent_map.items():
                if k in result:
                    print(f"  [LLM 폴백 분류] {v.name}")
                    return v
                    
            return IntentType.QUESTION
        except Exception as e:
            print(f"  [LLM 폴백 오류] {e}, QUESTION으로 처리")
            return IntentType.QUESTION

    def classify_intent(self, user_input: str) -> IntentType:
        """ML 예측 후 신뢰도 < 0.6 이면 LLM 폴백"""
        if not self.tfidf or not self.svm:
            self.last_confidence = 0.5
            return self.classify_intent_with_llm(user_input)
            
        try:
            vec = self.tfidf.transform([user_input])
            probas = self.svm.predict_proba(vec)[0]
            max_idx = probas.argmax()
            confidence = probas[max_idx]
            self.last_confidence = confidence
            
            label_str = self.svm.classes_[max_idx].lower()
            try:
                intent = IntentType(label_str)
            except ValueError:
                intent = IntentType.QUESTION
                
            print(f"  [ML 분류] {intent.name} (확신도: {confidence:.2f})")
            
            if confidence >= 0.6:
                return intent
            else:
                print("  [ML 분류] 확신도 낮음, LLM 재분류 진행")
                return self.classify_intent_with_llm(user_input)
                
        except Exception as e:
            print(f"  [ML 모델 에러] {e}")
            self.last_confidence = 0.5
            return self.classify_intent_with_llm(user_input)

    def determine_complexity(self, user_input: str, intent: IntentType) -> ComplexityLevel:
        """의도 기반 단순 복잡도 매핑"""
        if intent in [IntentType.CASUAL]:
            return ComplexityLevel.SIMPLE
        elif intent in [IntentType.ANALYSIS, IntentType.GENERATION]:
            return ComplexityLevel.COMPLEX
        elif intent in [IntentType.QUESTION, IntentType.SEARCH]:
            # 복합 주제 감지: 접속사 패턴 또는 긴 문장
            compound_patterns = ["하고", "그리고", "랑", "이랑", "또", "함께", "같이", "겸"]
            has_compound = any(p in user_input for p in compound_patterns)
            is_long = len(user_input) > 80
            if has_compound or is_long:
                return ComplexityLevel.COMPLEX
            return ComplexityLevel.SIMPLE
        return ComplexityLevel.SIMPLE

    def needs_realtime_info(self, user_input: str) -> bool:
        """실시간/최신 정보 여부 예측 (유지)"""
        user_input_lower = user_input.lower()
        realtime_keywords = [
            "날씨", "기온", "온도", "비", "미세먼지", "환율", "주가", "시세", 
            "비트코인", "뉴스", "속보", "최근", "오늘", "지금", "스코어"
        ]
        for keyword in realtime_keywords:
            if keyword in user_input_lower: return True
        return False
    
    def route(self, user_input: str, user_id: str = None) -> dict:
        self.current_user_id = user_id
        try:
            intent = self.classify_intent(user_input)
            complexity = self.determine_complexity(user_input, intent)
            
            return {
                "intent": intent.value,
                "complexity": complexity.value,
                "routing_confidence": self.last_confidence,
                "user_input": user_input,
                "user_id": user_id,
                "needs_realtime": self.needs_realtime_info(user_input)
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
    
    def __init__(self, use_rag: bool = False, pipeline=None):
        """
        Args:
            use_rag: RAG 시스템 사용 여부 (개발 중에는 False, 배포 시 True)
            pipeline: 중앙 Pipeline 인스턴스 참조 (call_llm 접근용)
        """
        self.use_rag = use_rag
        self.pipeline = pipeline
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
        
        - Drive 참조 ON (use_rag=True): Drive 문서 검색 + 실시간 정보 필요 시 웹 검색 동시 실행
        - Drive 참조 OFF (use_rag=False): 실시간 정보 필요 시 웹 검색만 실행
        - 실시간 정보 필요 여부는 Router의 needs_realtime 플래그로 판단
        """
        user_input = routing_result["user_input"]
        
        documents = []
        web_context = ""
        web_citations = []
        full_docs = []
        
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
            
            # 의도 검출 결과에 따라 웹 검색 결정
            intent = routing_result.get("intent")
            needs_realtime = routing_result.get("needs_realtime", False)

            if intent == "casual":
                needs_web = False
            elif intent == "analysis":
                needs_web = True
            elif intent == "question":
                needs_web = True
            elif intent == "generation":
                needs_web = needs_realtime
            elif intent == "search":
                needs_web = needs_realtime
            else:
                needs_web = needs_realtime

            if needs_web:
                try:
                    web_context, web_citations = self._web_search(user_input)
                except Exception as e:
                    print(f"  ⚠️ 웹 검색 실패 (스킵): {e}")
            else:
                print(f"  → 웹 검색 스킵 (실시간 정보 불필요)")
                
            # ──── Drive 참조 OFF ────
            intent = routing_result.get("intent")
            needs_realtime = routing_result.get("needs_realtime", False)

            if intent == "casual":
                needs_web = False
            elif intent == "analysis":
                needs_web = True
            elif intent == "question":
                needs_web = True
            elif intent == "generation":
                needs_web = needs_realtime
            elif intent == "search":
                needs_web = needs_realtime
            else:
                needs_web = needs_realtime

            if needs_web:
                try:
                    web_context, web_citations = self._web_search(user_input)
                except Exception as e:
                    print(f"  ⚠️ 웹 검색 실패 (스킵): {e}")
            else:
                print(f"  → 웹 검색 스킵 (실시간 정보 불필요)")
            full_docs = []
        
        return {
            **routing_result,
            "retrieved_documents": documents,
            "full_docs": full_docs,
            "web_context": web_context,
            "web_citations": web_citations,
        }
    
    def _compress_query(self, user_input: str) -> str:
        """
        웹 검색 전 쿼리 압축 (긴 질문 → 핵심 키워드)
        짧은 질문은 그대로 반환하여 불필요한 LLM 호출 방지
        """
        # 짧은 입력(50자 이하)은 압축 불필요
        if len(user_input) <= 50:
            return user_input

        try:
            llm_result = self.pipeline.call_llm(
                task="chat_research",
                prompt=user_input,
                user_id=getattr(self, "current_user_id", None)
            )
            compressed = llm_result["content"].strip()

            # 안전장치: 압축 결과가 비어있거나 너무 짧으면 원본 사용
            if len(compressed) < 2:
                print(f"  → 쿼리 압축 실패 (결과 너무 짧음), 원본 사용")
                return user_input

            print(f"  → 쿼리 압축: '{user_input[:30]}...' → '{compressed}'")
            return compressed

        except Exception as e:
            print(f"  → 쿼리 압축 실패 ({e}), 원본 사용")
            return user_input

    def _web_search(self, query: str) -> tuple:
        """
        Perplexity API를 통한 실시간 웹 검색
        
        Returns:
            (content: str, citations: list[dict]) - 검색 결과 텍스트와 구조화된 출처 목록
            각 citation: {"url": str, "title": str}
        """
        try:
            # 쿼리 압축 (긴 질문 → 핵심 키워드)
            compressed_query = self._compress_query(query)
            print(f"  → 웹 검색 실행: {compressed_query[:50]}...")
            response = litellm.completion(
                model="perplexity/sonar",
                messages=[{"role": "user", "content": compressed_query}],
                max_tokens=2000,
            )
            result = response.choices[0].message.content or ""
            
            # 웹 검색 비용 로깅
            if self.pipeline and hasattr(response, 'usage') and response.usage:
                ws_input = getattr(response.usage, 'prompt_tokens', 0) or 0
                ws_output = getattr(response.usage, 'completion_tokens', 0) or 0
                ws_cost = self.pipeline.cost_calculator.calculate_cost("perplexity/sonar", ws_input, ws_output)
                self.pipeline.logger.log_model_usage("perplexity/sonar", ws_input, ws_output, ws_cost)
                self.pipeline.cost_logger.log_llm_cost(
                    task="web_search",
                    model_name="perplexity/sonar",
                    input_tokens=ws_input,
                    output_tokens=ws_output,
                    cost_usd=ws_cost.get("cost_usd", {}).get("total", 0),
                    cost_krw=ws_cost.get("cost_krw", {}).get("total", 0),
                    user_id=None
                )
            
            # ── Perplexity API citations 강력 추출 (여러 경로 시도) ──
            raw_citations = []
            
            # 방법 1: response 최상위 citations
            try:
                if hasattr(response, 'citations') and response.citations:
                    raw_citations = list(response.citations)
                    print(f"  → citations 추출 (최상위): {len(raw_citations)}개")
            except Exception as e1:
                print(f"  → citations 최상위 추출 실패: {e1}")
            
            # 방법 2: _hidden_params.original_response.citations
            if not raw_citations:
                try:
                    if hasattr(response, '_hidden_params'):
                        raw_resp = response._hidden_params.get('original_response', {})
                        if hasattr(raw_resp, 'citations') and raw_resp.citations:
                            raw_citations = list(raw_resp.citations)
                            print(f"  → citations 추출 (hidden_params): {len(raw_citations)}개")
                        elif isinstance(raw_resp, dict) and 'citations' in raw_resp:
                            raw_citations = list(raw_resp['citations'])
                            print(f"  → citations 추출 (hidden_params dict): {len(raw_citations)}개")
                except Exception as e2:
                    print(f"  → citations hidden_params 추출 실패: {e2}")
            
            # 방법 3: model_extra 또는 json 응답 직접 탐색
            if not raw_citations:
                try:
                    resp_dict = response.model_dump() if hasattr(response, 'model_dump') else {}
                    if 'citations' in resp_dict:
                        raw_citations = list(resp_dict['citations'])
                        print(f"  → citations 추출 (model_dump): {len(raw_citations)}개")
                except Exception as e3:
                    print(f"  → citations model_dump 추출 실패: {e3}")
            
            # 방법 4: 응답 텍스트에서 URL 정규식 추출 (최후의 수단)
            if not raw_citations and result:
                import re
                urls = re.findall(r'https?://[^\s\)\]\"\'<>]+', result)
                if urls:
                    raw_citations = list(dict.fromkeys(urls))  # 중복 제거
                    print(f"  → citations 추출 (정규식 fallback): {len(raw_citations)}개")
            
            # ── URL을 구조화된 citation 객체로 변환 ──
            structured_citations = []
            for url in raw_citations:
                if isinstance(url, str) and url.startswith('http'):
                    title = self._extract_title_from_url(url)
                    structured_citations.append({
                        "url": url,
                        "title": title
                    })
            
            print(f"  → 웹 검색 완료 ({len(result)}자, 출처 {len(structured_citations)}개)")
            return result, structured_citations
        except Exception as e:
            print(f"  → 웹 검색 실패 (Fallback: 웹 검색 없이 진행): {e}")
            return "", []
    
    def _extract_title_from_url(self, url: str) -> str:
        """URL 경로에서 읽기 가능한 제목을 추출"""
        try:
            from urllib.parse import urlparse, unquote
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            hostname = hostname.replace("www.", "")
            
            # URL 경로에서 의미 있는 부분 추출
            path = unquote(parsed.path).strip("/")
            if path:
                # 마지막 경로 세그먼트 사용
                last_segment = path.split("/")[-1]
                # 파일 확장자 제거
                if "." in last_segment:
                    last_segment = last_segment.rsplit(".", 1)[0]
                # 하이픈/언더스코어를 공백으로
                last_segment = last_segment.replace("-", " ").replace("_", " ")
                if len(last_segment) > 3:
                    return f"{hostname} - {last_segment}"
            
            return hostname
        except Exception:
            return url[:60]



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
        task = self.complexity_task_map.get(complexity, "chat_simple")
        
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
            web_context = (
                f"\n\n[웹 검색 결과 — 아래 정보를 반드시 활용하세요]\n"
                f"중요: 검색 결과에 있는 정확한 수치, 날짜, 이름, 전문 용어를 답변에 그대로 포함하세요. "
                f"임의로 요약하거나 반올림하지 마세요.\n\n"
                f"{context['web_context']}"
            )
        
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
        # 프롬프트 구성 (데이터만 user message에, 행동 지시는 system_prompt에)
        prompt = f"""현재 시간: {time_str}

[사용자 질문]
{user_input}
{web_context}
{rag_context}
{used_docs_instruction}"""
        
        
        # [Agent] 시스템 프롬프트 적용
        options = {}
        if context.get("system_prompt"):
            options["system_prompt"] = context.get("system_prompt")
            
        # call_llm이 Fallback + 토큰 추출 + 비용 로깅 전부 처리
        llm_result = self.pipeline.call_llm(
            task=task,
            prompt=prompt,
            options=options,
            user_id=context.get("user_id"),
            conversation_history=context.get("conversation_history")
        )
        
        return (
            llm_result["content"],
            llm_result["model_used"],
            llm_result["input_tokens"],
            llm_result["output_tokens"],
        )
    
    def generate_response(self, context: Dict[str, Any]) -> tuple:
        """답변 생성 (Fallback 포함)"""
        return self.generate_response_with_fallback(context)
    
    def verify(self, response: str) -> tuple:
        """
        Reasoner 출력의 경량 자가 검증 (LLM 호출 없음)
        Returns: (is_verified: bool, confidence: float)
        """
        issues = []
        confidence = 1.0
        response_lower = response.lower()

        # ── 1. 빈 응답 / 의미 없는 응답 ──
        stripped = response.strip()
        if len(stripped) < 10:
            issues.append("응답이 너무 짧음")
            confidence -= 0.5

        # ── 2. LLM 거부 패턴 감지 ──
        refusal_patterns = [
            "죄송합니다만, 해당 요청",
            "답변을 드리기 어렵",
            "도움을 드리기 어렵",
            "I cannot",
            "I'm sorry, but I",
            "As an AI",
        ]
        for pattern in refusal_patterns:
            if pattern.lower() in response_lower:
                issues.append(f"LLM 거부 패턴: '{pattern}'")
                confidence -= 0.3
                break

        # ── 3. 반복 텍스트 감지 (LLM 루프) ──
        # 같은 문장이 3번 이상 반복되면 생성 오류
        sentences = [s.strip() for s in response.split('.') if len(s.strip()) > 10]
        if len(sentences) > 3:
            from collections import Counter
            sentence_counts = Counter(sentences)
            most_common_count = sentence_counts.most_common(1)[0][1] if sentence_counts else 0
            if most_common_count >= 3:
                issues.append(f"반복 텍스트 감지 ({most_common_count}회 반복)")
                confidence -= 0.4

        # ── 4. 언어 불일치 감지 ──
        # 한국어 입력인데 영어로만 답변한 경우 (간단 휴리스틱)
        korean_chars = sum(1 for c in response if '\uac00' <= c <= '\ud7a3')
        total_alpha = sum(1 for c in response if c.isalpha())
        if total_alpha > 50 and korean_chars / max(total_alpha, 1) < 0.1:
            # 알파벳 50자 이상인데 한국어 비율 10% 미만
            issues.append("영어 위주 응답 (한국어 입력 예상)")
            confidence -= 0.2

        # ── 결과 ──
        # 이슈가 하나라도 있으면 is_verified = False
        is_verified = len(issues) == 0
        confidence = max(0.0, min(1.0, confidence))

        if issues:
            print(f"  [Reasoner.verify] 이슈 {len(issues)}건: {issues} (confidence={confidence:.2f})")

        return is_verified, confidence

    def reason(self, research_result: Dict[str, Any]) -> Dict[str, Any]:
        """추론 실행"""
        response, model_used, input_tokens, output_tokens = self.generate_response(research_result)
        is_verified, confidence = self.verify(response)

        # 검증 실패 시 (심각한 오류: confidence <= 0.5) 1회 재생성 시도
        if not is_verified and confidence <= 0.5:
            print(f"  [Reasoner] 검증 실패 및 신뢰도 낮음 (confidence={confidence:.2f}), 재생성 시도")
            response2, model_used2, input_tokens2, output_tokens2 = self.generate_response(research_result)
            is_verified, confidence = self.verify(response2)
            
            response = response2
            model_used = f"{model_used} -> {model_used2}"
            input_tokens += input_tokens2
            output_tokens += output_tokens2

        return {
            **research_result,
            "response": response,
            "model_used": model_used,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "verified": is_verified,
            "confidence": confidence
        }


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
        """응답 포맷팅 (call_llm 위임, 짧은 답변은 바이패스)"""
        
        response = reasoning_result["response"]

        # 짧은 답변(4문장 이하)은 Synthesizer를 스킵하여 비용/시간 절감
        sentence_count = len([s for s in response.split('.') if s.strip()])
        if sentence_count <= 4 and len(response) < 500:
            print(f"  [Synthesizer] 짧은 답변 ({sentence_count}문장, {len(response)}자) → 바이패스")
            # 기본 마크다운 정리만 수행 (LLM 호출 없이)
            if hasattr(self.pipeline, 'guardrail'):
                response = self.pipeline.guardrail.clean_markdown_formatting(response)
            return response
        
        prompt = f"""아래 원본 답변에 마크다운 서식만 적용하세요. 내용을 절대 변경하지 마세요.

원본 답변:
{response}

[서식 적용 기준]
- 5문장 이상이면: 제목(##), 소제목(###), 리스트, 볼드 적용
- 4문장 이하이면: 원본 그대로 반환 (서식 적용 금지)
- 코드 블록·표가 있으면: 100% 원본 보존
- 원본보다 길어지면 안 됩니다"""

        try:
            llm_result = self.pipeline.call_llm(
                task="chat_synthesis",
                prompt=prompt,
                user_id=reasoning_result.get("user_id")
            )
            content = llm_result["content"]
            if hasattr(self.pipeline, 'guardrail'):
                content = self.pipeline.guardrail.clean_markdown_formatting(content)
            return content
            
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
        self.pipeline = pipeline
        from services.ai_drive.core.pii_detector import PIIDetector
        self.pii_detector = PIIDetector()
    
    def _get_user_pii_settings(self, user_id: str) -> Dict[str, bool]:
        """DB에서 사용자 PII 감지 항목 설정 조회"""
        try:
            import uuid as _uuid
            from application.database import SessionLocal, UserSettings
            uid = _uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            db = SessionLocal()
            try:
                settings = db.query(UserSettings).filter(
                    UserSettings.user_id == uid
                ).first()
                if settings and hasattr(settings, 'detection_items') and settings.detection_items:
                    return settings.detection_items
            finally:
                db.close()
        except Exception as e:
            print(f"  ⚠️ PII 설정 조회 실패: {e}")
        return {"ssn": True, "phone": True, "email": True, "creditCard": True, "account": True, "address": True}

    def mask_sensitive_info(self, text: str, user_id: str = None) -> str:
        """민감 정보 부분 마스킹 (6가지 PII 유형, 사용자 설정 반영)"""
        enabled_items = self._get_user_pii_settings(user_id) if user_id else None
        return self.pii_detector.partial_mask(text, enabled_items)
    
    def clean_markdown_formatting(self, text: str) -> str:
        """LLM이 전체 텍스트를 마크다운 코드 블록으로 감싸서 반환하는 경우 방어"""
        import re
        text = text.strip()
        # ```markdown 또는 ```md 또는 ``` 로 시작해서 ``` 로 끝나는 경우
        pattern = r'^```(?:markdown|md)?\s*\n([\s\S]*?)\n```$'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text
    
    def check_safety(self, text: str) -> bool:
        """안전성 검사"""
        # TODO: 유해 콘텐츠 검사 로직 구현
        return True
    
    def verify_quality(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """품질 검수 (복잡도에 따라 차등 적용)"""
        # Reasoner가 이슈를 발견한 경우 → SIMPLE이라도 스킵하지 않고 검증 수행
        reasoner_verified = synthesis_result.get("verified", True)
        if not reasoner_verified:
            print(f"  → [Reasoner 검증 실패] 강제 경량 검수 진행")
            return self._verify_fallback(synthesis_result)
            
        complexity = synthesis_result.get("complexity")
        
        # SIMPLE 작업 처리
        if complexity == ComplexityLevel.SIMPLE.value:
            routing_confidence = synthesis_result.get("routing_confidence", 0.0)
            
            if routing_confidence >= 0.7:
                # Router가 SIMPLE이라고 확신 → 신뢰하고 스킵
                print(f"  → [SIMPLE] Router 신뢰도 높음 ({routing_confidence:.2f}), 검수 스킵")
                return {
                    "quality_verified": True,
                    "quality_score": 1.0,
                    "quality_issues": [],
                    "needs_regeneration": False
                }
            else:
                # Router 신뢰도 낮음 → COMPLEX 오분류 가능성 → 경량 검수 적용
                print(f"  → [SIMPLE 경량 검수] Router 신뢰도 낮음 ({routing_confidence:.2f}), 오분류 가능성 있음")
                result = self._verify_fallback(synthesis_result)
                print(f"  ✓ 경량 검수 완료 (점수: {result['quality_score']:.2f})")
                return result
        
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
            
        # 4. 사실 주장 감지 (숫자+단위가 포함된 답변은 할루시네이션 위험)
        fact_patterns = [
            r'\d+[\.\,]?\d*\s*[%조억만원달러]',  # "2.3%", "432조원"
            r'\d{4}년',                          # "2025년"
        ]
        has_factual_claim = any(re.search(p, response) for p in fact_patterns)
        
        # 사실 주장이 있는데 참고 문서나 웹 검색 결과가 없으면 위험
        has_source = bool(synthesis_result.get("web_context")) or bool(synthesis_result.get("retrieved_documents"))
        if has_factual_claim and not has_source:
            quality_issues.append("검증되지 않은 수치/사실 포함 가능성 (참고 출처 없음)")
            

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

        # 1. 민감 정보 마스킹 먼저 (외부 LLM 전송 전에)
        user_id = synthesis_result.get("user_id")
        safe_response = self.mask_sensitive_info(formatted_response, user_id=user_id)
        synthesis_result["formatted_response"] = safe_response

        # 2. 품질 검수 (마스킹된 텍스트로 검수)
        quality_result = self.verify_quality(synthesis_result)

        # 3. 안전성 검사
        is_safe = self.check_safety(safe_response)

        # 재생성 필요 시 경고 메시지 추가
        if quality_result["needs_regeneration"]:
            print(f"  [!] 품질 경고: {quality_result['quality_issues']}")
            safe_response = f"※ 이 답변은 정확도가 낮을 수 있습니다. 중요한 수치는 원본 자료를 확인해주세요.\n\n{safe_response}"

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
        self.researcher = Researcher(use_rag=use_rag, pipeline=self)  # RAG 플래그, 파이프라인 전달
        self.reasoner = Reasoner(pipeline=self)
        self.synthesizer = Synthesizer(pipeline=self)
        self.guardrail = Guardrail(pipeline=self)
        self.logger = get_logger()
        self.cost_calculator = get_cost_calculator()
        self.cost_logger = get_cost_logger()

    def call_llm(self, task: str, prompt: str, options: dict = None, user_id: Optional[str] = None, conversation_history: list = None) -> dict:
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
            
        # 대화 히스토리 삽입 (시스템 프롬프트 뒤, 현재 질문 앞)
        if conversation_history:
            messages.extend(conversation_history)
            
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
                    REASONING_TASKS = {"chat_routing", "chat_guardrail", "chat_complex"}
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

다음 JSON 구조에 맞추어 응답해주세요 (다른 일반 텍스트나 설명 없이 순수 JSON만 만드세요):
{{
    "name": "에이전트 이름 (간결하게, 20자 이내)",
    "description": "에이전트 설명 (50자 이내)",
    "category": "카테고리 (마케팅/개발/기획/영업/인사/재무/기타 중 하나)",
    "input_example": "사용자가 이 에이전트에게 할 법한 구체적인 질문 예시 (예: '광운대 2025년 1학기 학사일정 알려줘')",
    "output_example": "입력 예시에 대한 에이전트의 완성된 답변 형태 예시 (단순 설명/요약이 아닌, 실제 AI가 답변하는 것처럼 작성된 모의 답변. 마크다운이나 표/JSON 포맷 등 실제 응답 형태 그대로 작성)",
    "system_prompt": "이 에이전트의 역할, 행동 규칙, 출력 형식을 정의하는 명확하고 구체적인 시스템 프롬프트 (예: '당신은 대학 학사일정 안내 에이전트입니다. 사용자가 학사 일정을 물어보면 표로 정리해 제공합니다.')",
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

    def process(self, user_input: str, user_id: Optional[str] = None, system_prompt: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        pipeline_start = time.time()
        print(f"\n{'='*60}")
        print(f"[Pipeline] 처리 시작: {user_input[:50]}...")
        print(f"{'='*60}")
        
        # 대화 히스토리 조회
        conversation_history = []
        if session_id:
            from services.orchestrator.db.tables import ChatLog
            from application.database import SessionLocal
            db = SessionLocal()
            try:
                recent_logs = db.query(ChatLog).filter(
                    ChatLog.session_id == session_id
                ).order_by(ChatLog.created_at.desc()).limit(5).all()

                for log in reversed(recent_logs):
                    conversation_history.append({"role": "user", "content": log.user_input})
                    conversation_history.append({"role": "assistant", "content": log.ai_response})
            finally:
                db.close()
        
        # 세션 시작
        session_id = self.logger.start_session(user_input, user_id)
        
        try:
            # Step 1: Router
            print(f"\n[Step 1/5] Router - 의도 분류 및 복잡도 판단")
            step_start = time.time()
            routing_result = self.router.route(user_input, user_id=user_id)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Router", routing_result, step_duration)
            print(f"  ✓ Router 완료: {step_duration:.0f}ms | intent={routing_result.get('intent')} complexity={routing_result.get('complexity')} confidence={routing_result.get('routing_confidence', 0):.2f}")
            
            # --- [FAST TRACK] CASUAL 의도인 경우 파이프라인 우회 ---
            if routing_result.get("intent") == IntentType.CASUAL.value:
                print(f"\n[Fast-Track] CASUAL 의도 감지 - 나머지 파이프라인 우회")
                step_start = time.time()
                
                llm_res = self.call_llm(
                    task="casual_chat", 
                    prompt=user_input, 
                    user_id=user_id,
                    conversation_history=conversation_history
                )
                
                casual_response = llm_res["content"].strip()
                step_duration = (time.time() - step_start) * 1000
                print(f"  ✓ Fast-Track 답변 생성 완료: {step_duration:.0f}ms")
                
                final_result = {
                    "response": casual_response,
                    "session_id": session_id,
                    "used_model": "gemini-2.5-flash-lite",
                    "sources": [],
                    "web_searched": False,
                    "web_citations": [],
                    "metadata": {
                        "intent": routing_result.get("intent"),
                        "complexity": routing_result.get("complexity"),
                        "confidence": routing_result.get("routing_confidence", 1.0)
                    },
                    "is_safe": True,
                    "quality_verified": True,
                    "routing_result": routing_result
                }
                pipeline_duration = (time.time() - pipeline_start) * 1000
                self.logger.end_session(final_result=final_result, success=True)
                print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] 파이프라인 Fast-Track 종료 (소요시간: {pipeline_duration:.0f}ms)")
                print(f"{'='*60}\n")
                return final_result
            # -----------------------------------------------------

            # Step 2: Researcher
            print(f"\n[Step 2/5] Researcher - RAG 기반 문서 검색")
            step_start = time.time()
            research_result = self.researcher.retrieve(routing_result)
            
            # [Injection] 에이전트 시스템 프롬프트 전파 (Router -> Researcher -> Reasoner)
            if system_prompt:
                research_result["system_prompt"] = system_prompt
                
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Researcher", {
                "documents_found": len(research_result.get("retrieved_documents", []))
            }, step_duration)
            print(f"  ✓ Researcher 완료: {step_duration:.0f}ms | 문서={len(research_result.get('retrieved_documents', []))}개 웹검색={'O' if research_result.get('web_context') else 'X'}")
            
            # Step 3: Reasoner
            print(f"\n[Step 3/5] Reasoner - 논리적 답변 생성 및 검증")
            step_start = time.time()
            
            research_result["conversation_history"] = conversation_history
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
            print(f"  ✓ Reasoner 완료: {step_duration:.0f}ms | model={reasoning_result.get('model_used')} verified={reasoning_result.get('verified')}")
            
            # Step 4: Synthesizer
            print(f"\n[Step 4/5] Synthesizer - 최종 응답 포맷팅")
            step_start = time.time()
            synthesis_result = self.synthesizer.synthesize(reasoning_result)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Synthesizer", {}, step_duration)
            print(f"  ✓ Synthesizer 완료: {step_duration:.0f}ms")
            
            # Step 5: Guardrail
            print(f"\n[Step 5/5] Guardrail - 안전성 및 품질 검증")
            step_start = time.time()
            final_result = self.guardrail.guard(synthesis_result)
            step_duration = (time.time() - step_start) * 1000
            self.logger.log_step("Guardrail", {
                "is_safe": final_result.get("is_safe"),
                "quality_score": final_result.get("quality_score")
            }, step_duration)
            print(f"  ✓ Guardrail 완료: {step_duration:.0f}ms | safe={final_result.get('is_safe')} quality={final_result.get('quality_score')}")
            
            # 비용은 call_llm()에서 자동 로깅됨 (이중 로깅 방지)
            # process() 결과용으로 Reasoner 정보만 추출
            model_used = reasoning_result.get("model_used", "unknown")
            input_tokens = reasoning_result.get("input_tokens", 0)
            output_tokens = reasoning_result.get("output_tokens", 0)
            
            # 세션 종료 (final_result 전달)
            self.logger.end_session(final_result=final_result, success=True)
            
            total_duration = (time.time() - pipeline_start) * 1000
            print(f"\n{'='*60}")
            print(f"[Pipeline] 처리 완료! 총 소요시간: {total_duration:.0f}ms ({total_duration/1000:.1f}s)")
            print(f"{'='*60}\n")   

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

    def process_premium(self, user_input: str, model_type: str, use_rag: bool = False, user_id: Optional[str] = None, system_prompt: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        '''
        프리미엄 모델 직접 호출 (5단계 파이프라인 bypass)
        
        5단계 파이프라인 로직을 메가 프롬프트로 통합하여
        선택된 프리미엄 모델 하나로 처리합니다.
        
        Args:
            user_input: 사용자 입력
            model_type: 프리미엄 모델 키 (GPT_5_4_PRO, GEMINI_3_PRO, PERPLEXITY, OPUS_4_6)
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
        
        # 대화 히스토리 조회
        conversation_history = []
        if session_id:
            from services.orchestrator.db.tables import ChatLog
            from application.database import SessionLocal
            db = SessionLocal()
            try:
                recent_logs = db.query(ChatLog).filter(
                    ChatLog.session_id == session_id
                ).order_by(ChatLog.created_at.desc()).limit(5).all()

                for log in reversed(recent_logs):
                    conversation_history.append({"role": "user", "content": log.user_input})
                    conversation_history.append({"role": "assistant", "content": log.ai_response})
            finally:
                db.close()
        
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
                    web_context, web_citations = self.researcher._web_search(user_input)
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

            messages = [{"role": "system", "content": final_system_prompt}]
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({"role": "user", "content": user_prompt})
            
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
            
            # 7. 민감정보 마스킹 및 마크다운 포맷팅 방어
            safe_response = self.guardrail.mask_sensitive_info(content, user_id=user_id)
            safe_response = self.guardrail.clean_markdown_formatting(safe_response)
            
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

