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
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            print("⚠️ GOOGLE_API_KEY 없음 - Mock 모드로 실행")
            self.use_mock = True
        else:
            self.use_mock = False
            self._init_client()
    
    def _init_client(self):
        """Gemini 클라이언트 초기화"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            print("✓ Gemini Flash 연결 성공")
        except Exception as e:
            print(f"⚠️ Gemini 연결 실패: {e}")
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
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 200
                }
            )
            
            # JSON 파싱
            result_text = response.text.strip()
            
            # ```json ``` 제거
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text.strip())
            
            # 검증
            result = self._validate_result(result)
            
            print(f"✓ AI 태깅 완료: {result['tags']}")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 파싱 실패: {e}")
            return self._mock_generate(text, title)
        except Exception as e:
            print(f"⚠️ Gemini 호출 실패: {e}")
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
        
        print(f"✓ Mock 태깅 완료: {result['tags']}")
        
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


# ==================== 테스트 코드 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("AI 자동 태깅 테스트")
    print("=" * 60)
    
    tagger = AutoTagger()
    
    # 테스트 1: 마케팅 문서
    print("\n[테스트 1] 마케팅 문서")
    result1 = tagger.generate_tags(
        text="2024년 마케팅 전략 보고서입니다. 타겟 고객은 20-30대이며, 인스타그램과 유튜브를 활용한 캠페인을 진행합니다. 예상 ROI는 150%입니다.",
        title="2024 마케팅 전략 보고서"
    )
    print(f"  결과: {result1}")
    
    # 테스트 2: 개발 문서
    print("\n[테스트 2] 개발 문서")
    result2 = tagger.generate_tags(
        text="API 서버 개발 가이드입니다. FastAPI를 사용하여 REST API를 구현합니다. 인증은 JWT를 사용합니다.",
        title="API 개발 매뉴얼"
    )
    print(f"  결과: {result2}")
    
    # 테스트 3: AI 문서
    print("\n[테스트 3] AI 문서")
    result3 = tagger.generate_tags(
        text="AI 드라이브는 문서를 자동으로 분석하고 검색할 수 있게 해주는 시스템입니다. RAG 기반으로 동작합니다.",
        title="AI 드라이브 기획서"
    )
    print(f"  결과: {result3}")
    
    print("\n" + "=" * 60)
    print("✓ 테스트 완료!")
    print("=" * 60)