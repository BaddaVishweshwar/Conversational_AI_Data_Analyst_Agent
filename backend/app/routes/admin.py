"""
Admin Routes - Secure admin panel with Google 2FA

Provides endpoints for:
- Admin authentication with 2FA
- User management
- Admin access granting/revoking
- Audit logging
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from sqlalchemy import or_, desc
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import pyotp
import qrcode
import io
import base64
from fastapi.responses import JSONResponse

from ..database import get_db
from ..models import User, AdminAuditLog
from ..routes.auth import get_current_user
from ..services.auth_service import get_password_hash, verify_password

router = APIRouter(prefix="/admin", tags=["Admin"])


# Pydantic schemas
class TwoFactorSetupResponse(BaseModel):
    qr_code: str  # Base64 encoded QR code image
    secret: str
    
class TwoFactorVerifyRequest(BaseModel):
    token: str
    
class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_token: str
    
class GrantAdminRequest(BaseModel):
    user_id: int
    email: EmailStr  # For confirmation
    password: str  # Admin's password
    totp_token: str  # Admin's 2FA token
    
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_admin: bool
    is_super_admin: bool
    totp_enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    admin_user_id: int
    action: str
    target_user_id: Optional[int]
    details: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaginatedUsersResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    pages: int

class PaginatedLogsResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    pages: int


def require_admin(current_user: User = Depends(get_current_user)):
    """Middleware to require admin access"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_2fa(current_user: User = Depends(require_admin)):
    """Middleware to require 2FA enabled"""
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA must be enabled for admin access"
        )
    return current_user


def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"


def log_admin_action(
    db: Session,
    admin_user_id: int,
    action: str,
    ip_address: str,
    target_user_id: Optional[int] = None,
    details: Optional[dict] = None
):
    """Log an admin action"""
    log = AdminAuditLog(
        admin_user_id=admin_user_id,
        action=action,
        target_user_id=target_user_id,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()


@router.post("/setup-2fa", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Generate QR code for Google Authenticator setup
    """
    # Generate TOTP secret
    secret = pyotp.random_base32()
    
    # Create TOTP URI for QR code
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name="Business Analytics AI"
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Store secret (not enabled yet)
    current_user.totp_secret = secret
    db.commit()
    
    return TwoFactorSetupResponse(
        qr_code=f"data:image/png;base64,{qr_code_base64}",
        secret=secret
    )


@router.post("/verify-2fa")
async def verify_2fa(
    request: TwoFactorVerifyRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Verify 2FA token and enable 2FA
    """
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not set up. Call /setup-2fa first"
        )
    
    # Verify token
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token"
        )
    
    # Enable 2FA
    current_user.totp_enabled = True
    db.commit()
    
    return {"message": "2FA enabled successfully"}


@router.post("/login")
async def admin_login(
    request: AdminLoginRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Admin login with email, password, and 2FA token
    """
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if admin
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify 2FA
    if not user.totp_enabled or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA not enabled. Please set up 2FA first"
        )
    
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(request.totp_token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA token"
        )
    
    # Log admin login
    log_admin_action(
        db=db,
        admin_user_id=user.id,
        action="admin_login",
        ip_address=get_client_ip(req)
    )
    
    # Generate session token (reuse existing auth logic)
    from ..routes.auth import create_access_token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@router.get("/users", response_model=PaginatedUsersResponse)
async def list_users(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    current_user: User = Depends(require_2fa),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only) with pagination and search
    """
    query = db.query(User)
    
    # Filter by search term
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.email.ilike(search_term),
                User.username.ilike(search_term)
            )
        )
    
    # Calculate totals
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    return {
        "items": users,
        "total": total,
        "page": (skip // limit) + 1,
        "pages": (total + limit - 1) // limit if limit > 0 else 0
    }


@router.post("/grant-admin")
async def grant_admin(
    request: GrantAdminRequest,
    req: Request,
    current_user: User = Depends(require_2fa),
    db: Session = Depends(get_db)
):
    """
    Grant admin access to a user (requires 2FA verification)
    """
    # Only super admin can grant admin access
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can grant admin access"
        )
    
    # Verify admin's password
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Verify admin's 2FA
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.totp_token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA token"
        )
    
    # Find target user
    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify email matches
    if target_user.email != request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email does not match user"
        )
    
    # Grant admin access
    target_user.is_admin = True
    db.commit()
    
    # Log action
    log_admin_action(
        db=db,
        admin_user_id=current_user.id,
        action="grant_admin",
        target_user_id=target_user.id,
        ip_address=get_client_ip(req),
        details={"target_email": target_user.email}
    )
    
    return {
        "message": f"Admin access granted to {target_user.email}",
        "user": UserResponse.from_orm(target_user)
    }


