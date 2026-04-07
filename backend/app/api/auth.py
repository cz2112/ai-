from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.email_service import send_verification_email, send_reset_password_email

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# 临时简化：直接比较密码（仅用于测试）
def verify_password(plain_password, hashed_password):
    return plain_password == hashed_password

def get_password_hash(password):
    return password  # 直接返回原密码

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# ==================== 注册接口 ====================
@router.post("/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(400, "用户名已存在")
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(400, "邮箱已被注册")
    
    # 创建新用户
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_admin=False,
        is_active=True,
        is_verified=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 发送验证邮件
    try:
        await send_verification_email(user.email, user.id, SECRET_KEY)
    except Exception as e:
        print(f"发送邮件失败: {e}")
    
    return {"message": "注册成功！验证邮件已发送到您的邮箱，请查收验证。"}

# ==================== 登录接口 ====================
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 查找用户（支持用户名或邮箱登录）
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查账号是否激活
    if not user.is_active:
        raise HTTPException(400, "账号已被禁用")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# ==================== 获取当前用户信息 ====================
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ==================== 邮箱验证接口 ====================
@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """验证邮箱接口 - 用户点击邮件中的链接后调用"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(400, "无效的验证链接")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, "用户不存在")
        
        if user.is_verified:
            return {"message": "邮箱已验证过，无需重复验证"}
        
        user.is_verified = True
        db.commit()
        
        return {"message": "✅ 邮箱验证成功！现在可以正常使用所有功能了"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(400, "验证链接已过期，请重新注册")
    except JWTError:
        raise HTTPException(400, "无效的验证链接")

# ==================== 忘记密码 - 发送重置邮件 ====================
@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    """忘记密码：发送密码重置邮件"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return {"message": "如果该邮箱已注册，我们会发送重置链接"}
    
    try:
        await send_reset_password_email(user.email, user.id, SECRET_KEY)
    except Exception as e:
        print(f"发送邮件失败: {e}")
        return {"message": "发送失败，请稍后重试"}
    
    return {"message": "重置链接已发送到您的邮箱"}

# ==================== 重置密码 ====================
@router.post("/reset-password")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """使用 token 重置密码"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(400, "无效的重置链接")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, "用户不存在")
        
        # 更新密码
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        
        return {"message": "✅ 密码重置成功！请使用新密码登录"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(400, "重置链接已过期（1小时有效），请重新申请")
    except JWTError:
        raise HTTPException(400, "无效的重置链接")