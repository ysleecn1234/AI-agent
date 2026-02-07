"""
AI-agent 로깅 및 추적 시스템
요청-처리-결과 전 과정을 로깅하여 운영성과 감사 대응성 확보
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import os


class PipelineLogger:
    """
    파이프라인 전체 흐름을 추적하는 로거
    - 요청 접수부터 최종 결과까지 모든 단계 기록
    - 운영 모니터링 및 감사 추적 지원
    - 비용 추적 및 성능 분석 데이터 수집
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        Args:
            log_dir: 로그 파일 저장 디렉토리
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 기본 로거 설정
        self.logger = self._setup_logger()
        
        # 현재 세션 정보
        self.current_session: Optional[Dict[str, Any]] = None
    
    def _setup_logger(self) -> logging.Logger:
        """로거 초기 설정"""
        logger = logging.getLogger("AIAgent")
        logger.setLevel(logging.INFO)
        
        # 파일 핸들러 (JSON 형식)
        json_handler = logging.FileHandler(
            self.log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d')}.jsonl",
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러 (사람이 읽기 쉬운 형식)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(json_handler)
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
        self._log_json({
            "event": "session_start",
            "session_id": session_id,
            "user_id": user_id,
            "user_input": user_input,
            "timestamp": self.current_session["start_time"]
        })
        
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
        
        self._log_json({
            "event": "step_completed",
            "session_id": self.current_session["session_id"],
            "step_name": step_name,
            "duration_ms": duration_ms,
            "timestamp": step_log["timestamp"]
        })
        
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
            usage_log["in7_cost_krw"] = cost_info.get("in7_comparison", {}).get("in7_cost_krw", 0)
            usage_log["savings_krw"] = cost_info.get("in7_comparison", {}).get("savings_krw", 0)
            usage_log["savings_rate"] = cost_info.get("in7_comparison", {}).get("savings_rate", 0)
        
        if "model_usage" not in self.current_session["metadata"]:
            self.current_session["metadata"]["model_usage"] = []
        
        self.current_session["metadata"]["model_usage"].append(usage_log)
        
        self._log_json({
            "event": "model_usage",
            "session_id": self.current_session["session_id"],
            **usage_log
        })
    
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
        
        self._log_json({
            "event": "error",
            "session_id": self.current_session["session_id"],
            **error_log
        })
        
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
        
        # 전체 세션 로그 저장
        self._save_session_log()
        
        self._log_json({
            "event": "session_end",
            "session_id": self.current_session["session_id"],
            "success": success,
            "total_duration_ms": total_duration,
            "timestamp": end_time.isoformat()
        })
        
        self.logger.info(
            f"Session ended: {self.current_session['session_id']} "
            f"(Success: {success}, Duration: {total_duration:.0f}ms)"
        )
        
        # 세션 초기화
        self.current_session = None
    
    def _save_session_log(self):
        """전체 세션 로그를 파일로 저장"""
        if not self.current_session:
            return
        
        session_file = self.log_dir / f"session_{self.current_session['session_id']}.json"
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_session, f, ensure_ascii=False, indent=2)
    
    def _log_json(self, data: Dict[str, Any]):
        """JSON 형식으로 로그 기록"""
        # JSONL 형식으로 추가 (한 줄에 하나의 JSON)
        log_file = self.log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
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