@router.post("/revoke-admin")
async def revoke_admin(
    request: GrantAdminRequest,  # Reuse same schema
    req: Request,
    current_user: User = Depends(require_2fa),
    db: Session = Depends(get_db)
):
    """
    Revoke admin access from a user (requires 2FA verification)
    """
    # Only super admin can revoke admin access
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can revoke admin access"
        )
    
    # Verify admin's password
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Verify admin's 2FA
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.totp_token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA token"
        )
    
    # Find target user
    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot revoke super admin
    if target_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke super admin access"
        )
    
    # Revoke admin access
    target_user.is_admin = False
    target_user.totp_enabled = False
    target_user.totp_secret = None
    db.commit()
    
    # Log action
    log_admin_action(
        db=db,
        admin_user_id=current_user.id,
        action="revoke_admin",
        target_user_id=target_user.id,
        ip_address=get_client_ip(req),
        details={"target_email": target_user.email}
    )
    
    return {
        "message": f"Admin access revoked from {target_user.email}",
        "user": UserResponse.from_orm(target_user)
    }



@router.post("/verify-totp")
async def verify_totp(
    request: TwoFactorVerifyRequest,
    current_user: User = Depends(require_admin),
):
    """
    Verify TOTP token without enabling/disabling (for session checks)
    """
    if not current_user.totp_enabled or not current_user.totp_secret:
         raise HTTPException(status_code=400, detail="2FA not enabled")
         
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA token"
        )
        
    return {"valid": True}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    req: Request,
    current_user: User = Depends(require_2fa),
    db: Session = Depends(get_db)
):
    """
    Delete a user (super admin only)
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can delete users"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.is_super_admin:
         raise HTTPException(status_code=400, detail="Cannot delete super admin")
         
    # Log before delete
    log_admin_action(
        db=db,
        admin_user_id=current_user.id,
        action="delete_user",
        target_user_id=user.id, # This will be set to NULL via update below, or we should log it as None?
                               # Actually, if we log it now, target_user_id will be user.id.
                               # Then we run update() to set target_user_id=None.
                               # It's better to log details only.
        ip_address=get_client_ip(req),
        details={"deleted_email": user.email, "deleted_user_id": user.id}
    )
    
    # Handle DB Constraints before deletion:
    # 1. Nullify target_user_id in AdminAuditLogs where this user was the target
    db.query(AdminAuditLog).filter(AdminAuditLog.target_user_id == user.id).update({AdminAuditLog.target_user_id: None})
    
    # 2. Delete AdminAuditLogs where this user was the admin (since admin_user_id is not nullable)
    db.query(AdminAuditLog).filter(AdminAuditLog.admin_user_id == user.id).delete()
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/audit-logs", response_model=PaginatedLogsResponse)
async def get_audit_logs(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    current_user: User = Depends(require_2fa),
    db: Session = Depends(get_db)
):
    query = db.query(AdminAuditLog)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                AdminAuditLog.action.ilike(search_term),
                AdminAuditLog.details.ilike(search_term)
            )
        )

    # Order by recent first
    query = query.order_by(desc(AdminAuditLog.created_at))

    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return {
        "items": logs,
        "total": total,
        "page": (skip // limit) + 1,
        "pages": (total + limit - 1) // limit if limit > 0 else 0
    }

