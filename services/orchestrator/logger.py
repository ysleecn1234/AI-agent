"""
AI-agent 로깅 및 추적 시스템
요청-처리-결과 전 과정을 로깅하여 운영성과 감사 대응성 확보
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


class PipelineLogger:
    """
    파이프라인 전체 흐름을 추적하는 로거
    - 요청 접수부터 최종 결과까지 모든 단계 기록
    - 운영 모니터링 및 감사 추적 지원
    - 비용 추적 및 성능 분석 데이터 수집
    """
    
    def __init__(self):
        # 콘솔 로거 설정
        self.logger = self._setup_logger()
        
        # 현재 세션 정보 (메모리)
        self.current_session: Optional[Dict[str, Any]] = None
    
    def _setup_logger(self) -> logging.Logger:
        """콘솔 로거 설정"""
        logger = logging.getLogger("AIAgent")
        logger.setLevel(logging.INFO)
        
        # 핸들러 중복 방지
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def start_session(self, user_input: str, user_id: Optional[str] = None) -> str:
        """
        새로운 요청 세션 시작
        
        Args:
            user_input: 사용자 입력
            user_id: 사용자 ID (선택)
        
        Returns:
            session_id: 생성된 세션 ID
        """
        session_id = str(uuid.uuid4())
        
        self.current_session = {
            "session_id": session_id,
            "user_id": user_id,
            "user_input": user_input,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "metadata": {}
        }
        
        self.logger.info(f"Session started: {session_id}")
        return session_id
    
    def log_step(
        self,
        step_name: str,
        step_data: Dict[str, Any],
        duration_ms: Optional[float] = None
    ):
        """
        파이프라인 단계 로깅
        
        Args:
            step_name: 단계 이름 (Router, Researcher, Reasoner 등)
            step_data: 단계별 처리 데이터
            duration_ms: 처리 시간 (밀리초)
        """
        if not self.current_session:
            self.logger.warning("No active session for logging step")
            return
        
        step_log = {
            "step_name": step_name,
            "timestamp": datetime.now().isoformat(),
            "data": step_data,
            "duration_ms": duration_ms
        }
        
        self.current_session["steps"].append(step_log)
        self.logger.info(f"Step completed: {step_name} ({duration_ms}ms)")
    
    def log_model_usage(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_info: Optional[Dict[str, Any]] = None
    ):
        """
        모델 사용 로깅 (비용 추적)
        
        Args:
            model_name: 사용된 모델명
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
            cost_info: 비용 정보 (CostCalculator에서 계산된 결과)
        """
        if not self.current_session:
            return
        
        usage_log = {
            "model": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "timestamp": datetime.now().isoformat()
        }
        
        # 비용 정보 추가
        if cost_info:
            usage_log["cost_usd"] = cost_info.get("cost_usd", {}).get("total", 0)
            usage_log["cost_krw"] = cost_info.get("cost_krw", {}).get("total", 0)
        
        if "model_usage" not in self.current_session["metadata"]:
            self.current_session["metadata"]["model_usage"] = []
        
        self.current_session["metadata"]["model_usage"].append(usage_log)
    
    def log_error(self, error_type: str, error_message: str, step_name: Optional[str] = None):
        """
        에러 로깅
        
        Args:
            error_type: 에러 타입
            error_message: 에러 메시지
            step_name: 에러 발생 단계
        """
        if not self.current_session:
            return
        
        error_log = {
            "error_type": error_type,
            "error_message": error_message,
            "step_name": step_name,
            "timestamp": datetime.now().isoformat()
        }
        
        if "errors" not in self.current_session["metadata"]:
            self.current_session["metadata"]["errors"] = []
        
        self.current_session["metadata"]["errors"].append(error_log)
        self.logger.error(f"Error in {step_name}: {error_type} - {error_message}")
    
    def end_session(self, final_result: Dict[str, Any], success: bool = True):
        """
        세션 종료 및 최종 결과 로깅
        
        Args:
            final_result: 최종 결과 데이터
            success: 성공 여부
        """
        if not self.current_session:
            return
        
        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.current_session["start_time"])
        total_duration = (end_time - start_time).total_seconds() * 1000  # ms
        
        self.current_session["end_time"] = end_time.isoformat()
        self.current_session["total_duration_ms"] = total_duration
        self.current_session["success"] = success
        self.current_session["final_result"] = final_result
         
        self.logger.info(
            f"Session ended: {self.current_session['session_id']} "
            f"(Success: {success}, Duration: {total_duration:.0f}ms)"
        )
        
        # 세션 초기화
        self.current_session = None
    
    def get_session_summary(self) -> Optional[Dict[str, Any]]:
        """현재 세션 요약 정보 반환"""
        if not self.current_session:
            return None
        
        total_cost = 0.0
        if "model_usage" in self.current_session["metadata"]:
            for usage in self.current_session["metadata"]["model_usage"]:
                if usage.get("cost_usd"):
                    total_cost += usage["cost_usd"]
        
        return {
            "session_id": self.current_session["session_id"],
            "user_input": self.current_session["user_input"],
            "steps_completed": len(self.current_session["steps"]),
            "total_cost_usd": total_cost,
            "errors": len(self.current_session["metadata"].get("errors", []))
        }


# 전역 로거 인스턴스
_global_logger: Optional[PipelineLogger] = None


def get_logger() -> PipelineLogger:
    """전역 로거 인스턴스 반환"""
    global _global_logger
    if _global_logger is None:
        _global_logger = PipelineLogger()
    return _global_logger
