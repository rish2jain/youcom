"""
HubSpot API Client with OAuth 2.0 authentication and rate limiting
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlencode

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.services.encryption_service import encryption_service


class HubSpotRateLimitError(Exception):
    """Raised when HubSpot API rate limit is exceeded"""
    pass


class HubSpotAuthError(Exception):
    """Raised when HubSpot authentication fails"""
    pass


class HubSpotAPIError(Exception):
    """Raised when HubSpot API returns an error"""
    pass


class HubSpotClient:
    """HubSpot API client with OAuth 2.0 and rate limiting"""
    
    BASE_URL = "https://api.hubapi.com"
    OAUTH_URL = "https://app.hubspot.com/oauth"
    
    # Rate limiting: HubSpot allows 100 requests per 10 seconds
    MAX_REQUESTS_PER_WINDOW = 100
    RATE_LIMIT_WINDOW = 10  # seconds
    
    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Rate limiting
        self._request_times: List[float] = []
        self._rate_limit_lock = asyncio.Lock()
        
        # Token refresh tracking
        self._token_refresh_lock = asyncio.Lock()
        self._token_expires_at: Optional[datetime] = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @classmethod
    def from_encrypted_tokens(cls, encrypted_access_token: str, encrypted_refresh_token: Optional[str] = None):
        """Create client from encrypted tokens"""
        access_token = encryption_service.decrypt(encrypted_access_token)
        refresh_token = encryption_service.decrypt(encrypted_refresh_token) if encrypted_refresh_token else None
        
        if not access_token:
            raise HubSpotAuthError("Failed to decrypt access token")
        
        return cls(access_token, refresh_token)
    
    @classmethod
    def get_oauth_url(cls, client_id: str, redirect_uri: str, scopes: List[str], state: Optional[str] = None) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "response_type": "code"
        }
        
        if state:
            params["state"] = state
        
        return f"{cls.OAUTH_URL}/authorize?{urlencode(params)}"
    
    @classmethod
    async def exchange_code_for_tokens(cls, client_id: str, client_secret: str, 
                                     redirect_uri: str, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{cls.OAUTH_URL}/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise HubSpotAuthError(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def refresh_access_token(self, client_id: str, client_secret: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            raise HubSpotAuthError("No refresh token available")
        
        async with self._token_refresh_lock:
            response = await self.client.post(
                f"{self.OAUTH_URL}/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": self.refresh_token
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise HubSpotAuthError(f"Token refresh failed: {response.text}")
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            
            # Update refresh token if provided
            if "refresh_token" in token_data:
                self.refresh_token = token_data["refresh_token"]
            
            # Set token expiration
            if "expires_in" in token_data:
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
            
            return token_data
    
    async def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        async with self._rate_limit_lock:
            now = time.time()
            
            # Remove requests older than the rate limit window
            self._request_times = [t for t in self._request_times if now - t < self.RATE_LIMIT_WINDOW]
            
            # If we're at the limit, wait until we can make another request
            if len(self._request_times) >= self.MAX_REQUESTS_PER_WINDOW:
                oldest_request = min(self._request_times)
                wait_time = self.RATE_LIMIT_WINDOW - (now - oldest_request)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            # Record this request
            self._request_times.append(now)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((HubSpotRateLimitError, httpx.RequestError))
    )
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make authenticated request to HubSpot API with rate limiting and retries"""
        await self._wait_for_rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Content-Type"] = "application/json"
        
        response = await self.client.request(method, url, headers=headers, **kwargs)
        
        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 10))
            await asyncio.sleep(retry_after)
            raise HubSpotRateLimitError("Rate limit exceeded")
        
        # Handle authentication errors
        if response.status_code == 401:
            raise HubSpotAuthError("Authentication failed - token may be expired")
        
        # Handle other errors
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            raise HubSpotAPIError(f"API error {response.status_code}: {error_data}")
        
        return response
    
    # Contact API methods
    async def get_contacts(self, limit: int = 100, after: Optional[str] = None, 
                          properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get contacts from HubSpot"""
        params = {"limit": limit}
        if after:
            params["after"] = after
        if properties:
            params["properties"] = ",".join(properties)
        
        response = await self._make_request("GET", "/crm/v3/objects/contacts", params=params)
        return response.json()
    
    async def get_contact(self, contact_id: str, properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get a specific contact by ID"""
        params = {}
        if properties:
            params["properties"] = ",".join(properties)
        
        response = await self._make_request("GET", f"/crm/v3/objects/contacts/{contact_id}", params=params)
        return response.json()
    
    async def create_contact(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact"""
        data = {"properties": properties}
        response = await self._make_request("POST", "/crm/v3/objects/contacts", json=data)
        return response.json()
    
    async def update_contact(self, contact_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update a contact"""
        data = {"properties": properties}
        response = await self._make_request("PATCH", f"/crm/v3/objects/contacts/{contact_id}", json=data)
        return response.json()
    
    # Company API methods
    async def get_companies(self, limit: int = 100, after: Optional[str] = None,
                           properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get companies from HubSpot"""
        params = {"limit": limit}
        if after:
            params["after"] = after
        if properties:
            params["properties"] = ",".join(properties)
        
        response = await self._make_request("GET", "/crm/v3/objects/companies", params=params)
        return response.json()
    
    async def get_company(self, company_id: str, properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get a specific company by ID"""
        params = {}
        if properties:
            params["properties"] = ",".join(properties)
        
        response = await self._make_request("GET", f"/crm/v3/objects/companies/{company_id}", params=params)
        return response.json()
    
    async def create_company(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company"""
        data = {"properties": properties}
        response = await self._make_request("POST", "/crm/v3/objects/companies", json=data)
        return response.json()
    
    async def update_company(self, company_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update a company"""
        data = {"properties": properties}
        response = await self._make_request("PATCH", f"/crm/v3/objects/companies/{company_id}", json=data)
        return response.json()
    
    # Custom Properties API methods
    async def get_contact_properties(self) -> Dict[str, Any]:
        """Get all contact properties"""
        response = await self._make_request("GET", "/crm/v3/properties/contacts")
        return response.json()
    
    async def create_contact_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom contact property"""
        response = await self._make_request("POST", "/crm/v3/properties/contacts", json=property_data)
        return response.json()
    
    async def get_company_properties(self) -> Dict[str, Any]:
        """Get all company properties"""
        response = await self._make_request("GET", "/crm/v3/properties/companies")
        return response.json()
    
    async def create_company_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom company property"""
        response = await self._make_request("POST", "/crm/v3/properties/companies", json=property_data)
        return response.json()
    
    # Workflow API methods
    async def trigger_workflow(self, workflow_id: str, object_id: str, object_type: str = "contact") -> Dict[str, Any]:
        """Trigger a workflow for a specific object"""
        data = {
            "objectId": object_id,
            "objectType": object_type
        }
        response = await self._make_request("POST", f"/automation/v2/workflows/{workflow_id}/enrollments", json=data)
        return response.json()
    
    # Account Info API methods
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        response = await self._make_request("GET", "/account-info/v3/details")
        return response.json()
    
    # Search API methods
    async def search_contacts(self, filters: List[Dict[str, Any]], properties: Optional[List[str]] = None,
                             limit: int = 100, after: Optional[str] = None) -> Dict[str, Any]:
        """Search contacts with filters"""
        data = {
            "filterGroups": [{"filters": filters}],
            "limit": limit,
            "properties": properties or []
        }
        if after:
            data["after"] = after
        
        response = await self._make_request("POST", "/crm/v3/objects/contacts/search", json=data)
        return response.json()
    
    async def search_companies(self, filters: List[Dict[str, Any]], properties: Optional[List[str]] = None,
                              limit: int = 100, after: Optional[str] = None) -> Dict[str, Any]:
        """Search companies with filters"""
        data = {
            "filterGroups": [{"filters": filters}],
            "limit": limit,
            "properties": properties or []
        }
        if after:
            data["after"] = after
        
        response = await self._make_request("POST", "/crm/v3/objects/companies/search", json=data)
        return response.json()