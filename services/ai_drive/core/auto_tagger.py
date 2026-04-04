"""
AI 드라이브 - AI 자동 태깅
Gemini Flash로 태그/키워드/문서유형 자동 생성
"""

import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class AutoTagger:
    """
    문서 자동 태깅
    
    - 태그: 주제 분류 (3~5개)
    - 키워드: 핵심 단어 (3~5개)
    - 문서 유형: 보고서/제안서/회의록/계약서/기타
    """
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator  # 중앙 LLM 호출용

        # orchestrator가 있으면 중앙 관제 모드, 없으면 기존 방식
        if self.orchestrator:
            self.use_mock = False
        else:
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                self.use_mock = True
            else:
                self.use_mock = False
                self._init_client()

        # 비용 로깅을 위한 PostgresClient
        try:
            from db.postgres_client import PostgresClient
            self.postgres_client = PostgresClient()
        except Exception as e:
            self.postgres_client = None
    
    def _init_client(self):
        """Gemini 클라이언트 초기화"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            self.use_mock = True
    
    def generate_tags(self, text: str, title: str = "") -> Dict[str, any]:
        """
        문서에서 태그/키워드/유형 자동 생성
        
        Args:
            text: 문서 텍스트 (청킹 전 원본)
            title: 문서 제목 (있으면 참고)
            
        Returns:
            {
                "tags": ["마케팅", "전략", "2024"],
                "keywords": ["타겟고객", "ROI", "예산"],
                "doc_type": "보고서"
            }
        """
        if self.use_mock:
            return self._mock_generate(text, title)
        
        return self._real_generate(text, title)
    
    def generate_title_and_description(self, text: str) -> Dict[str, str]:
        """
        채팅/에이전트 결과에서 제목과 설명 자동 생성
        
        Args:
            text: 채팅 또는 에이전트 출력 내용
        
        Returns:
            {
                "title": "자동 생성된 제목",
                "description": "자동 생성된 설명"
            }
        """
        if self.use_mock:
            return self._mock_generate_title(text)
        
        return self._real_generate_title(text)
    
    def _real_generate_title(self, text: str) -> Dict[str, str]:
        """실제 Gemini API로 제목/설명 생성"""
    
        # 텍스트가 너무 길면 앞부분만 사용
        max_chars = 2000
        if len(text) > max_chars:
            text = text[:max_chars]
    
        prompt = f"""다음 내용을 보고 적절한 제목과 설명을 생성해주세요.

    내용:
    {text}

    다음 JSON 형식으로만 응답해주세요 (다른 텍스트 없이):
    {{
        "title" : "내용을 잘 나타내는 간결한 제목 (20자 이내)",
        "description" : "내용 요약 (50자 이내)"
    }}
    """
    
        try:
            llm_result = self.orchestrator.call_llm(
                task="title_gen",
                prompt=prompt,
            )
            result_text = llm_result["content"].strip()

            # ```json ``` 제거
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
        
            result = json.loads(result_text.strip())

            return {
                "title": result.get("title", "제목 없음")[:50],
                "description": result.get("description", "")[:200]
            }

        except Exception as e:
            return self._mock_generate_title(text)
    
    def _mock_generate_title(self, text: str) -> Dict[str, str]:
        """Mock 제목/설명 생성"""
        
        text_lower = text.lower()
        
        # 문서 유형 판별
        doc_type = ""
        if "회의" in text_lower or "미팅" in text_lower:
            doc_type = "[회의록]"
        elif "보고" in text_lower or "결과" in text_lower:
            doc_type = "[보고서]"
        elif "제안" in text_lower or "기획" in text_lower:
            doc_type = "[제안서]"
        elif "정리" in text_lower or "요약" in text_lower:
            doc_type = "[요약]"
        elif "질문" in text_lower or "답변" in text_lower:
            doc_type = "[Q&A]"
        
        # 핵심 키워드 추출
        keywords = []
        keyword_rules = {
            "마케팅": ["마케팅", "광고", "홍보", "캠페인"],
            "개발": ["개발", "코드", "api", "서버", "프로그램"],
            "전략": ["전략", "계획", "목표", "방향"],
            "매출": ["매출", "수익", "성장", "실적"],
            "고객": ["고객", "사용자", "타겟"],
            "AI": ["ai", "인공지능", "머신러닝"],
            "예산": ["예산", "비용", "투자"],
            "신제품": ["신제품", "출시", "런칭", "제품"]
        }
        
        for keyword, patterns in keyword_rules.items():
            for pattern in patterns:
                if pattern in text_lower:
                    if keyword not in keywords:
                        keywords.append(keyword)
                    break
            if len(keywords) >= 2:
                break
        
        # 제목 생성
        if doc_type or keywords:
            title = f"{doc_type} {' '.join(keywords)} 관련".strip()
        else:
            # 키워드 없으면 첫 문장에서 추출
            first_sentence = text.split('.')[0].strip()
            if len(first_sentence) > 20:
                title = first_sentence[:17] + "..."
            else:
                title = first_sentence
        
        # 설명 생성
        if len(text) > 50:
            description = text[:47].replace('\n', ' ') + "..."
        else:
            description = text.replace('\n', ' ')
        
        # 빈 제목 방지
        if not title or title.strip() == "관련":
            title = "새 문서"

        return {
            "title": title,
            "description": description
        }

    def _real_generate(self, text: str, title: str) -> Dict[str, any]:
        """실제 Gemini API 호출"""
        
        # 텍스트가 너무 길면 앞부분만 사용 (비용 절감)
        max_chars = 3000
        if len(text) > max_chars:
            text = text[:max_chars]
        
        prompt = f"""다음 문서를 분석하여 태그, 키워드, 문서유형을 추출해주세요.

