from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from ..models import User
from ..config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    print(f"DEBUG AUTH: Authenticating {email}")
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"DEBUG AUTH: User {email} NOT found in DB")
            return None
        
        print(f"DEBUG AUTH: User found. ID: {user.id}, Hash len: {len(user.hashed_password) if user.hashed_password else 0}")
        is_valid = verify_password(password, user.hashed_password)
        print(f"DEBUG AUTH: Password valid? {is_valid}")
        
        if not is_valid:
            return None
        return user
    except Exception as e:
        print(f"DEBUG AUTH: Error: {e}")
        raise e


def create_user(db: Session, email: str, username: str, password: str) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
