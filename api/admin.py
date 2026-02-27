"""
Admin Usage Statistics API Router
사용 통계 및 한도 관리 — 읽기 전용 집계 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from application.database import SessionLocal, User, UserSettings
from application.auth import decode_access_token
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, cast, Date
from datetime import datetime, date
from calendar import monthrange
from decimal import Decimal
import uuid

router = APIRouter(prefix="/admin", tags=["Admin"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

MONTHLY_BUDGET_DEFAULT = 1_000_000  # 기본 월 예산 (KRW)


def get_current_user_id(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return payload.get("user_id")


def _categorize_operation(operation: str) -> str:
    """operation 필드 → 사용자 관점 3개 카테고리 매핑"""
    op = operation or ""
    # AI 채팅: chat 관련 LLM 호출 전체
    if op.startswith("llm:chat"):
        return "ai_chat"
    # 문서 Q&A: 문서 채팅
    elif op == "llm:doc_chat":
        return "doc_qa"
    # 문서 처리: 임베딩 + 태깅 + 제목생성 + 스토리지
    elif op in ("embedding", "storage", "llm:tagging", "llm:title_gen", "llm:doc_format"):
        return "doc_processing"
    else:
        return "other"


def _parse_month(month_str: str | None) -> tuple[date, date]:
    """
    'YYYY-MM' 문자열을 파싱하여 (첫날, 말일)을 반환.
    None이면 현재 달 사용.
    """
    if month_str:
        try:
            year, mon = map(int, month_str.split("-"))
        except (ValueError, AttributeError):
            raise HTTPException(400, "month 형식은 YYYY-MM이어야 합니다")
    else:
        today = date.today()
        year, mon = today.year, today.month

    first = date(year, mon, 1)
    last = date(year, mon, monthrange(year, mon)[1])
    return first, last


def _get_monthly_budget(db, user_id: str) -> int:
    """사용자의 월 예산 한도를 DB에서 조회 (없으면 기본값)"""
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()
        if settings and settings.monthly_budget is not None:
            return settings.monthly_budget
    except Exception:
        pass
    return MONTHLY_BUDGET_DEFAULT


# ==================== 1. 이번 달 비용 요약 ====================

@router.get("/usage/summary")
def get_usage_summary(user_id: str = Depends(get_current_user_id)):
    """이번 달 비용 요약 (카테고리별 + 전월 대비)"""
    from services.ai_drive.db.postgres_client import CostLog

    db = SessionLocal()
    try:
        today = date.today()
        cur_first, cur_last = _parse_month(f"{today.year}-{today.month:02d}")

        # 전월 계산
        if today.month == 1:
            prev_year, prev_mon = today.year - 1, 12
        else:
            prev_year, prev_mon = today.year, today.month - 1
        prev_first, prev_last = _parse_month(f"{prev_year}-{prev_mon:02d}")

        # 이번 달 cost_logs 집계
        cur_rows = (
            db.query(
                CostLog.operation,
                func.sum(CostLog.cost_krw).label("sum_krw"),
                func.sum(CostLog.cost_usd).label("sum_usd"),
                func.sum(CostLog.tokens_used).label("sum_tokens"),
            )
            .filter(
                cast(CostLog.timestamp, Date) >= cur_first,
                cast(CostLog.timestamp, Date) <= cur_last,
            )
            .group_by(CostLog.operation)
            .all()
        )

        # 카테고리별 비용 집계 (cost_logs 기준)
        cost_by_category: dict = {}
        total_krw = Decimal("0")
        total_usd = Decimal("0")
        total_tokens = 0

        for row in cur_rows:
            cat = _categorize_operation(row.operation)
            if cat not in cost_by_category:
                cost_by_category[cat] = {"cost_krw": Decimal("0")}
            cost_by_category[cat]["cost_krw"] += row.sum_krw or Decimal("0")
            total_krw += row.sum_krw or Decimal("0")
            total_usd += row.sum_usd or Decimal("0")
            total_tokens += row.sum_tokens or 0

        for cat in cost_by_category:
            cost_by_category[cat]["cost_krw"] = float(cost_by_category[cat]["cost_krw"])

        # activity_logs 기반 건수 조회 (사용자 행위 기준)
        from services.ai_drive.db.postgres_client import ActivityLog
        activity_counts_raw = (
            db.query(
                ActivityLog.action,
                func.count().label("cnt"),
            )
            .filter(
                ActivityLog.action.in_(["chat", "doc_chat", "upload"]),
                cast(ActivityLog.timestamp, Date) >= cur_first,
                cast(ActivityLog.timestamp, Date) <= cur_last,
            )
            .group_by(ActivityLog.action)
            .all()
        )
        action_to_cat = {"chat": "ai_chat", "doc_chat": "doc_qa", "upload": "doc_processing"}
        activity_counts: dict = {"ai_chat": 0, "doc_qa": 0, "doc_processing": 0}
        for row in activity_counts_raw:
            cat_key = action_to_cat.get(row.action)
            if cat_key:
                activity_counts[cat_key] = row.cnt

        # activity_count를 cost_by_category에 병합
        for cat in cost_by_category:
            cost_by_category[cat]["activity_count"] = activity_counts.get(cat, 0)
        # cost_by_category에 없는 카테고리도 activity_count가 있으면 추가
        for cat, cnt in activity_counts.items():
            if cat not in cost_by_category and cnt > 0:
                cost_by_category[cat] = {"cost_krw": 0.0, "activity_count": cnt}

        # 전월 집계
        prev_rows = (
            db.query(
                func.sum(CostLog.cost_krw).label("sum_krw"),
                func.sum(CostLog.tokens_used).label("sum_tokens"),
            )
            .filter(
                cast(CostLog.timestamp, Date) >= prev_first,
                cast(CostLog.timestamp, Date) <= prev_last,
            )
            .first()
        )
        prev_krw = float(prev_rows.sum_krw or 0)
        prev_tokens = int(prev_rows.sum_tokens or 0)

        total_krw_f = float(total_krw)
        cost_change = round(((total_krw_f - prev_krw) / prev_krw * 100), 1) if prev_krw > 0 else 0.0
        token_change = round(((total_tokens - prev_tokens) / prev_tokens * 100), 1) if prev_tokens > 0 else 0.0

        monthly_budget = _get_monthly_budget(db, user_id)
        budget_pct = round(total_krw_f / monthly_budget * 100, 1) if monthly_budget > 0 else 0.0

        return {
            "month": f"{today.year}-{today.month:02d}",
            "total_cost_krw": total_krw_f,
            "total_cost_usd": float(total_usd),
            "total_tokens": total_tokens,
            "monthly_budget_krw": monthly_budget,
            "budget_usage_percent": budget_pct,
            "cost_by_category": cost_by_category,
            "vs_last_month": {
                "cost_change_percent": cost_change,
                "token_change_percent": token_change,
            },
        }
    finally:
        db.close()


# ==================== 2. 일별 비용 추이 ====================

@router.get("/usage/daily")
def get_usage_daily(
    month: str = Query(None, description="YYYY-MM"),
    user_id: str = Depends(get_current_user_id),
):
    """일별 비용/토큰 추이 (빈 날짜는 0으로 채움)"""
    from services.ai_drive.db.postgres_client import CostLog

    db = SessionLocal()
    try:
        first, last = _parse_month(month)

        rows = (
            db.query(
                cast(CostLog.timestamp, Date).label("day"),
                func.sum(CostLog.cost_krw).label("sum_krw"),
                func.sum(CostLog.tokens_used).label("sum_tokens"),
            )
            .filter(
                cast(CostLog.timestamp, Date) >= first,
                cast(CostLog.timestamp, Date) <= last,
            )
            .group_by(cast(CostLog.timestamp, Date))
            .order_by(cast(CostLog.timestamp, Date))
            .all()
        )

        day_map = {row.day: row for row in rows}
        daily = []
        d = first
        from datetime import timedelta
        while d <= last:
            row = day_map.get(d)
            daily.append({
                "date": d.isoformat(),
                "cost_krw": float(row.sum_krw) if row and row.sum_krw else 0,
                "tokens": int(row.sum_tokens) if row and row.sum_tokens else 0,
            })
            d += timedelta(days=1)

        return {
            "month": f"{first.year}-{first.month:02d}",
            "daily": daily,
        }
    finally:
        db.close()


# ==================== 3. 사용자별 비용 집계 ====================

@router.get("/usage/by-user")
def get_usage_by_user(
    month: str = Query(None, description="YYYY-MM"),
    user_id: str = Depends(get_current_user_id),
):
    """사용자별 비용/토큰/채팅횟수 집계"""
    from services.ai_drive.db.postgres_client import CostLog, ActivityLog

    db = SessionLocal()
    try:
        first, last = _parse_month(month)

        # cost_logs 집계 + users JOIN
        cost_rows = (
            db.query(
                CostLog.user_id,
                User.name.label("user_name"),
                func.sum(CostLog.cost_krw).label("sum_krw"),
                func.sum(CostLog.tokens_used).label("sum_tokens"),
            )
            .outerjoin(User, CostLog.user_id == User.id)
            .filter(
                cast(CostLog.timestamp, Date) >= first,
                cast(CostLog.timestamp, Date) <= last,
            )
            .group_by(CostLog.user_id, User.name)
            .all()
        )

        # activity_logs에서 chat 건수 조회
        chat_rows = (
            db.query(
                ActivityLog.user_id,
                func.count().label("chat_count"),
            )
            .filter(
                ActivityLog.action == "chat",
                cast(ActivityLog.timestamp, Date) >= first,
                cast(ActivityLog.timestamp, Date) <= last,
            )
            .group_by(ActivityLog.user_id)
            .all()
        )
        chat_map = {str(r.user_id): r.chat_count for r in chat_rows}

        users = []
        for row in cost_rows:
            uid = str(row.user_id)
            users.append({
                "user_id": uid,
                "user_name": row.user_name or "알 수 없음",
                "total_cost_krw": float(row.sum_krw or 0),
                "total_tokens": int(row.sum_tokens or 0),
                "chat_count": chat_map.get(uid, 0),
            })

        # 비용 순 정렬
        users.sort(key=lambda x: x["total_cost_krw"], reverse=True)

        return {"users": users}
    finally:
        db.close()


# ==================== 4. 부서별 비용 집계 ====================

@router.get("/usage/by-department")
def get_usage_by_department(
    month: str = Query(None, description="YYYY-MM"),
    user_id: str = Depends(get_current_user_id),
):
    """부서별 비용/토큰/사용자 수 집계 — cost_logs JOIN users로 department 획득"""
    from services.ai_drive.db.postgres_client import CostLog

    db = SessionLocal()
    try:
        first, last = _parse_month(month)

        rows = (
            db.query(
                User.department,
                func.sum(CostLog.cost_krw).label("sum_krw"),
                func.sum(CostLog.tokens_used).label("sum_tokens"),
                func.count(func.distinct(CostLog.user_id)).label("user_count"),
            )
            .join(User, CostLog.user_id == User.id)
            .filter(
                cast(CostLog.timestamp, Date) >= first,
                cast(CostLog.timestamp, Date) <= last,
            )
            .group_by(User.department)
            .all()
        )

        departments = []
        for row in rows:
            departments.append({
                "department": row.department or "미지정",
                "total_cost_krw": float(row.sum_krw or 0),
                "total_tokens": int(row.sum_tokens or 0),
                "user_count": row.user_count or 0,
            })

        departments.sort(key=lambda x: x["total_cost_krw"], reverse=True)

        return {"departments": departments}
    finally:
        db.close()
