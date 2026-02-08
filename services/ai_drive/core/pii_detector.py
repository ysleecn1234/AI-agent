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
        # 정규식 패턴 정의
        self.patterns = {
            "주민등록번호": r'\d{6}[-\s]?\d{7}',
            "전화번호": r'(01[016789][-\s]?\d{3,4}[-\s]?\d{4}|0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})',
            "이메일": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "계좌번호": r'\d{3,4}[-\s]?\d{2,4}[-\s]?\d{4,6}[-\s]?\d{0,4}',
            "신용카드번호": r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
        }
    
    def detect(self, text: str) -> Dict[str, Any]:
        """
        텍스트에서 개인정보 감지
        
        Args:
            text: 검사할 텍스트
            
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
        
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            
            if matches:
                # 주민등록번호는 추가 검증 (앞자리가 유효한 생년월일인지)
                if pii_type == "주민등록번호":
                    matches = self._validate_rrn(matches)
                
                if matches:
                    count = len(matches)
                    findings.append({
                        "type": pii_type,
                        "count": count
                    })
                    total_count += count
        
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


# 테스트 코드
if __name__ == "__main__":
    detector = PIIDetector()
    
    # 테스트 텍스트
    test_text = """
    안녕하세요, 김철수입니다.
    연락처: 010-1234-5678
    이메일: test@example.com
    주민번호: 901215-1234567
    계좌번호: 110-123-456789
    신용카드: 1234-5678-9012-3456
    """
    
    print("=" * 60)
    print("개인정보 감지 테스트")
    print("=" * 60)
    
    result = detector.detect(test_text)
    
    print(f"개인정보 포함: {result['has_pii']}")
    print(f"총 감지 수: {result['total_count']}")
    print("-" * 60)
    
    for finding in result['findings']:
        print(f"  - {finding['type']}: {finding['count']}건")
    
    print("=" * 60)