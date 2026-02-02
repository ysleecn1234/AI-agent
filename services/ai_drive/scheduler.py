"""
AI 드라이브 - 아카이브 자동 삭제 스케줄러
매일 새벽 2시에 30일 이상 된 아카이브 문서 삭제
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# 상위 디렉토리 import 설정
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from db.postgres_client import PostgresClient
from db.milvus_client import MilvusClient


# 설정
ARCHIVE_DAYS = 30  # 30일 이상 된 문서 삭제
STORAGE_DIR = current_dir / "storage"


def cleanup_old_archives():
    """
    30일 이상 된 아카이브 문서 삭제
    - PostgreSQL에서 삭제
    - Milvus에서 삭제
    - 파일 삭제
    """
    print("=" * 60)
    print(f"[{datetime.now()}] 아카이브 정리 시작")
    print("=" * 60)
    
    postgres = None
    milvus = None
    
    try:
        # DB 연결
        postgres = PostgresClient()
        milvus = MilvusClient()
        
        # 30일 이상 된 아카이브 문서 조회
        old_docs = postgres.get_old_archives(days=ARCHIVE_DAYS)
        
        if not old_docs:
            print("✓ 삭제할 문서 없음")
            return
        
        print(f"삭제 대상: {len(old_docs)}개")
        
        deleted_count = 0
        
        for doc in old_docs:
            doc_id = doc["doc_id"]
            title = doc["title"]
            file_path = doc.get("file_path")
            
            try:
                # 1. Milvus에서 삭제
                milvus.delete_by_doc_id(doc_id)
                
                # 2. PostgreSQL에서 삭제
                postgres.hard_delete_document(doc_id)
                
                # 3. 파일 삭제
                if file_path:
                    full_path = Path(file_path)
                    if not full_path.is_absolute():
                        full_path = STORAGE_DIR / file_path
                    
                    if full_path.exists():
                        os.remove(full_path)
                        print(f"  ✓ 파일 삭제: {full_path}")
                
                deleted_count += 1
                print(f"  ✓ 삭제 완료: {title} ({doc_id})")
                
            except Exception as e:
                print(f"  ✗ 삭제 실패: {title} - {str(e)}")
        
        print("-" * 60)
        print(f"✓ 정리 완료: {deleted_count}/{len(old_docs)}개 삭제")
        
    except Exception as e:
        print(f"✗ 오류 발생: {str(e)}")
        
    finally:
        if postgres:
            postgres.close()
        if milvus:
            milvus.close()
    
    print("=" * 60)


def main():
    """스케줄러 실행"""
    
    # 테스트 모드 확인
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("테스트 모드: 즉시 실행")
        cleanup_old_archives()
        return
    
    # 스케줄러 설정
    scheduler = BlockingScheduler()
    
    # 매일 새벽 2시 실행
    scheduler.add_job(
        cleanup_old_archives,
        CronTrigger(hour=2, minute=0),
        id="cleanup_archives",
        name="아카이브 자동 삭제"
    )
    
    print("=" * 60)
    print("AI 드라이브 스케줄러 시작")
    print("=" * 60)
    print(f"실행 시간: 매일 새벽 2시")
    print(f"삭제 기준: {ARCHIVE_DAYS}일 이상 된 아카이브")
    print("종료: Ctrl+C")
    print("=" * 60)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n스케줄러 종료")


if __name__ == "__main__":
    main()