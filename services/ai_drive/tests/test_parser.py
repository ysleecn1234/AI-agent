"""
FileParser 테스트 스크립트
"""
from pathlib import Path
import sys

# 상위 디렉토리를 Python 경로에 추가
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils.file_parser import FileParser


def test_parser():
    parser = FileParser()
    test_dir = Path(__file__).parent.parent / "test_files"
    
    print("=" * 80)
    print("FileParser 테스트 시작")
    print("=" * 80)
    
    # 테스트할 파일들
    test_files = [
        "test.txt",
        "test.md",
        "test.csv",
        "test.pdf",
        "test.docx",
        "test.pptx"
    ]
    
    success_count = 0
    fail_count = 0
    
    for filename in test_files:
        file_path = test_dir / filename
        
        if not file_path.exists():
            print(f"\n❌ {filename}: 파일 없음")
            fail_count += 1
            continue
        
        try:
            print(f"\n✅ {filename} 테스트:")
            print("-" * 80)
            
            # 파일 파싱
            text = parser.parse(str(file_path))
            
            # 결과 출력 (처음 300자만)
            preview = text[:300] if len(text) > 300 else text
            print(preview)
            
            if len(text) > 300:
                print(f"\n... (총 {len(text)}자)")
            
            print(f"\n✓ 파싱 성공! (총 {len(text)}자 추출)")
            success_count += 1
            
        except Exception as e:
            print(f"\n✗ 파싱 실패: {str(e)}")
            fail_count += 1
    
    print("\n" + "=" * 80)
    print("테스트 결과")
    print("=" * 80)
    print(f"✓ 성공: {success_count}개")
    print(f"✗ 실패: {fail_count}개")
    print("=" * 80)


if __name__ == "__main__":
    test_parser()