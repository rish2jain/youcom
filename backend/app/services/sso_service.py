"""
SSO Service - Week 1 Implementation
Google, Azure AD, and Okta SSO authentication for enterprise users.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
import secrets
import base64

import httpx
from jose import jwt, JWTError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import settings
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.auth import UserCreate, UserResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

class SSOError(Exception):
    """SSO authentication error"""
    def __init__(self, message: str, provider: str = None, error_code: str = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code

class GoogleSSOProvider:
    """Google OAuth2 SSO provider"""
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        
        # Google OAuth2 endpoints
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning("Google SSO not configured - missing credentials")
    
    def get_authorization_url(self, state: str) -> str:
        """Generate Google OAuth2 authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"Google token exchange failed: {e.response.text}")
                raise SSOError(
                    "Failed to exchange code for token",
                    provider="google",
                    error_code="token_exchange_failed"
                )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.userinfo_url, headers=headers)
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"Google userinfo failed: {e.response.text}")
                raise SSOError(
                    "Failed to get user information",
                    provider="google",
                    error_code="userinfo_failed"
                )

class AzureADSSOProvider:
    """Azure AD OAuth2/SAML SSO provider"""
    
    def __init__(self):
        self.client_id = settings.azure_client_id
        self.client_secret = settings.azure_client_secret
        self.tenant_id = settings.azure_tenant_id
        self.redirect_uri = settings.azure_redirect_uri
        
        # Azure AD endpoints
        self.auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.userinfo_url = "https://graph.microsoft.com/v1.0/me"
        
        if not all([self.client_id, self.client_secret, self.tenant_id, self.redirect_uri]):
            logger.warning("Azure AD SSO not configured - missing credentials")
    
    def get_authorization_url(self, state: str) -> str:
        """Generate Azure AD OAuth2 authorization URL"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "response_mode": "query",
            "scope": "openid profile email User.Read",
            "state": state
        }
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"Azure AD token exchange failed: {e.response.text}")
                raise SSOError(
                    "Failed to exchange code for token",
                    provider="azure",
                    error_code="token_exchange_failed"
                )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.userinfo_url, headers=headers)
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"Azure AD userinfo failed: {e.response.text}")
                raise SSOError(
                    "Failed to get user information",
                    provider="azure",
                    error_code="userinfo_failed"
                )

class OktaSSOProvider:
    """Okta OAuth2/SAML SSO provider"""
    
    def __init__(self):
        self.client_id = settings.okta_client_id
        self.client_secret = settings.okta_client_secret
        self.domain = settings.okta_domain
        self.redirect_uri = settings.okta_redirect_uri
        
        # Okta endpoints
        self.auth_url = f"https://{self.domain}/oauth2/default/v1/authorize"
        self.token_url = f"https://{self.domain}/oauth2/default/v1/token"
        self.userinfo_url = f"https://{self.domain}/oauth2/default/v1/userinfo"
        
        if not all([self.client_id, self.client_secret, self.domain, self.redirect_uri]):
            logger.warning("Okta SSO not configured - missing credentials")
    
    def get_authorization_url(self, state: str) -> str:
        """Generate Okta OAuth2 authorization URL"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "openid profile email",
            "redirect_uri": self.redirect_uri,
            "state": state
        }
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"Okta token exchange failed: {e.response.text}")
                raise SSOError(
                    "Failed to exchange code for token",
                    provider="okta",
                    error_code="token_exchange_failed"
                )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Okta"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.userinfo_url, headers=headers)
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"Okta userinfo failed: {e.response.text}")
                raise SSOError(
                    "Failed to get user information",
                    provider="okta",
                    error_code="userinfo_failed"
                )

