from datetime import timedelta
from application.auth import ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from application.database import get_db
from application.database import User, InvitationCode
from application.auth import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

# 1. Pydantic Models for Request Body
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    department: str
    invitation_code: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    user_name: str
    department: str

# 2. Endpoints
@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # [1] 초대 코드 검증
    invite = db.query(InvitationCode).filter(InvitationCode.code == user.invitation_code).first()
    if not invite:
        raise HTTPException(status_code=400, detail="유효하지 않은 초대 코드입니다.")
    if invite.is_used:
        raise HTTPException(status_code=400, detail="이미 사용된 초대 코드입니다.")

    # [2] Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # [3] 초대 코드 소모 표시
    invite.is_used = True
    invite.used_at = datetime.utcnow()

    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        name=user.name,
        department=user.department,
        memory={} # Initialize empty memory
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate Token
    access_token = create_access_token(
        data={"sub": new_user.email, "user_id": str(new_user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": str(new_user.id),
        "user_name": new_user.name,
        "department": new_user.department,
        "user_id": str(new_user.id) # [New] Check 1
    }

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    # Find User
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify Password
    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate Token
    access_token = create_access_token(
        data={"sub": db_user.email, "user_id": str(db_user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": str(db_user.id),
        "user_name": db_user.name,
        "department": db_user.department,
        "user_id": str(db_user.id) # [New] Check 2
    }
