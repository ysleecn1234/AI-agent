"""
AI-agent 비용 계산 시스템
모델별 토큰 단가 및 실시간 비용 추적
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModelPricing:
    """모델 가격 정보"""
    input_price_per_1m: float  # 입력 토큰 100만개당 USD
    output_price_per_1m: float  # 출력 토큰 100만개당 USD
    provider: str  # 제공사 (OpenAI, Anthropic, Google 등)


class CostCalculator:
    """
    비용 계산 및 추적 시스템
    - 모델별 토큰 단가 관리
    - 실시간 비용 계산
    - IN7 요금표 대비 절감률 계산
    """
    
    def __init__(self):
        # 모델별 가격 테이블 (2026년 1월 기준 최신 가격)
        self.pricing_table: Dict[str, ModelPricing] = {
            # OpenAI GPT-5 시리즈
            "gpt-5": ModelPricing(
                input_price_per_1m=5.00,
                output_price_per_1m=15.00,
                provider="OpenAI"
            ),
            "gpt-4o-mini": ModelPricing(
                input_price_per_1m=0.15,
                output_price_per_1m=0.60,
                provider="OpenAI"
            ),
            "gpt-3.5-turbo": ModelPricing(
                input_price_per_1m=0.50,
                output_price_per_1m=1.50,
                provider="OpenAI"
            ),
            "openai/o1": ModelPricing(
                input_price_per_1m=15.00,
                output_price_per_1m=60.00,
                provider="OpenAI"
            ),
            
            # Anthropic Claude 4 시리즈
            "claude-4-sonnet": ModelPricing(
                input_price_per_1m=3.00,
                output_price_per_1m=15.00,
                provider="Anthropic"
            ),
            "claude-3-opus": ModelPricing(
                input_price_per_1m=15.00,
                output_price_per_1m=75.00,
                provider="Anthropic"
            ),
            "claude-3-haiku": ModelPricing(
                input_price_per_1m=0.25,
                output_price_per_1m=1.25,
                provider="Anthropic"
            ),
            
            # Google Gemini 2.0 시리즈
            "gemini/gemini-2.0-flash-exp": ModelPricing(
                input_price_per_1m=0.075,
                output_price_per_1m=0.30,
                provider="Google"
            ),
            "gemini/gemini-2.0-pro-exp": ModelPricing(
                input_price_per_1m=1.25,
                output_price_per_1m=5.00,
                provider="Google"
            ),
            
            # Meta Llama 4 시리즈 (오픈소스 - 인프라 비용만)
            "meta-llama/llama-4-8b": ModelPricing(
                input_price_per_1m=0.10,
                output_price_per_1m=0.10,
                provider="Meta"
            ),
            "meta-llama/llama-4-70b": ModelPricing(
                input_price_per_1m=0.80,
                output_price_per_1m=0.80,
                provider="Meta"
            ),
        }
        
        # IN7 요금표 (기획서 기준 - 원가 대비 약 2배)
        # 예시: GPT-4o-mini 입력 0.4원, 출력 1.6원
        self.in7_markup_rate = 2.0  # IN7은 원가 대비 2배 청구
        
        # 환율 (USD to KRW)
        # TODO: 나중에 실시간 환율 API 연동 고려
        self.usd_to_krw = 1400.0
    
    def calculate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """
        모델 사용 비용 계산
        
        Args:
            model_name: 모델명
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
        
        Returns:
            비용 정보 딕셔너리
        """
        # 모델 가격 정보 가져오기
        pricing = self.pricing_table.get(model_name)
        
        if not pricing:
            # 알 수 없는 모델은 평균 가격으로 추정
            pricing = ModelPricing(
                input_price_per_1m=1.0,
                output_price_per_1m=3.0,
                provider="Unknown"
            )
        
        # 비용 계산 (USD)
        input_cost_usd = (input_tokens / 1_000_000) * pricing.input_price_per_1m
        output_cost_usd = (output_tokens / 1_000_000) * pricing.output_price_per_1m
        total_cost_usd = input_cost_usd + output_cost_usd
        
        # 비용 계산 (KRW)
        input_cost_krw = input_cost_usd * self.usd_to_krw
        output_cost_krw = output_cost_usd * self.usd_to_krw
        total_cost_krw = total_cost_usd * self.usd_to_krw
        
        # IN7 예상 청구 금액 (원가 대비 2배)
        in7_cost_krw = total_cost_krw * self.in7_markup_rate
        
        # 절감액 및 절감률
        savings_krw = in7_cost_krw - total_cost_krw
        savings_rate = (savings_krw / in7_cost_krw * 100) if in7_cost_krw > 0 else 0
        
        return {
            "model": model_name,
            "provider": pricing.provider,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            },
            "cost_usd": {
                "input": round(input_cost_usd, 6),
                "output": round(output_cost_usd, 6),
                "total": round(total_cost_usd, 6)
            },
            "cost_krw": {
                "input": round(input_cost_krw, 2),
                "output": round(output_cost_krw, 2),
                "total": round(total_cost_krw, 2)
            },
            "in7_comparison": {
                "in7_cost_krw": round(in7_cost_krw, 2),
                "our_cost_krw": round(total_cost_krw, 2),
                "savings_krw": round(savings_krw, 2),
                "savings_rate": round(savings_rate, 1)
            }
        }
    
    def estimate_cost_by_complexity(
        self,
        complexity: str,
        estimated_input_tokens: int = 1000,
        estimated_output_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        복잡도별 예상 비용 계산
        
        Args:
            complexity: 복잡도 (simple, complex, bulk)
            estimated_input_tokens: 예상 입력 토큰
            estimated_output_tokens: 예상 출력 토큰
        
        Returns:
            복잡도별 모델 비용 비교
        """
        # 복잡도별 주 모델
        model_mapping = {
            "simple": "gemini/gemini-2.0-flash-exp",
            "complex": "gpt-5",
            "bulk": "claude-4-sonnet"
        }
        
        primary_model = model_mapping.get(complexity, "gemini/gemini-2.0-flash-exp")
        
        return self.calculate_cost(
            primary_model,
            estimated_input_tokens,
            estimated_output_tokens
        )
    
    def generate_cost_report(
        self,
        session_logs: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        세션 로그 기반 비용 리포트 생성
        
        Args:
            session_logs: 세션별 비용 로그 리스트
        
        Returns:
            종합 비용 리포트
        """
        total_cost_usd = 0.0
        total_cost_krw = 0.0
        total_in7_cost_krw = 0.0
        total_tokens = 0
        
        model_breakdown = {}
        
        for log in session_logs:
            cost_usd = log.get("cost_usd", {}).get("total", 0)
            cost_krw = log.get("cost_krw", {}).get("total", 0)
            in7_cost = log.get("in7_comparison", {}).get("in7_cost_krw", 0)
            tokens = log.get("tokens", {}).get("total", 0)
            model = log.get("model", "unknown")
            
            total_cost_usd += cost_usd
            total_cost_krw += cost_krw
            total_in7_cost_krw += in7_cost
            total_tokens += tokens
            
            # 모델별 집계
            if model not in model_breakdown:
                model_breakdown[model] = {
                    "count": 0,
                    "tokens": 0,
                    "cost_krw": 0
                }
            
            model_breakdown[model]["count"] += 1
            model_breakdown[model]["tokens"] += tokens
            model_breakdown[model]["cost_krw"] += cost_krw
        
        # 총 절감액 및 절감률
        total_savings_krw = total_in7_cost_krw - total_cost_krw
        total_savings_rate = (total_savings_krw / total_in7_cost_krw * 100) if total_in7_cost_krw > 0 else 0
        
        return {
            "summary": {
                "total_sessions": len(session_logs),
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost_usd, 4),
                "total_cost_krw": round(total_cost_krw, 2),
                "in7_cost_krw": round(total_in7_cost_krw, 2),
                "savings_krw": round(total_savings_krw, 2),
                "savings_rate": round(total_savings_rate, 1)
            },
            "model_breakdown": model_breakdown,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_pricing_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """모델 가격 정보 조회"""
        pricing = self.pricing_table.get(model_name)
        
        if not pricing:
            return None
        
        return {
            "model": model_name,
            "provider": pricing.provider,
            "pricing_usd": {
                "input_per_1m": pricing.input_price_per_1m,
                "output_per_1m": pricing.output_price_per_1m
            },
            "pricing_krw": {
                "input_per_1m": round(pricing.input_price_per_1m * self.usd_to_krw, 2),
                "output_per_1m": round(pricing.output_price_per_1m * self.usd_to_krw, 2)
            }
        }
    
    def list_all_models(self) -> list[str]:
        """지원하는 모든 모델 목록 반환"""
        return list(self.pricing_table.keys())


# 전역 비용 계산기 인스턴스
_global_calculator: Optional[CostCalculator] = None


def get_cost_calculator() -> CostCalculator:
    """전역 비용 계산기 인스턴스 반환"""
    global _global_calculator
    if _global_calculator is None:
        _global_calculator = CostCalculator()
    return _global_calculator


# 테스트 코드
if __name__ == "__main__":
    calculator = CostCalculator()
    
    print("=" * 80)
    print("비용 계산 시스템 테스트")
    print("=" * 80)
    
    # 1. 단일 모델 비용 계산
    print("\n[테스트 1] GPT-5 비용 계산 (입력 1000토큰, 출력 500토큰)")
    cost = calculator.calculate_cost("gpt-5", 1000, 500)
    print(f"모델: {cost['model']}")
    print(f"총 토큰: {cost['tokens']['total']}")
    print(f"비용 (USD): ${cost['cost_usd']['total']}")
    print(f"비용 (KRW): {cost['cost_krw']['total']:,}원")
    print(f"IN7 예상 청구액: {cost['in7_comparison']['in7_cost_krw']:,}원")
    print(f"절감액: {cost['in7_comparison']['savings_krw']:,}원")
    print(f"절감률: {cost['in7_comparison']['savings_rate']}%")
    
    # 2. 복잡도별 비용 비교
    print("\n[테스트 2] 복잡도별 비용 비교")
    for complexity in ["simple", "complex", "bulk"]:
        cost = calculator.estimate_cost_by_complexity(complexity, 1000, 500)
        print(f"\n{complexity.upper()}: {cost['model']}")
        print(f"  비용: {cost['cost_krw']['total']:,}원")
        print(f"  절감률: {cost['in7_comparison']['savings_rate']}%")
    
    # 3. 모델 가격 정보 조회
    print("\n[테스트 3] 모델 가격 정보")
    for model in ["gemini/gemini-2.0-flash-exp", "gpt-5", "claude-4-sonnet"]:
        info = calculator.get_pricing_info(model)
        if info:
            print(f"\n{model}:")
            print(f"  제공사: {info['provider']}")
            print(f"  입력: ${info['pricing_usd']['input_per_1m']}/1M ({info['pricing_krw']['input_per_1m']:,}원/1M)")
            print(f"  출력: ${info['pricing_usd']['output_per_1m']}/1M ({info['pricing_krw']['output_per_1m']:,}원/1M)")
