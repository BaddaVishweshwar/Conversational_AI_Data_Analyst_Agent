"""
Clerk Authentication Middleware for FastAPI

This middleware verifies Clerk session tokens and extracts user information.
"""

from fastapi import HTTPException, Header
from typing import Optional
from clerk_backend_api import Clerk
from clerk_backend_api.jwks_helpers import authenticate_request
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Clerk client
clerk_client = None
if settings.CLERK_SECRET_KEY:
    clerk_client = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)


async def get_clerk_user(authorization: Optional[str] = Header(None)):
    """
    Verify Clerk session token and return user information.
    
    Args:
        authorization: Bearer token from request header
        
    Returns:
        dict: User information from Clerk
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not clerk_client:
        raise HTTPException(
            status_code=500,
            detail="Clerk authentication not configured"
        )
    
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )
    
    # Verify token with Clerk
    try:
        # Verify the JWT token
        claims = authenticate_request(
            request=None,  # We're manually passing the token
            secret_key=settings.CLERK_SECRET_KEY,
            token=token
        )
        
        if not claims:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        # Get user ID from claims
        user_id = claims.get('sub')
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token claims"
            )
        
        # Fetch full user details from Clerk
        try:
            user = clerk_client.users.get(user_id=user_id)
            
            # Return user information
            return {
                'id': user.id,
                'email': user.email_addresses[0].email_address if user.email_addresses else None,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'clerk_user_id': user.id,
            }
        except Exception as e:
            logger.error(f"Failed to fetch user from Clerk: {e}")
            # Return minimal user info from claims
            return {
                'id': user_id,
                'clerk_user_id': user_id,
                'email': claims.get('email'),
                'username': claims.get('username'),
            }
            
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {str(e)}"
        )


def get_or_create_user(db, clerk_user_info: dict):
    """
    Get or create a local user record synced with Clerk.
    
    Args:
        db: Database session
        clerk_user_info: User information from Clerk
        
    Returns:
        User: Local user model instance
    """
    from ..models import User
    
    clerk_user_id = clerk_user_info['clerk_user_id']
    
    # Try to find existing user by Clerk ID
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if not user:
        # Create new user
        user = User(
            clerk_user_id=clerk_user_id,
            email=clerk_user_info.get('email'),
            username=clerk_user_info.get('username') or clerk_user_info.get('email', '').split('@')[0],
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user from Clerk: {user.email}")
    
    return user
