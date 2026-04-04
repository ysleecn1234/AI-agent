"""
AI 드라이브 - 크기별 과금 관리
기획서 기준:
- 소형 (<50KB): 0.3원/일
- 중형 (50~500KB): 0.5원/일
- 대형 (>500KB): 1원/일
"""

from typing import Dict, Any
from enum import Enum


class DocumentSize(Enum):
    """문서 크기 분류"""
    SMALL = "small"    # <50KB
    MEDIUM = "medium"  # 50~500KB
    LARGE = "large"    # >500KB


class CostManager:
    """
    문서 크기별 과금 관리
    """
    
    # 크기별 일일 비용 (원)
    DAILY_COST = {
        DocumentSize.SMALL: 0.3,
        DocumentSize.MEDIUM: 0.5,
        DocumentSize.LARGE: 1.0
    }
    
    # 크기 기준 (bytes)
    SIZE_THRESHOLD = {
        "small_max": 50 * 1024,      # 50KB
        "medium_max": 500 * 1024     # 500KB
    }
    
    def __init__(self):
        pass
    
    def classify_size(self, file_size: int) -> DocumentSize:
        """
        파일 크기 분류
        
        Args:
            file_size: 파일 크기 (bytes)
            
        Returns:
            DocumentSize (SMALL/MEDIUM/LARGE)
        """
        if file_size < self.SIZE_THRESHOLD["small_max"]:
            return DocumentSize.SMALL
        elif file_size < self.SIZE_THRESHOLD["medium_max"]:
            return DocumentSize.MEDIUM
        else:
            return DocumentSize.LARGE
    
    def calculate_daily_cost(self, file_size: int) -> Dict[str, Any]:
        """
        일일 비용 계산
        
        Args:
            file_size: 파일 크기 (bytes)
            
        Returns:
            {
                "size_category": "small/medium/large",
                "file_size_kb": 45.2,
                "daily_cost_krw": 0.3,
                "monthly_cost_krw": 9.0
            }
        """
        size_category = self.classify_size(file_size)
        daily_cost = self.DAILY_COST[size_category]
        
        return {
            "size_category": size_category.value,
            "file_size_bytes": file_size,
            "file_size_kb": round(file_size / 1024, 2),
            "daily_cost_krw": daily_cost,
            "monthly_cost_krw": round(daily_cost * 30, 2)
        }
    
    def calculate_storage_cost(
        self,
        file_size: int,
        days: int = 1
    ) -> float:
        """
        저장 비용 계산
        
        Args:
            file_size: 파일 크기 (bytes)
            days: 저장 일수
            
        Returns:
            총 비용 (원)
        """
        size_category = self.classify_size(file_size)
        daily_cost = self.DAILY_COST[size_category]
        
        return round(daily_cost * days, 2)
    
    def get_size_info(self, file_size: int) -> str:
        """
        파일 크기 정보 문자열
        """
        size_category = self.classify_size(file_size)
        size_kb = file_size / 1024
        
        category_name = {
            DocumentSize.SMALL: "소형",
            DocumentSize.MEDIUM: "중형",
            DocumentSize.LARGE: "대형"
        }
        
        return f"{category_name[size_category]} ({size_kb:.1f}KB)"