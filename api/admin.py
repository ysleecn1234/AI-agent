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


def _categorize_operation(op: str) -> str:
    """operation 필드 → 사용자 관점 3개 카테고리 매핑"""
    if not op:
        return "other"
    if op.startswith("llm:chat_") or op == "llm:chat_simple":
        return "ai_chat"
    if op == "llm:doc_chat":
        return "doc_qa"
    if op == "embedding" or op == "llm:tagging" or op == "llm:title_gen":
        return "doc_processing"
    if op.startswith("llm:agent_"):
        return "agent"
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
def get_usage_summary(
    month: str = Query(None, description="조회할 연-월 (YYYY-MM). 지정하지 않으면 이번 달 기준"),
    user_id: str = Depends(get_current_user_id)
):
    """이번 달 (또는 선택된 달) 비용 요약 (카테고리별 + 전월 대비)"""
    from services.ai_drive.db.postgres_client import CostLog

    db = SessionLocal()
    try:
        cur_first, cur_last = _parse_month(month)

        # 전월 계산
        if cur_first.month == 1:
            prev_year, prev_mon = cur_first.year - 1, 12
        else:
            prev_year, prev_mon = cur_first.year, cur_first.month - 1
        prev_first, prev_last = _parse_month(f"{prev_year}-{prev_mon:02d}")

        # 선택한 월 전체 비용/토큰 집계 (실시간 cost_logs 기준)
        cur_summary = (
            db.query(
                func.round(func.sum(CostLog.cost_krw)).label("sum_krw"),
                func.sum(CostLog.cost_usd).label("sum_usd"),
                func.sum(CostLog.tokens_used).label("sum_tokens"),
            )
            .filter(
                cast(CostLog.timestamp, Date) >= cur_first,
                cast(CostLog.timestamp, Date) <= cur_last,
            )
            .first()
        )

        # 이번 달 cost_logs 집계
        cur_rows = (
            db.query(
                CostLog.operation,
                func.round(func.sum(CostLog.cost_krw)).label("sum_krw"),
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

        # 건수 조회 — 카테고리별로 최적 소스 사용
        from services.ai_drive.db.postgres_client import ActivityLog

        # AI 채팅: activity_logs action='chat' (실제 사용자 채팅 메시지 수)
        ai_chat_cnt = (
            db.query(func.count())
            .filter(
                ActivityLog.action == "chat",
                cast(ActivityLog.timestamp, Date) >= cur_first,
                cast(ActivityLog.timestamp, Date) <= cur_last,
            )
            .scalar() or 0
        )

        # AI 에이전트: activity_logs action='create_draft' (또는 관련 액션)
        agent_cnt = (
            db.query(func.count())
            .filter(
                ActivityLog.action == "create_draft",
                cast(ActivityLog.timestamp, Date) >= cur_first,
                cast(ActivityLog.timestamp, Date) <= cur_last,
            )
            .scalar() or 0
        )

        # 문서 Q&A: activity_logs에 doc_chat 미기록 → cost_logs llm:doc_chat 건수로 대체
        # (문서 Q&A 채팅은 activity_logs에 'chat'으로 기록되지 않으므로 ai_chat_cnt와 중복 없음)
        doc_qa_cnt = (
            db.query(func.count())
            .filter(
                CostLog.operation == "llm:doc_chat",
                cast(CostLog.timestamp, Date) >= cur_first,
                cast(CostLog.timestamp, Date) <= cur_last,
            )
            .scalar() or 0
        )

        # 문서 처리: upload + chat_save
        doc_proc_cnt = (
            db.query(func.count())
            .filter(
                ActivityLog.action.in_(["upload", "chat_save"]),
                cast(ActivityLog.timestamp, Date) >= cur_first,
                cast(ActivityLog.timestamp, Date) <= cur_last,
            )
            .scalar() or 0
        )

        activity_counts = {
            "ai_chat": ai_chat_cnt,
            "doc_qa": doc_qa_cnt,
            "doc_processing": doc_proc_cnt,
            "agent": agent_cnt,
        }

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
                func.round(func.sum(CostLog.cost_krw)).label("sum_krw"),
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

        # 인기 모델 TOP 5 (cost_logs 기준, 이번 달)
        CHAT_ANSWER_OPERATIONS = [
            'llm:chat_simple',
            'llm:chat_complex', 
            'llm:chat_bulk',
            'llm:chat_reasoning',
            'llm:premium:GPT_5_2',
            'llm:premium:GEMINI_3_PRO',
            'llm:premium:PERPLEXITY',
            'llm:premium:OPUS_4_6',
        ]
        
        top_models_rows = (
            db.query(
                CostLog.model_name,
                func.round(func.sum(CostLog.cost_krw)).label("sum_krw"),
                func.count().label("usage_count"),
                func.sum(CostLog.tokens_used).label("sum_tokens"),
            )
            .filter(
                cast(CostLog.timestamp, Date) >= cur_first,
                cast(CostLog.timestamp, Date) <= cur_last,
                CostLog.model_name != None,
                CostLog.model_name != "",
                CostLog.operation.in_(CHAT_ANSWER_OPERATIONS)
            )
            .group_by(CostLog.model_name)
            .order_by(func.sum(CostLog.cost_krw).desc())
            .limit(5)
            .all()
        )
        
        top_models = []
        for r in top_models_rows:
            top_models.append({
                "model": r.model_name,
                "cost_krw": float(r.sum_krw or 0),
                "count": r.usage_count,
                "tokens": int(r.sum_tokens or 0)
            })

        return {
            "month": f"{cur_first.year}-{cur_first.month:02d}",
            "total_cost_krw": total_krw_f,
            "total_cost_usd": float(total_usd),
            "total_tokens": total_tokens,
            "monthly_budget_krw": monthly_budget,
            "budget_usage_percent": budget_pct,
            "cost_by_category": cost_by_category,
            "top_models": top_models,
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
                func.round(func.sum(CostLog.cost_krw)).label("sum_krw"),
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

        # cost_logs에서 문서 Q&A 건수 조회 (사용자별)
        doc_chat_rows = (
            db.query(
                CostLog.user_id,
                func.count().label("doc_chat_count"),
            )
            .filter(
                CostLog.operation == "llm:doc_chat",
                cast(CostLog.timestamp, Date) >= first,
                cast(CostLog.timestamp, Date) <= last,
            )
            .group_by(CostLog.user_id)
            .all()
        )
        doc_chat_map = {str(r.user_id): r.doc_chat_count for r in doc_chat_rows}

        users = []
        seen_uids = set()
        for row in cost_rows:
            uid = str(row.user_id)
            seen_uids.add(uid)
            users.append({
                "user_id": uid,
                "user_name": row.user_name or "알 수 없음",
                "total_cost_krw": float(row.sum_krw or 0),
                "total_tokens": int(row.sum_tokens or 0),
                "chat_count": chat_map.get(uid, 0),
                "doc_chat_count": doc_chat_map.get(uid, 0),
            })

        # 비용 내림차순 정렬
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
                func.round(func.sum(CostLog.cost_krw)).label("sum_krw"),
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