class SSOService:
    """Main SSO service orchestrating all providers"""
    
    def __init__(self):
        self.providers = {
            "google": GoogleSSOProvider(),
            "azure": AzureADSSOProvider(),
            "okta": OktaSSOProvider()
        }
        
        self.auth_service = AuthService()
        
        # State storage for OAuth2 flows (in production, use Redis)
        self.state_storage = {}
    
    def get_available_providers(self) -> List[str]:
        """Get list of configured SSO providers"""
        available = []
        
        for name, provider in self.providers.items():
            # Check if provider is configured
            if name == "google" and hasattr(provider, 'client_id') and provider.client_id:
                available.append(name)
            elif name == "azure" and hasattr(provider, 'client_id') and provider.client_id:
                available.append(name)
            elif name == "okta" and hasattr(provider, 'client_id') and provider.client_id:
                available.append(name)
        
        return available
    
    def generate_sso_url(self, provider: str, workspace_id: Optional[str] = None) -> Tuple[str, str]:
        """Generate SSO authorization URL"""
        if provider not in self.providers:
            raise SSOError(f"Unknown SSO provider: {provider}")
        
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)
        
        # Store state with metadata
        self.state_storage[state] = {
            "provider": provider,
            "workspace_id": workspace_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        # Get authorization URL from provider
        auth_url = self.providers[provider].get_authorization_url(state)
        
        logger.info(f"Generated SSO URL for {provider}")
        return auth_url, state
    
    async def handle_sso_callback(
        self,
        provider: str,
        code: str,
        state: str,
        db_session
    ) -> Tuple[UserResponse, str]:
        """Handle SSO callback and authenticate user"""
        
        # Validate state parameter
        if state not in self.state_storage:
            raise SSOError("Invalid or expired state parameter", provider=provider)
        
        state_data = self.state_storage[state]
        
        # Check expiration
        if datetime.utcnow() > state_data["expires_at"]:
            del self.state_storage[state]
            raise SSOError("State parameter expired", provider=provider)
        
        # Verify provider matches
        if state_data["provider"] != provider:
            raise SSOError("Provider mismatch", provider=provider)
        
        try:
            # Exchange code for token
            token_data = await self.providers[provider].exchange_code_for_token(code)
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise SSOError("No access token received", provider=provider)
            
            # Get user information
            user_info = await self.providers[provider].get_user_info(access_token)
            
            # Create or update user
            user, access_token = await self._create_or_update_user(
                user_info, provider, state_data.get("workspace_id"), db_session
            )
            
            # Clean up state
            del self.state_storage[state]
            
            logger.info(f"SSO authentication successful for {user.email} via {provider}")
            return user, access_token
        
        except Exception as e:
            # Clean up state on error
            if state in self.state_storage:
                del self.state_storage[state]
            
            if isinstance(e, SSOError):
                raise
            else:
                logger.error(f"SSO callback error: {e}")
                raise SSOError(f"SSO authentication failed: {str(e)}", provider=provider)
    
    async def _create_or_update_user(
        self,
        user_info: Dict[str, Any],
        provider: str,
        workspace_id: Optional[str],
        db_session
    ) -> Tuple[UserResponse, str]:
        """Create or update user from SSO information"""
        
        # Extract user information based on provider
        email = self._extract_email(user_info, provider)
        full_name = self._extract_name(user_info, provider)
        
        if not email:
            raise SSOError("No email address provided by SSO provider", provider=provider)
        
        # Check if user already exists
        existing_user = await self.auth_service.get_user_by_email(email, db_session)
        
        if existing_user:
            # Update existing user
            existing_user.sso_provider = provider
            existing_user.sso_id = self._extract_user_id(user_info, provider)
            existing_user.last_login = datetime.utcnow()
            
            if full_name and not existing_user.full_name:
                existing_user.full_name = full_name
            
            await db_session.commit()
            
            # Generate access token
            access_token = self.auth_service.create_access_token(
                data={"sub": existing_user.email, "user_id": str(existing_user.id)}
            )
            
            return UserResponse.from_orm(existing_user), access_token
        
        else:
            # Create new user
            user_create = UserCreate(
                email=email,
                full_name=full_name or email.split("@")[0],
                password="",  # No password for SSO users
                sso_provider=provider,
                sso_id=self._extract_user_id(user_info, provider)
            )
            
            user = await self.auth_service.create_user(user_create, db_session)
            
            # Add to workspace if specified
            if workspace_id:
                await self._add_user_to_workspace(user.id, workspace_id, db_session)
            
            # Generate access token
            access_token = self.auth_service.create_access_token(
                data={"sub": user.email, "user_id": str(user.id)}
            )
            
            return user, access_token
    
    def _extract_email(self, user_info: Dict[str, Any], provider: str) -> Optional[str]:
        """Extract email from user info based on provider"""
        if provider == "google":
            return user_info.get("email")
        elif provider == "azure":
            return user_info.get("mail") or user_info.get("userPrincipalName")
        elif provider == "okta":
            return user_info.get("email")
        
        return None
    
    def _extract_name(self, user_info: Dict[str, Any], provider: str) -> Optional[str]:
        """Extract full name from user info based on provider"""
        if provider == "google":
            return user_info.get("name")
        elif provider == "azure":
            return user_info.get("displayName")
        elif provider == "okta":
            return user_info.get("name")
        
        return None
    
    def _extract_user_id(self, user_info: Dict[str, Any], provider: str) -> Optional[str]:
        """Extract user ID from user info based on provider"""
        if provider == "google":
            return user_info.get("id")
        elif provider == "azure":
            return user_info.get("id")
        elif provider == "okta":
            return user_info.get("sub")
        
        return None
    
    async def _add_user_to_workspace(
        self,
        user_id: str,
        workspace_id: str,
        db_session
    ):
        """Add user to workspace (implement based on your workspace model)"""
        # This would depend on your workspace membership model
        # For now, just log the action
        logger.info(f"Adding user {user_id} to workspace {workspace_id}")
    
    def cleanup_expired_states(self):
        """Clean up expired state parameters"""
        now = datetime.utcnow()
        expired_states = [
            state for state, data in self.state_storage.items()
            if data["expires_at"] < now
        ]
        
        for state in expired_states:
            del self.state_storage[state]
        
        if expired_states:
            logger.info(f"Cleaned up {len(expired_states)} expired SSO states")
    
    async def get_sso_status(self) -> Dict[str, Any]:
        """Get SSO service status"""
        available_providers = self.get_available_providers()
        
        return {
            "available_providers": available_providers,
            "total_providers": len(self.providers),
            "configured_providers": len(available_providers),
            "active_states": len(self.state_storage),
            "status": "healthy" if available_providers else "no_providers_configured"
        }

# Global SSO service instance
sso_service = SSOService()