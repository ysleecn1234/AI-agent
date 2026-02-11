
import sys
from pathlib import Path
from sqlalchemy import text

# 프로젝트 루트를 Python 경로에 추가
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from application.database import SessionLocal, engine
    from services.ai_hub.db.tables import Agent
    
    print("✅ Connecting to Database...")
    
    # DB 연결 테스트
    db = SessionLocal()
    
    try:
        # 테이블 존재 여부 확인 (SQLAlchemy Core)
        inspector = text("SELECT to_regclass('public.agents');")
        result = db.execute(inspector).scalar()
        
        if result:
            count = db.query(Agent).count()
            print(f"\n📊 Current Agent Count: {count}")
            
            if count > 0:
                print("\n[Sample Agents]")
                agents = db.query(Agent).limit(5).all()
                for agent in agents:
                    print(f"- {agent.name} ({agent.category}): {agent.description[:50]}...")
            else:
                print("\nℹ️ No agents found in the database.")
        else:
            print("\n⚠️ 'agents' table does not exist yet.")
            
    except Exception as e:
        print(f"\n❌ Database Query Error: {e}")
        
    finally:
        db.close()

except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Connection Error: {e}")
