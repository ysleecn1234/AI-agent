"""
Settings API Router
사용자 개인정보 보호 설정 조회/수정
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict

from application.database import SessionLocal, UserSettings
from application.auth import decode_access_token
from fastapi.security import OAuth2PasswordBearer

# 인증 의존성
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("user_id")


# ==================== Pydantic 모델 ====================

class DetectionItems(BaseModel):
    ssn: bool = True
    phone: bool = True
    email: bool = True
    creditCard: bool = True
    account: bool = True
    address: bool = True

class PrivacySettings(BaseModel):
    mode: str = "block"  # block / mask
    detectionItems: DetectionItems = DetectionItems()

class AccountInfo(BaseModel):
    name: str = ""
    email: str = ""
    department: str = ""

class SettingsRequest(BaseModel):
    privacy: PrivacySettings = PrivacySettings()
    account: Optional[AccountInfo] = None

class SettingsResponse(BaseModel):
    privacy: PrivacySettings
    account: AccountInfo


# ==================== 라우터 설정 ====================

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
)

DEFAULT_DETECTION = {
    "ssn": True,
    "phone": True,
    "email": True,
    "creditCard": True,
    "account": True,
    "address": True,
}


@router.get("")
async def get_settings(user_id: str = Depends(get_current_user_id)):
    """사용자 설정 조회"""
    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        if settings:
            privacy = PrivacySettings(
                mode=settings.privacy_mode,
                detectionItems=DetectionItems(**(settings.detection_items or DEFAULT_DETECTION))
            )
        else:
            # 설정이 없으면 기본값 반환
            privacy = PrivacySettings()

        # 계정 정보는 User 테이블에서 조회
        from application.database import User
        user = db.query(User).filter(User.id == user_id).first()
        account = AccountInfo(
            name=user.name if user else "",
            email=user.email if user else "",
            department=user.department if user else "",
        )

        return {
            "privacy": privacy.model_dump(),
            "account": account.model_dump(),
        }
    finally:
        db.close()


@router.put("")
async def update_settings(request: SettingsRequest, user_id: str = Depends(get_current_user_id)):
    """사용자 설정 저장"""
    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()

        detection_dict = request.privacy.detectionItems.model_dump()

        if settings:
            # 기존 설정 업데이트
            settings.privacy_mode = request.privacy.mode
            settings.detection_items = detection_dict
        else:
            # 새 설정 생성
            settings = UserSettings(
                user_id=user_id,
                privacy_mode=request.privacy.mode,
                detection_items=detection_dict,
            )
            db.add(settings)

        db.commit()
        return {"success": True, "message": "설정이 저장되었습니다"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"설정 저장 실패: {str(e)}")
    finally:
        db.close()
