"""
AI 드라이브 - 스케줄러
1. 아카이브 자동 삭제: 매일 새벽 2시에 30일 이상 된 아카이브 문서 삭제
2. 일일 Storage 과금: 매일 새벽 2시에 active 문서 대상 일일 저장 비용 기록
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
sys.path.insert(0, str(current_dir.parent.parent))  # 프로젝트 루트

from db.postgres_client import PostgresClient
from db.milvus_client import MilvusClient


# 설정
ARCHIVE_DAYS = 30  # 30일 이상 된 문서 삭제


def cleanup_old_archives():
    """
    30일 이상 된 아카이브 문서 삭제
    - PostgreSQL에서 삭제
    - Milvus에서 삭제
    - 파일 삭제
    """
    STORAGE_DIR = current_dir / "storage"
    
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


def bill_daily_storage():
    """
    일일 Storage 과금
    - status='active'인 문서 전체 조회
    - 각 문서의 file_size 기준으로 CostManager.calculate_daily_cost()
    - cost_logs에 operation='storage'로 기록
    """
    print("=" * 60)
    print(f"[{datetime.now()}] 일일 Storage 과금 시작")
    print("=" * 60)
    
    postgres = None
    
    try:
        postgres = PostgresClient()
        
        from core.cost_manager import CostManager
        from services.common.cost_logger import get_cost_logger
        
        cost_manager = CostManager()
        cost_logger = get_cost_logger()
        
        # active 문서 전체 조회
        active_docs = postgres.get_all_active_documents()
        
        if not active_docs:
            print("✓ 과금 대상 문서 없음")
            return
        
        print(f"과금 대상: {len(active_docs)}개 문서")
        
        billed_count = 0
        total_cost_krw = 0.0
        
        for doc in active_docs:
            try:
                file_size = doc["file_size"]
                storage_cost = cost_manager.calculate_daily_cost(file_size)
                daily_krw = storage_cost["daily_cost_krw"]
                
                cost_logger.log_embedding_cost(
                    user_id=doc["creator_id"],
                    doc_id=doc["doc_id"],
                    tokens=0,
                    cost_usd=daily_krw / 1400,
                    cost_krw=daily_krw,
                    operation="storage",
                )
                
                billed_count += 1
                total_cost_krw += daily_krw
                
            except Exception as e:
                print(f"  ✗ 과금 실패: {doc['title']} - {str(e)}")
        
        print("-" * 60)
        print(f"✓ 과금 완료: {billed_count}/{len(active_docs)}개 문서")
        print(f"  총 일일 비용: ₩{total_cost_krw:.1f}")
        
    except Exception as e:
        print(f"✗ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if postgres:
            postgres.close()
    
    print("=" * 60)


def main():
    """스케줄러 실행"""
    
    # 테스트 모드 확인
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("테스트 모드: 즉시 실행")
        cleanup_old_archives()
        bill_daily_storage()
        return
    
    # 스케줄러 설정
    scheduler = BlockingScheduler()
    
    # 매일 새벽 2시: 아카이브 정리
    scheduler.add_job(
        cleanup_old_archives,
        CronTrigger(hour=2, minute=0),
        id="cleanup_archives",
        name="아카이브 자동 삭제"
    )
    
    # 매일 새벽 2시 5분: 일일 Storage 과금
    scheduler.add_job(
        bill_daily_storage,
        CronTrigger(hour=2, minute=5),
        id="daily_storage_billing",
        name="일일 Storage 과금"
    )
    
    print("=" * 60)
    print("AI 드라이브 스케줄러 시작")
    print("=" * 60)
    print(f"작업 1: 아카이브 정리 (매일 02:00, {ARCHIVE_DAYS}일 기준)")
    print(f"작업 2: 일일 Storage 과금 (매일 02:05)")
    print("종료: Ctrl+C")
    print("=" * 60)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n스케줄러 종료")


if __name__ == "__main__":
    main()