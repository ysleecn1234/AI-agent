"""
AI 드라이브 - 텍스트 청킹 유틸리티
긴 텍스트를 토큰 단위로 분할
"""

import tiktoken
from typing import List


class TextChunker:
    """
    텍스트를 토큰 기반으로 청킹
    - 청크 크기: 1000토큰
    - 오버랩: 200토큰
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding_name: str = "cl100k_base"
    ):
        """
        Args:
            chunk_size: 청크당 토큰 수
            chunk_overlap: 청크 간 오버랩 토큰 수
            encoding_name: tiktoken 인코딩 이름
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
    
    def chunk(self, text: str) -> List[str]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            청크 리스트
        """
        if not text or not text.strip():
            return []
        
        # 텍스트를 토큰으로 인코딩
        tokens = self.encoding.encode(text)
        
        # 청크 생성
        chunks = []
        start_idx = 0
        
        while start_idx < len(tokens):
            # 청크 끝 인덱스
            end_idx = start_idx + self.chunk_size
            
            # 현재 청크의 토큰들
            chunk_tokens = tokens[start_idx:end_idx]
            
            # 토큰을 텍스트로 디코딩
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # 다음 시작 위치 (오버랩 적용)
            start_idx = end_idx - self.chunk_overlap
        
        return chunks
    
    def get_token_count(self, text: str) -> int:
        """
        텍스트의 토큰 수 계산
        
        Args:
            text: 토큰 수를 계산할 텍스트
            
        Returns:
            토큰 수
        """
        return len(self.encoding.encode(text))
    
    def chunk_with_metadata(self, text: str) -> List[dict]:
        """
        메타데이터를 포함한 청크 생성
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            메타데이터 포함 청크 리스트
            [{
                "text": "청크 텍스트",
                "chunk_index": 0,
                "token_count": 950,
                "char_count": 3200
            }, ...]
        """
        chunks = self.chunk(text)
        
        result = []
        for idx, chunk_text in enumerate(chunks):
            result.append({
                "text": chunk_text,
                "chunk_index": idx,
                "token_count": self.get_token_count(chunk_text),
                "char_count": len(chunk_text)
            })
        
        return result


# 테스트 코드
if __name__ == "__main__":
    chunker = TextChunker()
    
    # 테스트 텍스트 (긴 텍스트)
    test_text = "이것은 테스트 텍스트입니다. " * 500  # 약 5000자
    
    print("=" * 80)
    print("TextChunker 테스트")
    print("=" * 80)
    print(f"원본 텍스트 길이: {len(test_text)}자")
    print(f"원본 토큰 수: {chunker.get_token_count(test_text)}")
    
    # 청킹
    chunks = chunker.chunk(test_text)
    
    print(f"\n생성된 청크 수: {len(chunks)}")
    print("-" * 80)
    
    for idx, chunk in enumerate(chunks[:3]):  # 처음 3개만 출력
        print(f"\n[청크 {idx + 1}]")
        print(f"길이: {len(chunk)}자")
        print(f"토큰 수: {chunker.get_token_count(chunk)}")
        print(f"미리보기: {chunk[:100]}...")
    
    if len(chunks) > 3:
        print(f"\n... (나머지 {len(chunks) - 3}개 청크)")