문서 제목: {title if title else "없음"}

문서 내용:
{text}

다음 JSON 형식으로만 응답해주세요 (다른 텍스트 없이):
{{
    "tags": ["태그1", "태그2", "태그3"],
    "keywords": ["키워드1", "키워드2", "키워드3"],
    "doc_type": "문서유형"
}}

규칙:
- tags: 문서의 주제/분야를 나타내는 3~5개 태그
- keywords: 문서의 핵심 단어 3~5개
- doc_type: 다음 중 하나만 선택 [보고서, 제안서, 회의록, 계약서, 매뉴얼, 기획서, 기타]
"""
        
        try:
            llm_result = self.orchestrator.call_llm(
                task="tagging",
                prompt=prompt,
            )
            result_text = llm_result["content"].strip()
            
            # ```json ``` 제거
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text.strip())
            
            # 검증
            result = self._validate_result(result)

            return result

        except json.JSONDecodeError as e:
            return self._mock_generate(text, title)
        except Exception as e:
            return self._mock_generate(text, title)
    
    def _mock_generate(self, text: str, title: str) -> Dict[str, any]:
        """Mock 태깅 (API 없을 때)"""
        
        # 간단한 키워드 추출 (텍스트 기반)
        tags = []
        keywords = []
        doc_type = "기타"
        
        text_lower = text.lower()
        title_lower = title.lower() if title else ""
        combined = text_lower + " " + title_lower
        
        # 태그 추출 (간단한 규칙 기반)
        tag_rules = {
            "마케팅": ["마케팅", "광고", "프로모션", "캠페인"],
            "개발": ["개발", "코드", "프로그램", "api", "서버"],
            "기획": ["기획", "전략", "계획", "목표"],
            "영업": ["영업", "매출", "거래", "계약"],
            "인사": ["인사", "채용", "교육", "직원"],
            "재무": ["재무", "예산", "비용", "수익"],
            "AI": ["ai", "인공지능", "머신러닝", "딥러닝"]
        }
        
        for tag, keywords_list in tag_rules.items():
            for kw in keywords_list:
                if kw in combined:
                    if tag not in tags:
                        tags.append(tag)
                    break
        
        # 문서 유형 추출
        type_rules = {
            "보고서": ["보고서", "리포트", "report", "결과"],
            "제안서": ["제안서", "제안", "proposal"],
            "회의록": ["회의록", "회의", "미팅"],
            "계약서": ["계약서", "계약", "contract"],
            "매뉴얼": ["매뉴얼", "가이드", "manual", "guide"],
            "기획서": ["기획서", "기획안", "plan"]
        }
        
        for dtype, keywords_list in type_rules.items():
            for kw in keywords_list:
                if kw in combined:
                    doc_type = dtype
                    break
        
        # 기본값
        if not tags:
            tags = ["일반"]
        
        # 키워드는 제목에서 추출
        if title:
            keywords = [w for w in title.split() if len(w) > 1][:3]
        if not keywords:
            keywords = ["문서"]
        
        result = {
            "tags": tags[:5],
            "keywords": keywords[:5],
            "doc_type": doc_type
        }

        return result
    
    def _validate_result(self, result: Dict) -> Dict:
        """결과 검증 및 정규화"""
        
        # tags 검증
        if "tags" not in result or not isinstance(result["tags"], list):
            result["tags"] = ["일반"]
        result["tags"] = result["tags"][:5]  # 최대 5개
        
        # keywords 검증
        if "keywords" not in result or not isinstance(result["keywords"], list):
            result["keywords"] = []
        result["keywords"] = result["keywords"][:5]  # 최대 5개
        
        # doc_type 검증
        valid_types = ["보고서", "제안서", "회의록", "계약서", "매뉴얼", "기획서", "기타"]
        if "doc_type" not in result or result["doc_type"] not in valid_types:
            result["doc_type"] = "기타"
        
        return result