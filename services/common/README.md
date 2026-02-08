# 서비스 공통 모듈 (Common Services)

이 디렉토리는 여러 마이크로서비스(Hub, Drive, Orchestrator)에서 공통으로 사용되는 코드를 관리합니다.

## 구조
- `db/`: 데이터베이스 관련 공통 코드 (Schema Mixin 등)
- `utils/`: 유틸리티 함수 (현재 비어있음)

## 사용법
### DB 모델 Mixin 사용법
`services/common/db/models.py`에 정의된 Mixin 클래스를 상속받아 각 서비스의 DB 모델을 정의합니다.

```python
from application.database import Base
from services.common.db.models import CostLogMixin

class CostLog(Base, CostLogMixin):
    __tablename__ = "cost_logs"
    # 추가 컬럼이나 오버라이딩 가능
```

### 장점
1. **스키마 통일**: 모든 서비스가 동일한 이름과 타입의 로그 컬럼을 가집니다.
2. **DB 분리 유지**: 각 서비스는 자신의 `Base`와 DB 연결을 그대로 사용합니다.
3. **확장성**: 공통 변경 사항은 Mixin만 수정하면 모든 서비스에 반영됩니다.
