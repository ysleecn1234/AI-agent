"""
AI 드라이브 - 임베딩 생성
OpenAI text-embedding-3-small 사용
"""

import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
import time

# 환경 변수 로드
load_dotenv()


class EmbeddingGenerator:
    """
    텍스트를 벡터로 변환
    - 모델: text-embedding-3-small
    - 차원: 1536
    - 비용: 1K 토큰당 약 0.003원
    """
    
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.last_usage = None  # 마지막 호출의 토큰 사용량
    
    def create(self, text: str) -> List[float]:
        """
        단일 텍스트 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            임베딩 벡터 (1536차원)
        """
        if not text or not text.strip():
            raise ValueError("빈 텍스트는 임베딩할 수 없습니다.")
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        self.last_usage = response.usage
        return response.data[0].embedding
    
    def create_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        여러 텍스트 일괄 임베딩 생성 (배치 분할)
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 한 번에 처리할 최대 개수 (기본 100)
            
        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []
        
        # 빈 텍스트 필터링
        valid_texts = [t for t in texts if t and t.strip()]
        
        if not valid_texts:
            return []
        
        all_embeddings = []
        
        # 배치 분할 처리
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            
            # 재시도 로직 (최대 3회)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=batch
                    )
                    break  # 성공하면 루프 탈출
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(1)  # 1초 대기 후 재시도
                    else:
                        raise e  # 3번 다 실패하면 에러 발생
            
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            
            # 토큰 사용량 누적
            if self.last_usage is None:
                self.last_usage = response.usage
            else:
                self.last_usage.total_tokens += response.usage.total_tokens
            

        return all_embeddings

    def get_dimension(self) -> int:
        """
        임베딩 차원 수 반환
        
        Returns:
            차원 수 (text-embedding-3-small = 1536)
        """
        return 1536