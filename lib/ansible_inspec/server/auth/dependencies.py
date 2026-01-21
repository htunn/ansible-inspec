"""
FastAPI authentication dependencies for ansible-inspec server.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
import logging

from .azure_ad import AzureADAuth, get_azure_ad_auth
from ..config import Settings, get_settings
from ..models import User

logger = logging.getLogger(__name__)


# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AzureADAuth = Depends(get_azure_ad_auth),
    settings: Settings = Depends(get_settings)
) -> Dict:
    """
    FastAPI dependency to get current authenticated user
    
    Checks for token in:
    1. Authorization header (Bearer token)
    2. HTTP-only cookie
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        auth_service: Azure AD auth service
        settings: Application settings
        
    Returns:
        Dict containing user information
        
    Raises:
        HTTPException: If authentication fails or is not configured
    """
    # If authentication is disabled, return mock user
    if not settings.auth.enabled:
        logger.debug("Authentication disabled, using mock user")
        return {
            "user_id": "mock-user",
            "username": "anonymous",
            "name": "Anonymous User",
            "roles": ["admin"]  # Full access when auth disabled
        }
    
    # Try to get token from Authorization header first
    token = None
    if credentials:
        token = credentials.credentials
    
    # If no token in header, check cookie
    if not token:
        token = request.cookies.get(settings.auth.cookie_name)
    
    # Require token when auth is enabled
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify internal JWT session token
    try:
        user_info = auth_service.verify_jwt_token(token)
        logger.debug(f"Authenticated user: {user_info.get('username')}")
        return user_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Get current active user (can be extended to check user status in DB)
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Dict containing user information
    """
    # In future, check if user is active in database
    return current_user


def require_role(required_role: str):
    """
    Dependency factory to require specific role
    
    Args:
        required_role: Role required to access endpoint
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: Dict = Depends(get_current_user)) -> Dict:
        """Check if user has required role"""
        user_roles = current_user.get("roles", [])
        
        # Admin role has access to everything
        if "admin" in user_roles:
            return current_user
        
        # Check for required role
        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        
        return current_user
    
    return role_checker


# Pre-defined role dependencies
require_admin = require_role("admin")
require_operator = require_role("operator")
require_viewer = require_role("viewer")
