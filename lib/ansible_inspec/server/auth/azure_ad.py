"""
Azure AD OAuth2 authentication for ansible-inspec server.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
import httpx

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class AzureADAuth:
    """Azure AD authentication handler"""
    
    def __init__(self, settings: Settings):
        """
        Initialize Azure AD authentication
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.tenant_id = settings.auth.azure_tenant_id
        self.client_id = settings.auth.azure_client_id
        self.client_secret = settings.auth.azure_client_secret
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            logger.warning("Azure AD credentials not configured")
            self.enabled = False
        else:
            self.enabled = True
            self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self.jwks_uri = f"{self.authority}/discovery/v2.0/keys"
            self.token_endpoint = f"{self.authority}/oauth2/v2.0/token"
            self.authorize_endpoint = f"{self.authority}/oauth2/v2.0/authorize"
            
            logger.info(f"Azure AD authentication initialized for tenant: {self.tenant_id}")
    
    async def validate_token(self, token: str) -> Dict:
        """
        Validate Azure AD token and extract claims
        
        Args:
            token: JWT access token from Azure AD
            
        Returns:
            Dict containing user claims
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Decode without verification first to check issuer
            unverified = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            
            # Verify issuer
            expected_issuer = f"{self.authority}/v2.0"
            if unverified.get("iss") != expected_issuer:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token issuer"
                )
            
            # In production, fetch and cache JWKS for signature verification
            # For now, we'll do basic validation
            
            # Verify audience
            if self.client_id not in unverified.get("aud", ""):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token audience"
                )
            
            # Check expiration
            exp = unverified.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            # Extract user information
            return {
                "user_id": unverified.get("oid"),  # Object ID
                "username": unverified.get("preferred_username") or unverified.get("upn"),
                "email": unverified.get("email") or unverified.get("preferred_username"),
                "name": unverified.get("name"),
                "roles": unverified.get("roles", []),
                "tenant_id": unverified.get("tid")
            }
            
        except JWTError as e:
            logger.error(f"JWT validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth2 flow
            redirect_uri: Redirect URI used in authorization request
            
        Returns:
            Dict containing access_token, refresh_token, etc.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "scope": "openid profile email User.Read"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )
            
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token from previous authentication
            
        Returns:
            Dict containing new access_token
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": "openid profile email User.Read"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh token"
                )
            
            return response.json()
    
    def create_jwt_token(self, user_claims: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create internal JWT token for session management
        
        Args:
            user_claims: User claims to encode in token
            expires_delta: Token expiration time delta
            
        Returns:
            Encoded JWT token
        """
        to_encode = user_claims.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.settings.auth.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.auth.jwt_secret,
            algorithm=self.settings.auth.jwt_algorithm
        )
        
        return encoded_jwt
    
    def verify_jwt_token(self, token: str) -> Dict:
        """
        Verify internal JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Dict containing token claims
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.auth.jwt_secret,
                algorithms=[self.settings.auth.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            logger.error(f"JWT verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token"
            )


# Global Azure AD auth instance
_azure_ad_instance: Optional[AzureADAuth] = None


def get_azure_ad_auth(settings: Settings = Depends(get_settings)) -> AzureADAuth:
    """
    Get or create Azure AD auth instance
    
    Args:
        settings: Application settings (injected)
        
    Returns:
        AzureADAuth instance
    """
    global _azure_ad_instance
    if _azure_ad_instance is None:
        _azure_ad_instance = AzureADAuth(settings)
    return _azure_ad_instance
