# Utils 모듈

AI 드라이브의 유틸리티 기능을 담당하는 모듈입니다.

## 📂 파일 구조
```
utils/
├── file_parser.py   # 파일 파싱
└── chunker.py       # 텍스트 청킹
```

## �� 파일별 설명

### 1. file_parser.py
- **역할**: 다양한 파일 형식에서 텍스트 추출
- **지원 형식**:
  - PDF (.pdf)
  - Word (.docx)
  - PowerPoint (.pptx)
  - Excel (.xlsx)
  - 텍스트 (.txt, .md)
  - CSV (.csv)
- **주요 메서드**:
  - `parse(file_path)` - 파일에서 텍스트 추출

### 2. chunker.py
- **역할**: 긴 텍스트를 작은 청크로 분할
- **설정**:
  - 청크 크기: 1000 토큰
  - 오버랩: 200 토큰
- **주요 메서드**:
  - `chunk(text)` - 텍스트 청킹
  - `get_token_count(text)` - 토큰 수 계산

## 🔗 사용 예시
```python
from utils.file_parser import FileParser
from utils.chunker import TextChunker

# 파일 파싱
parser = FileParser()
text = parser.parse("document.pdf")

# 청킹
chunker = TextChunker()
chunks = chunker.chunk(text)
```