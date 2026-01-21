"""
Azure AD OAuth2 authentication for ansible-inspec server.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import urlencode
import logging
import httpx
import secrets

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
            
            # JWKS caching for signature verification
            self._jwks_cache: Optional[Dict] = None
            self._jwks_cache_time: Optional[datetime] = None
            self._jwks_cache_ttl = timedelta(hours=24)
            
            logger.info(f"Azure AD authentication initialized for tenant: {self.tenant_id}")
    
    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Build Azure AD authorization URL for OAuth2 flow
        
        Args:
            redirect_uri: Redirect URI after authentication
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Azure AD authentication not configured"
            )
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "openid profile email User.Read",
            "state": state or secrets.token_urlsafe(32),
            "response_mode": "query"
        }
        
        auth_url = f"{self.authorize_endpoint}?{urlencode(params)}"
        logger.debug(f"Generated authorization URL for redirect_uri: {redirect_uri}")
        return auth_url
    
    async def _fetch_jwks(self) -> Dict:
        """
        Fetch JWKS (JSON Web Key Set) from Azure AD for token signature verification
        
        Returns:
            Dict containing JWKS keys
        """
        # Check cache first
        if self._jwks_cache and self._jwks_cache_time:
            if datetime.utcnow() - self._jwks_cache_time < self._jwks_cache_ttl:
                logger.debug("Using cached JWKS")
                return self._jwks_cache
        
        # Fetch new JWKS
        logger.info(f"Fetching JWKS from {self.jwks_uri}")
        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_uri)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch JWKS: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Cannot verify token signature - JWKS unavailable"
                )
            
            jwks = response.json()
            
            # Cache the JWKS
            self._jwks_cache = jwks
            self._jwks_cache_time = datetime.utcnow()
            logger.debug(f"Cached JWKS with {len(jwks.get('keys', []))} keys")
            
            return jwks
    
    async def validate_token(self, token: str) -> Dict:
        """
        Validate Azure AD token with JWKS signature verification and extract claims
        
        Args:
            token: JWT access token from Azure AD
            
        Returns:
            Dict containing user claims
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing key ID (kid)"
                )
            
            # Fetch JWKS and find the matching key
            jwks = await self._fetch_jwks()
            signing_key = None
            
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    signing_key = key
                    break
            
            if not signing_key:
                logger.error(f"No matching key found for kid: {kid}")
                # Invalidate cache and retry once
                self._jwks_cache = None
                jwks = await self._fetch_jwks()
                for key in jwks.get("keys", []):
                    if key.get("kid") == kid:
                        signing_key = key
                        break
                
                if not signing_key:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token signed with unknown key"
                    )
            
            # Verify token signature and decode
            expected_issuer = f"{self.authority}/v2.0"
            
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=expected_issuer,
                options={"verify_signature": True, "verify_aud": True, "verify_iss": True}
            )
            
            # Extract user information
            return {
                "user_id": payload.get("oid"),  # Object ID
                "username": payload.get("preferred_username") or payload.get("upn"),
                "email": payload.get("email") or payload.get("preferred_username"),
                "name": payload.get("name"),
                "roles": payload.get("roles", []),
                "tenant_id": payload.get("tid")
            }
            
        except JWTError as e:
            logger.error(f"JWT validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
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
