"""
AI 드라이브 - 임베딩 생성
OpenAI text-embedding-3-small 사용
"""

import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

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
        """
        Args:
            model: 임베딩 모델명
        """
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
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
        
        return response.data[0].embedding
    
    def create_batch(self, texts: List[str]) -> List[List[float]]:
        """
        여러 텍스트 일괄 임베딩 생성
        
        Args:
            texts: 임베딩할 텍스트 리스트
            
        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []
        
        # 빈 텍스트 필터링
        valid_texts = [t for t in texts if t and t.strip()]
        
        if not valid_texts:
            return []
        
        response = self.client.embeddings.create(
            model=self.model,
            input=valid_texts
        )
        
        # 인덱스 순서대로 정렬
        embeddings = [item.embedding for item in response.data]
        
        return embeddings
    
    def get_dimension(self) -> int:
        """
        임베딩 차원 수 반환
        
        Returns:
            차원 수 (text-embedding-3-small = 1536)
        """
        return 1536


# 테스트 코드
if __name__ == "__main__":
    print("=" * 80)
    print("EmbeddingGenerator 테스트")
    print("=" * 80)
    
    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY=sk-xxx 추가하세요.")
        exit(1)
    
    print(f"✓ API 키 확인: {api_key[:10]}...")
    
    try:
        generator = EmbeddingGenerator()
        
        # 단일 텍스트 테스트
        test_text = "AI 드라이브는 문서 관리 시스템입니다."
        embedding = generator.create(test_text)
        
        print(f"\n[단일 텍스트 테스트]")
        print(f"입력: {test_text}")
        print(f"임베딩 차원: {len(embedding)}")
        print(f"임베딩 미리보기: {embedding[:5]}...")
        
        # 배치 테스트
        test_texts = [
            "첫 번째 테스트 문장입니다.",
            "두 번째 테스트 문장입니다.",
            "세 번째 테스트 문장입니다."
        ]
        embeddings = generator.create_batch(test_texts)
        
        print(f"\n[배치 테스트]")
        print(f"입력 개수: {len(test_texts)}")
        print(f"출력 개수: {len(embeddings)}")
        print(f"각 임베딩 차원: {len(embeddings[0])}")
        
        print("\n" + "=" * 80)
        print("✓ 테스트 성공!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")