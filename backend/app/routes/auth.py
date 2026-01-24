from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..database import get_db
from ..models import User
from ..services.auth_service import (
    authenticate_user,
    create_user,
    create_access_token,
    create_refresh_token,
    verify_token
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Pydantic schemas
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class GoogleLoginRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    is_super_admin: bool
    totp_enabled: bool
    
    class Config:
        from_attributes = True


# Dependency to get current user
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    payload = verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
    # Create user
    user = create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password
    )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = authenticate_user(db, user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_token(data: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token"""
    payload = verify_token(data.refresh_token, "refresh")
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    
    # Generate new tokens
    access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


# Password Reset Endpoints

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset email"""
    from ..models import PasswordResetToken
    from ..services.email_service import email_service
    import uuid
    from datetime import datetime, timedelta
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Delete any existing unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False
    ).delete()
    
    # Create new token
    token_record = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at
    )
    db.add(token_record)
    db.commit()
    
    # Send email
    email_sent = email_service.send_password_reset_email(user.email, reset_token)
    
    if not email_sent:
        raise HTTPException(
            status_code=500,
            detail="Failed to send reset email. Please check email configuration."
        )
    
    return {"message": "If the email exists, a reset link has been sent"}


@router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str, db: Session = Depends(get_db)):
    """Verify if reset token is valid"""
    from ..models import PasswordResetToken
    from datetime import datetime
    
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    return {"valid": token_record is not None}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token"""
    from ..models import PasswordResetToken
    from datetime import datetime
    import bcrypt
    
    # Find valid token
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not token_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash new password
    hashed_password = bcrypt.hashpw(
        request.new_password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    # Update password
    user.hashed_password = hashed_password
    
    # Mark token as used
    token_record.used = True
    
    db.commit()
    
    return {"message": "Password reset successful"}


@router.post("/google", response_model=Token)
async def google_login(data: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Login or register via Google OAuth"""
    from google.oauth2 import id_token
    from google.auth.transport import requests
    from ..config import settings
    from ..services.auth_service import create_user
    import secrets
    
    try:
        # Verify the ID token
        idinfo = id_token.verify_oauth2_token(
            data.id_token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID if hasattr(settings, 'GOOGLE_CLIENT_ID') else None
        )

        email = idinfo['email']
        username = idinfo.get('name', email.split('@')[0])
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create user if it doesn't exist (random password since they'll use Google)
            user = create_user(
                db=db,
                email=email,
                username=username,
                password=secrets.token_urlsafe(32)
            )
        
        # Generate tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except ValueError as ve:
        # Invalid token
        print(f"❌ Google Auth Value Error: {ve}")
        raise HTTPException(status_code=401, detail=f"Invalid Google Token: {str(ve)}")
    except Exception as e:
        import traceback
        print(f"❌ Google Auth Internal Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Auth Error: {str(e)}")

