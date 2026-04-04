"""
AI 드라이브 - 개인정보 감지 모듈
업로드 시 개인정보 자동 감지 및 차단
"""

import re
from typing import List, Dict, Any


class PIIDetector:
    """
    개인정보(PII) 감지기
    - 주민등록번호
    - 전화번호
    - 이메일
    - 계좌번호
    - 신용카드번호
    """
    
    def __init__(self):
        # 정규식 패턴 정의 (구체적 → 범용 순서로 정의)
        # 감지 순서가 중요: 먼저 감지된 부분은 이후 패턴에서 제외
        self.detection_order = [
            "주민등록번호",
            "신용카드번호",
            "전화번호",
            "이메일",
            "계좌번호",
            "주소",
        ]
        
        self.patterns = {
            # 하이픈/공백/없음, 국제번호(+82) 모두 처리
            "주민등록번호": r'\b\d{6}[-\s]?\d{7}\b',
            "전화번호": r'(\+82[-\s]?)?0?1[016789][-\s]?\d{3,4}[-\s]?\d{4}|01[016789]\d{7,8}',
            "이메일": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            # 하이픈 또는 공백 구분자 모두 처리
            "계좌번호": r'\b\d{3,6}[-\s]\d{2,6}[-\s]\d{4,6}\b',
            "신용카드번호": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "주소": r'(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)(특별시|광역시|특별자치시|특별자치도|도)?\s?[\w]+[시군구읍면](?:\s?[\w]+[구군동읍면리])*',
        }
        
        
        # 프론트엔드 키 → 감지 타입 매핑
        self.key_to_type = {
            "ssn": "주민등록번호",
            "phone": "전화번호",
            "email": "이메일",
            "creditCard": "신용카드번호",
            "account": "계좌번호",
            "address": "주소",
        }
    
    def detect(self, text: str, enabled_items: Dict[str, bool] = None) -> Dict[str, Any]:
        """
        텍스트에서 개인정보 감지 (순서 기반, 중복 제거)
        
        Args:
            text: 검사할 텍스트
            enabled_items: 감지할 항목 (예: {"ssn": True, "phone": False, ...})
                          None이면 모든 항목 검사
            
        Returns:
            {
                "has_pii": True/False,
                "findings": [
                    {"type": "주민등록번호", "count": 2},
                    {"type": "전화번호", "count": 1},
                    ...
                ],
                "total_count": 3
            }
        """
        findings = []
        total_count = 0
        
        # enabled_items로 활성 타입 필터링
        if enabled_items:
            active_types = [
                self.key_to_type[key]
                for key, enabled in enabled_items.items()
                if enabled and key in self.key_to_type
            ]
        else:
            active_types = list(self.detection_order)
        
        # 순서대로 감지하고, 매칭된 부분을 제거하여 중복 방지
        remaining_text = text
        for pii_type in self.detection_order:
            if pii_type not in active_types or pii_type not in self.patterns:
                continue
                
            pattern = self.patterns[pii_type]
            matches = re.findall(pattern, remaining_text)
            
            if matches:
                # 주민등록번호는 추가 검증
                if pii_type == "주민등록번호":
                    matches = self._validate_rrn(matches)
                
                if matches:
                    count = len(matches)
                    findings.append({
                        "type": pii_type,
                        "count": count
                    })
                    total_count += count
                    
                    # 매칭된 부분을 제거하여 다음 패턴에서 중복 감지 방지
                    remaining_text = re.sub(pattern, '___', remaining_text)
        
        return {
            "has_pii": total_count > 0,
            "findings": findings,
            "total_count": total_count
        }
    
    def _validate_rrn(self, matches: List[str]) -> List[str]:
        """
        주민등록번호 유효성 검증
        - 앞 6자리가 유효한 생년월일인지 확인
        """
        valid = []
        
        for match in matches:
            # 숫자만 추출
            digits = re.sub(r'[-\s]', '', match)
            
            if len(digits) != 13:
                continue
            
            # 앞 6자리 (생년월일)
            year = int(digits[0:2])
            month = int(digits[2:4])
            day = int(digits[4:6])
            
            # 월, 일 유효성 체크
            if 1 <= month <= 12 and 1 <= day <= 31:
                valid.append(match)
        
        return valid
    
    def contains_critical_pii(self, text: str) -> bool:
        """
        치명적 개인정보(주민번호) 포함 여부
        → 무조건 차단 대상
        
        Args:
            text: 검사할 텍스트
            
        Returns:
            주민등록번호 포함 시 True
        """
        pattern = self.patterns["주민등록번호"]
        matches = re.findall(pattern, text)
        valid_matches = self._validate_rrn(matches)
        return len(valid_matches) > 0


    def partial_mask(self, text: str, enabled_items: Dict[str, bool] = None) -> str:
        """
        부분 마스킹: 일부 자리만 *로 치환 (채팅 답변용)
        예) 010-1234-5678  → 010-****-5678
            user@company.com → use***@company.com
            901215-1234567   → 901215-*******
            1234-5678-9012-3456 → 1234-****-****-3456
        """
        if enabled_items:
            active_types = [
                self.key_to_type[key]
                for key, enabled in enabled_items.items()
                if enabled and key in self.key_to_type
            ]
        else:
            active_types = list(self.detection_order)

        masked_text = text

        if "전화번호" in active_types:
            # 구분자(하이픈/공백) 있는 형태 + 국제번호 포함
            # +82-10-1234-5678 / +82-010-1234-5678 / 010-1234-5678 모두 처리
            masked_text = re.sub(
                r'(\+82[-\s]?0?1[016789]|01[016789])([-\s])(\d{3,4})([-\s]\d{4})',
                lambda m: m.group(1) + m.group(2) + '*' * len(m.group(3)) + m.group(4),
                masked_text
            )
            # 구분자 없는 연속 형태: 01012345678, 번호는01012345678입니다 → 010****5678
            # \b 대신 lookaround 사용 (한글 옆에서도 작동)
            masked_text = re.sub(
                r'(?<!\d)(01[016789])(\d{3,4})(\d{4})(?!\d)',
                lambda m: m.group(1) + '*' * len(m.group(2)) + m.group(3),
                masked_text
            )
            
            # 혼합 구분자: 010-12345678, 0101234 5678 등
            masked_text = re.sub(
                r'(?<!\d)(01[016789])([-\s])(\d{3,4})(\d{4})(?!\d)',
                lambda m: m.group(1) + m.group(2) + '*' * len(m.group(3)) + m.group(4),
                masked_text
            )

        if "주민등록번호" in active_types:
            # 901215-1234567 → 901215-*******
            masked_text = re.sub(
                r'(?<!\d)(\d{6})([-\s]?)(\d{7})(?!\d)',
                r'\1\2*******',
                masked_text
            )

        if "이메일" in active_types:
            # user@company.com → use***@company.com (마크다운 링크 내부도 처리)
            masked_text = re.sub(
                r'(?<![a-zA-Z0-9._%+-])([a-zA-Z0-9._%+-]{1,3})[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'\1***\2',
                masked_text
            )

        if "신용카드번호" in active_types:
            # 1234-5678-9012-3456 → 1234-****-****-3456
            masked_text = re.sub(
                r'(?<!\d)(\d{4})([-\s]?)(\d{4})([-\s]?)(\d{4})([-\s]?)(\d{4})(?!\d)',
                r'\1\2****\4****\6\7',
                masked_text
            )

        if "계좌번호" in active_types:
            # 110-123-456789 → 110-***-456789
            masked_text = re.sub(
                r'(?<!\d)(\d{3,6})([-\s])(\d{2,6})([-\s])(\d{4,6})(?!\d)',
                lambda m: m.group(1) + m.group(2) + '*' * len(m.group(3)) + m.group(4) + m.group(5),
                masked_text
            )

        if "주소" in active_types:
            masked_text = re.sub(
                r'(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)(특별시|광역시|특별자치시|특별자치도|도)?\s?[\w]+[시군구읍면](?:\s?[\w]+[구군동읍면리])*',
                lambda m: m.group(1) + (m.group(2) or '') + ' ***',
                masked_text
            )

        return masked_text

    def mask(self, text: str, enabled_items: Dict[str, bool] = None) -> str:
        """
        텍스트에서 개인정보를 마스킹 처리
        
        Args:
            text: 마스킹할 텍스트
            enabled_items: 감지할 항목 (None이면 모든 항목)
            
        Returns:
            마스킹된 텍스트
        """
        # enabled_items로 감지할 패턴 필터링
        if enabled_items:
            active_patterns = {}
            for key, enabled in enabled_items.items():
                if enabled and key in self.key_to_type:
                    pii_type = self.key_to_type[key]
                    if pii_type in self.patterns:
                        active_patterns[pii_type] = self.patterns[pii_type]
        else:
            active_patterns = self.patterns
        
        masked_text = text
        for pii_type, pattern in active_patterns.items():
            masked_text = re.sub(pattern, f'[{pii_type} 마스킹됨]', masked_text)
        
        return masked_text

