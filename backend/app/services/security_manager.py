"""
Security Manager for Advanced Intelligence Suite

This service provides comprehensive security hardening, rate limiting,
input validation, and GDPR compliance for all Advanced Intelligence Suite components.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import secrets
import ipaddress
from urllib.parse import urlparse

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, text
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from jose import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from app.models.ml_training import FeedbackRecord
from app.models.user import User
from app.models.audit_log import AuditLog
from app.config import settings

logger = logging.getLogger(__name__)

class SecurityLevel(str, Enum):
    """Security levels for different operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RateLimitType(str, Enum):
    """Types of rate limiting."""
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"

class ComplianceStandard(str, Enum):
    """Compliance standards."""
    GDPR = "gdpr"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"

@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    limit_type: RateLimitType
    endpoint_pattern: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_allowance: int
    security_level: SecurityLevel

@dataclass
class SecurityEvent:
    """Security event for logging and monitoring."""
    event_id: str
    event_type: str
    severity: SecurityLevel
    source_ip: str
    user_id: Optional[str]
    endpoint: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ValidationRule:
    """Input validation rule."""
    field_name: str
    data_type: str
    min_length: Optional[int]
    max_length: Optional[int]
    pattern: Optional[str]
    allowed_values: Optional[List[str]]
    required: bool
    sanitize: bool

class SecurityManager:
    """Comprehensive security manager for Advanced Intelligence Suite."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client: Optional[redis.Redis] = None
        
        # Encryption setup
        self.encryption_key = self._derive_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Rate limiting configuration
        self.rate_limit_rules = {
            # ML endpoints - higher limits for legitimate use
            "/api/ml/predict": RateLimitRule(
                limit_type=RateLimitType.PER_USER,
                endpoint_pattern="/api/ml/predict",
                requests_per_minute=100,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_allowance=20,
                security_level=SecurityLevel.MEDIUM
            ),
            "/api/ml/feedback": RateLimitRule(
                limit_type=RateLimitType.PER_USER,
                endpoint_pattern="/api/ml/feedback",
                requests_per_minute=50,
                requests_per_hour=500,
                requests_per_day=2000,
                burst_allowance=10,
                security_level=SecurityLevel.MEDIUM
            ),
            
            # Sentiment analysis endpoints
            "/api/sentiment": RateLimitRule(
                limit_type=RateLimitType.PER_USER,
                endpoint_pattern="/api/sentiment/*",
                requests_per_minute=200,
                requests_per_hour=2000,
                requests_per_day=20000,
                burst_allowance=50,
                security_level=SecurityLevel.LOW
            ),
            
            # Template endpoints
            "/api/templates": RateLimitRule(
                limit_type=RateLimitType.PER_USER,
                endpoint_pattern="/api/templates/*",
                requests_per_minute=30,
                requests_per_hour=300,
                requests_per_day=1000,
                burst_allowance=10,
                security_level=SecurityLevel.LOW
            ),
            
            # Integration endpoints - more restrictive
            "/api/integrations": RateLimitRule(
                limit_type=RateLimitType.PER_USER,
                endpoint_pattern="/api/integrations/*",
                requests_per_minute=20,
                requests_per_hour=100,
                requests_per_day=500,
                burst_allowance=5,
                security_level=SecurityLevel.HIGH
            ),
            
            # Admin endpoints - very restrictive
            "/api/admin": RateLimitRule(
                limit_type=RateLimitType.PER_USER,
                endpoint_pattern="/api/admin/*",
                requests_per_minute=10,
                requests_per_hour=50,
                requests_per_day=200,
                burst_allowance=2,
                security_level=SecurityLevel.CRITICAL
            )
        }
        
        # Input validation rules
        self.validation_rules = {
            "user_feedback": [
                ValidationRule("feedback_type", "string", 1, 50, r"^[a-zA-Z_]+$", 
                             ["accuracy", "relevance", "severity", "category"], True, True),
                ValidationRule("original_value", "float", None, None, None, None, True, False),
                ValidationRule("corrected_value", "float", None, None, None, None, True, False),
                ValidationRule("confidence", "float", None, None, r"^[0-1](\.[0-9]+)?$", None, False, False),
                ValidationRule("comments", "string", 0, 1000, None, None, False, True)
            ],
            "template_data": [
                ValidationRule("name", "string", 1, 100, r"^[a-zA-Z0-9\s\-_]+$", None, True, True),
                ValidationRule("industry_sector", "string", 1, 50, r"^[a-zA-Z\s]+$", None, True, True),
                ValidationRule("description", "string", 0, 500, None, None, False, True),
                ValidationRule("template_config", "json", None, None, None, None, True, False)
            ],
            "integration_config": [
                ValidationRule("integration_type", "string", 1, 50, r"^[a-zA-Z_]+$", 
                             ["hubspot", "obsidian", "slack", "teams"], True, True),
                ValidationRule("api_key", "string", 10, 500, None, None, False, False),  # Don't sanitize API keys
                ValidationRule("webhook_url", "url", 10, 500, None, None, False, True),
                ValidationRule("sync_enabled", "boolean", None, None, None, None, False, False)
            ]
        }
        
        # Security event tracking
        self.security_events: List[SecurityEvent] = []
        self.max_security_events = 10000
        
        # Blocked IPs and users
        self.blocked_ips: Set[str] = set()
        self.blocked_users: Set[str] = set()
        self.suspicious_ips: Dict[str, int] = {}
        
        # GDPR compliance settings
        self.gdpr_retention_days = 365 * 2  # 2 years default
        self.gdpr_anonymization_fields = [
            "user_id", "email", "ip_address", "user_agent"
        ]
        
        # JWT settings
        self.jwt_secret = getattr(settings, 'jwt_secret_key', None)
        if not self.jwt_secret:
            raise RuntimeError(
                "JWT secret key is required but not configured. "
                "Please set 'jwt_secret_key' in your settings or environment variables. "
                "Use a secure, random value that persists across restarts."
            )
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24
        
        # Security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
    
    async def initialize(self) -> None:
        """Initialize the security manager."""
        try:
            # Connect to Redis for rate limiting and caching
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            
            # Load blocked IPs and users from database
            await self._load_security_blacklists()
            
            logger.info("Security manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize security manager: {e}")
            raise
    
    def _derive_encryption_key(self) -> bytes:
        """Derive encryption key from settings."""
        password = getattr(settings, 'encryption_password', None)
        salt = getattr(settings, 'encryption_salt', None)
        
        if not password or not salt:
            raise RuntimeError(
                "Encryption password and salt are required but not configured. "
                "Please set 'encryption_password' and 'encryption_salt' in your settings. "
                "Use secure, random values for production deployments."
            )
        
        # Ensure values are bytes
        if isinstance(password, str):
            password = password.encode()
        if isinstance(salt, str):
            salt = salt.encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    async def check_rate_limit(
        self, 
        request: Request,
        endpoint: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Check if request is within rate limits."""
        try:
            # Find matching rate limit rule
            rule = self._find_rate_limit_rule(endpoint)
            if not rule:
                return True  # No rate limit rule, allow request
            
            # Determine rate limit key
            if rule.limit_type == RateLimitType.PER_IP:
                key_suffix = self._get_client_ip(request)
            elif rule.limit_type == RateLimitType.PER_USER and user_id:
                key_suffix = user_id
            elif rule.limit_type == RateLimitType.PER_ENDPOINT:
                key_suffix = endpoint
            else:
                key_suffix = "global"
            
            # Check rate limits for different time windows
            current_time = int(time.time())
            
            # Check minute limit
            minute_key = f"rate_limit:minute:{endpoint}:{key_suffix}:{current_time // 60}"
            minute_count = await self._get_rate_limit_count(minute_key, 60)
            
            if minute_count >= rule.requests_per_minute:
                await self._log_security_event(
                    "rate_limit_exceeded",
                    SecurityLevel.MEDIUM,
                    request,
                    user_id,
                    f"Minute rate limit exceeded: {minute_count}/{rule.requests_per_minute}"
                )
                return False
            
            # Check hour limit
            hour_key = f"rate_limit:hour:{endpoint}:{key_suffix}:{current_time // 3600}"
            hour_count = await self._get_rate_limit_count(hour_key, 3600)
            
            if hour_count >= rule.requests_per_hour:
                await self._log_security_event(
                    "rate_limit_exceeded",
                    SecurityLevel.MEDIUM,
                    request,
                    user_id,
                    f"Hour rate limit exceeded: {hour_count}/{rule.requests_per_hour}"
                )
                return False
            
            # Check day limit
            day_key = f"rate_limit:day:{endpoint}:{key_suffix}:{current_time // 86400}"
            day_count = await self._get_rate_limit_count(day_key, 86400)
            
            if day_count >= rule.requests_per_day:
                await self._log_security_event(
                    "rate_limit_exceeded",
                    SecurityLevel.HIGH,
                    request,
                    user_id,
                    f"Day rate limit exceeded: {day_count}/{rule.requests_per_day}"
                )
                return False
            
            # Increment counters
            await self._increment_rate_limit_counters([minute_key, hour_key, day_key])
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow request on error to avoid blocking legitimate traffic
    
    def _find_rate_limit_rule(self, endpoint: str) -> Optional[RateLimitRule]:
        """Find matching rate limit rule for endpoint."""
        for pattern, rule in self.rate_limit_rules.items():
            if self._match_endpoint_pattern(endpoint, pattern):
                return rule
        return None
    
    def _match_endpoint_pattern(self, endpoint: str, pattern: str) -> bool:
        """Check if endpoint matches pattern (supports wildcards)."""
        if pattern.endswith("*"):
            return endpoint.startswith(pattern[:-1])
        return endpoint == pattern
    
    async def _get_rate_limit_count(self, key: str, ttl: int) -> int:
        """Get current rate limit count for key."""
        if not self.redis_client:
            return 0
        
        try:
            count = await self.redis_client.get(key)
            return int(count) if count else 0
        except Exception:
            return 0
    
    async def _increment_rate_limit_counters(self, keys: List[str]) -> None:
        """Increment rate limit counters."""
        if not self.redis_client:
            return
        
        try:
            pipe = self.redis_client.pipeline()
            for key in keys:
                pipe.incr(key)
                # Set TTL based on key type
                if "minute" in key:
                    pipe.expire(key, 120)  # 2 minutes
                elif "hour" in key:
                    pipe.expire(key, 7200)  # 2 hours
                elif "day" in key:
                    pipe.expire(key, 172800)  # 2 days
            
            await pipe.execute()
            
        except Exception as e:
            logger.warning(f"Failed to increment rate limit counters: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"
    
    async def validate_input(
        self, 
        data: Dict[str, Any], 
        validation_type: str
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Validate and sanitize input data."""
        if validation_type not in self.validation_rules:
            return True, data, []  # No validation rules, allow data
        
        rules = self.validation_rules[validation_type]
        sanitized_data = {}
        errors = []
        
        try:
            for rule in rules:
                field_name = rule.field_name
                value = data.get(field_name)
                
                # Check required fields
                if rule.required and (value is None or value == ""):
                    errors.append(f"Field '{field_name}' is required")
                    continue
                
                # Skip validation for optional empty fields
                if value is None or value == "":
                    continue
                
                # Type validation
                if not self._validate_type(value, rule.data_type):
                    errors.append(f"Field '{field_name}' must be of type {rule.data_type}")
                    continue
                
                # Length validation
                if rule.data_type == "string" and isinstance(value, str):
                    if rule.min_length and len(value) < rule.min_length:
                        errors.append(f"Field '{field_name}' must be at least {rule.min_length} characters")
                        continue
                    
                    if rule.max_length and len(value) > rule.max_length:
                        errors.append(f"Field '{field_name}' must be at most {rule.max_length} characters")
                        continue
                
                # Pattern validation
                if rule.pattern and isinstance(value, str):
                    if not re.match(rule.pattern, value):
                        errors.append(f"Field '{field_name}' format is invalid")
                        continue
                
                # Allowed values validation
                if rule.allowed_values and value not in rule.allowed_values:
                    errors.append(f"Field '{field_name}' must be one of: {', '.join(rule.allowed_values)}")
                    continue
                
                # URL validation
                if rule.data_type == "url":
                    if not self._validate_url(value):
                        errors.append(f"Field '{field_name}' must be a valid URL")
                        continue
                
                # Sanitize if needed
                if rule.sanitize and isinstance(value, str):
                    value = self._sanitize_string(value)
                
                sanitized_data[field_name] = value
            
            # Copy non-validated fields
            for key, value in data.items():
                if key not in sanitized_data and key not in [rule.field_name for rule in rules]:
                    sanitized_data[key] = value
            
            is_valid = len(errors) == 0
            return is_valid, sanitized_data, errors
            
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            return False, {}, [f"Validation error: {str(e)}"]
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type."""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "float":
            return isinstance(value, (int, float))
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "json":
            return isinstance(value, (dict, list))
        elif expected_type == "url":
            return isinstance(value, str)
        return True
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _sanitize_string(self, value: str) -> str:
        """
        Sanitize string input for safe display and normalization.
        
        WARNING: This function is NOT a substitute for parameterized queries
        or context-specific encoding. Use proper parameterized queries for
        all database operations and appropriate escaping for HTML output.
        """
        # Trim whitespace and normalize unicode
        sanitized = value.strip()
        
        # Basic normalization - preserve legitimate characters like apostrophes
        # Only remove control characters and normalize whitespace
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        return sanitized
    
    async def check_ip_security(self, request: Request) -> bool:
        """Check if IP address is allowed."""
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            await self._log_security_event(
                "blocked_ip_access",
                SecurityLevel.HIGH,
                request,
                None,
                f"Access attempt from blocked IP: {client_ip}"
            )
            return False
        
        # Check for suspicious activity
        if client_ip in self.suspicious_ips:
            suspicious_count = self.suspicious_ips[client_ip]
            if suspicious_count > 10:  # Block after 10 suspicious activities
                self.blocked_ips.add(client_ip)
                await self._store_blocked_ip(client_ip, "Automatic block due to suspicious activity")
                return False
        
        return True
    
    async def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    async def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    async def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    async def generate_jwt_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """Generate JWT token for user."""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
            "iat": datetime.utcnow(),
            "iss": "advanced-intelligence-suite"
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    async def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    async def _log_security_event(
        self,
        event_type: str,
        severity: SecurityLevel,
        request: Request,
        user_id: Optional[str],
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security event."""
        try:
            event = SecurityEvent(
                event_id=secrets.token_urlsafe(16),
                event_type=event_type,
                severity=severity,
                source_ip=self._get_client_ip(request),
                user_id=user_id,
                endpoint=str(request.url.path),
                description=description,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Store in memory
            self.security_events.append(event)
            
            # Trim old events
            if len(self.security_events) > self.max_security_events:
                self.security_events = self.security_events[-self.max_security_events:]
            
            # Store in database for persistence
            audit_log = AuditLog(
                user_id=user_id,
                action=event_type,
                resource_type="security",
                resource_id=event.event_id,
                details={
                    "severity": severity.value,
                    "source_ip": event.source_ip,
                    "endpoint": event.endpoint,
                    "description": description,
                    "metadata": metadata or {}
                },
                ip_address=event.source_ip,
                user_agent=request.headers.get("User-Agent", "")
            )
            
            self.db.add(audit_log)
            await self.db.commit()
            
            # Update suspicious IP tracking
            if severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                ip = event.source_ip
                self.suspicious_ips[ip] = self.suspicious_ips.get(ip, 0) + 1
            
            logger.warning(f"Security event: {event_type} - {description}")
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    async def _load_security_blacklists(self) -> None:
        """Load blocked IPs and users from database."""
        try:
            # Load blocked IPs from audit logs (simplified approach)
            blocked_ip_result = await self.db.execute(
                select(AuditLog.ip_address)
                .where(AuditLog.action == "ip_blocked")
                .where(AuditLog.created_at >= datetime.utcnow() - timedelta(days=30))
                .distinct()
            )
            
            blocked_ips = [row[0] for row in blocked_ip_result.fetchall() if row[0]]
            self.blocked_ips.update(blocked_ips)
            
            logger.info(f"Loaded {len(blocked_ips)} blocked IPs")
            
        except Exception as e:
            logger.error(f"Failed to load security blacklists: {e}")
    
    async def _store_blocked_ip(self, ip: str, reason: str) -> None:
        """Store blocked IP in database."""
        try:
            audit_log = AuditLog(
                user_id=None,
                action="ip_blocked",
                resource_type="security",
                resource_id=ip,
                details={"reason": reason},
                ip_address=ip,
                user_agent=""
            )
            
            self.db.add(audit_log)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to store blocked IP: {e}")
    
    async def ensure_gdpr_compliance(self, user_id: str) -> Dict[str, Any]:
        """Ensure GDPR compliance for user data."""
        try:
            compliance_report = {
                "user_id": user_id,
                "data_retention_check": False,
                "anonymization_applied": False,
                "data_export_ready": False,
                "deletion_completed": False,
                "actions_taken": []
            }
            
            # Check data retention
            cutoff_date = datetime.utcnow() - timedelta(days=self.gdpr_retention_days)
            
            # Check ML feedback records
            old_feedback_result = await self.db.execute(
                select(func.count(FeedbackRecord.id))
                .where(FeedbackRecord.user_id == user_id)
                .where(FeedbackRecord.feedback_timestamp < cutoff_date)
            )
            
            old_feedback_count = old_feedback_result.scalar() or 0
            
            if old_feedback_count > 0:
                # Anonymize old feedback records
                await self.db.execute(
                    text("""
                        UPDATE ml_feedback_records 
                        SET user_id = 'anonymized_' || substr(md5(user_id || :salt), 1, 8)
                        WHERE user_id = :user_id 
                        AND feedback_timestamp < :cutoff_date
                    """),
                    {
                        "user_id": user_id,
                        "cutoff_date": cutoff_date,
                        "salt": secrets.token_urlsafe(16)
                    }
                )
                
                compliance_report["anonymization_applied"] = True
                compliance_report["actions_taken"].append(f"Anonymized {old_feedback_count} old feedback records")
            
            # Check audit logs
            old_audit_result = await self.db.execute(
                select(func.count(AuditLog.id))
                .where(AuditLog.user_id == user_id)
                .where(AuditLog.created_at < cutoff_date)
            )
            
            old_audit_count = old_audit_result.scalar() or 0
            
            if old_audit_count > 0:
                # Anonymize old audit logs
                await self.db.execute(
                    text("""
                        UPDATE audit_logs 
                        SET user_id = 'anonymized_' || substr(md5(user_id || :salt), 1, 8),
                            ip_address = 'anonymized',
                            user_agent = 'anonymized'
                        WHERE user_id = :user_id 
                        AND created_at < :cutoff_date
                    """),
                    {
                        "user_id": user_id,
                        "cutoff_date": cutoff_date,
                        "salt": secrets.token_urlsafe(16)
                    }
                )
                
                compliance_report["actions_taken"].append(f"Anonymized {old_audit_count} old audit logs")
            
            await self.db.commit()
            
            compliance_report["data_retention_check"] = True
            compliance_report["data_export_ready"] = True
            
            return compliance_report
            
        except Exception as e:
            logger.error(f"GDPR compliance check failed for user {user_id}: {e}")
            await self.db.rollback()
            return {"error": str(e)}
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data for GDPR compliance."""
        try:
            user_data = {
                "user_id": user_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "data": {}
            }
            
            # Export ML feedback records
            feedback_result = await self.db.execute(
                select(FeedbackRecord)
                .where(FeedbackRecord.user_id == user_id)
            )
            
            feedback_records = feedback_result.scalars().all()
            user_data["data"]["ml_feedback"] = [
                {
                    "id": record.id,
                    "feedback_type": record.feedback_type,
                    "original_value": record.original_value,
                    "corrected_value": record.corrected_value,
                    "confidence": record.confidence,
                    "feedback_timestamp": record.feedback_timestamp.isoformat(),
                    "processed": record.processed
                }
                for record in feedback_records
            ]
            
            # Export audit logs
            audit_result = await self.db.execute(
                select(AuditLog)
                .where(AuditLog.user_id == user_id)
                .order_by(desc(AuditLog.created_at))
                .limit(1000)  # Limit to recent 1000 entries
            )
            
            audit_records = audit_result.scalars().all()
            user_data["data"]["audit_logs"] = [
                {
                    "id": record.id,
                    "action": record.action,
                    "resource_type": record.resource_type,
                    "resource_id": record.resource_id,
                    "details": record.details,
                    "created_at": record.created_at.isoformat(),
                    "ip_address": record.ip_address
                }
                for record in audit_records
            ]
            
            return user_data
            
        except Exception as e:
            logger.error(f"User data export failed for user {user_id}: {e}")
            return {"error": str(e)}
    
    async def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """Delete all user data for GDPR right to be forgotten."""
        try:
            deletion_report = {
                "user_id": user_id,
                "deletion_timestamp": datetime.utcnow().isoformat(),
                "deleted_records": {},
                "errors": []
            }
            
            # Delete ML feedback records
            feedback_result = await self.db.execute(
                select(func.count(FeedbackRecord.id))
                .where(FeedbackRecord.user_id == user_id)
            )
            feedback_count = feedback_result.scalar() or 0
            
            if feedback_count > 0:
                await self.db.execute(
                    text("DELETE FROM ml_feedback_records WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                deletion_report["deleted_records"]["ml_feedback"] = feedback_count
            
            # Delete audit logs (keep anonymized version for security)
            audit_result = await self.db.execute(
                select(func.count(AuditLog.id))
                .where(AuditLog.user_id == user_id)
            )
            audit_count = audit_result.scalar() or 0
            
            if audit_count > 0:
                # Anonymize instead of delete for security audit trail
                await self.db.execute(
                    text("""
                        UPDATE audit_logs 
                        SET user_id = 'deleted_user',
                            ip_address = 'anonymized',
                            user_agent = 'anonymized'
                        WHERE user_id = :user_id
                    """),
                    {"user_id": user_id}
                )
                deletion_report["deleted_records"]["audit_logs"] = f"{audit_count} anonymized"
            
            await self.db.commit()
            
            return deletion_report
            
        except Exception as e:
            logger.error(f"User data deletion failed for user {user_id}: {e}")
            await self.db.rollback()
            return {"error": str(e)}
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers to add to responses."""
        return self.security_headers.copy()
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics and statistics."""
        try:
            # Count security events by type and severity
            event_stats = {}
            severity_stats = {}
            
            for event in self.security_events[-1000:]:  # Last 1000 events
                event_stats[event.event_type] = event_stats.get(event.event_type, 0) + 1
                severity_stats[event.severity.value] = severity_stats.get(event.severity.value, 0) + 1
            
            # Rate limiting statistics
            rate_limit_stats = {}
            if self.redis_client:
                try:
                    # Use SCAN to avoid blocking Redis
                    count = 0
                    async for key in self.redis_client.scan_iter(match="rate_limit:*", count=100):
                        count += 1
                    rate_limit_stats["active_rate_limits"] = count
                except Exception:
                    rate_limit_stats["active_rate_limits"] = 0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "security_events": {
                    "total_events": len(self.security_events),
                    "events_by_type": event_stats,
                    "events_by_severity": severity_stats
                },
                "blocked_entities": {
                    "blocked_ips": len(self.blocked_ips),
                    "suspicious_ips": len(self.suspicious_ips),
                    "blocked_users": len(self.blocked_users)
                },
                "rate_limiting": rate_limit_stats,
                "compliance": {
                    "gdpr_retention_days": self.gdpr_retention_days,
                    "anonymization_fields": len(self.gdpr_anonymization_fields)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get security metrics: {e}")
            return {"error": str(e)}
    
    async def run_security_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit."""
        try:
            audit_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "security_checks": {},
                "recommendations": [],
                "compliance_status": {},
                "risk_level": "low"
            }
            
            # Check for recent security events
            recent_events = [
                event for event in self.security_events
                if event.timestamp > datetime.utcnow() - timedelta(hours=24)
            ]
            
            critical_events = [
                event for event in recent_events
                if event.severity == SecurityLevel.CRITICAL
            ]
            
            audit_report["security_checks"]["recent_critical_events"] = len(critical_events)
            
            if len(critical_events) > 0:
                audit_report["risk_level"] = "high"
                audit_report["recommendations"].append("Investigate recent critical security events")
            
            # Check rate limiting effectiveness
            rate_limit_events = [
                event for event in recent_events
                if event.event_type == "rate_limit_exceeded"
            ]
            
            audit_report["security_checks"]["rate_limit_violations"] = len(rate_limit_events)
            
            if len(rate_limit_events) > 100:
                audit_report["recommendations"].append("Review rate limiting rules - high violation count")
            
            # Check blocked entities
            audit_report["security_checks"]["blocked_ips"] = len(self.blocked_ips)
            audit_report["security_checks"]["suspicious_ips"] = len(self.suspicious_ips)
            
            if len(self.suspicious_ips) > 50:
                audit_report["recommendations"].append("High number of suspicious IPs detected")
            
            # GDPR compliance check
            audit_report["compliance_status"]["gdpr"] = {
                "retention_policy_configured": self.gdpr_retention_days > 0,
                "anonymization_fields_defined": len(self.gdpr_anonymization_fields) > 0,
                "data_export_available": True,
                "data_deletion_available": True
            }
            
            # Security configuration check
            audit_report["security_checks"]["encryption_enabled"] = self.cipher_suite is not None
            audit_report["security_checks"]["jwt_configured"] = bool(self.jwt_secret)
            audit_report["security_checks"]["rate_limiting_enabled"] = len(self.rate_limit_rules) > 0
            audit_report["security_checks"]["input_validation_enabled"] = len(self.validation_rules) > 0
            
            # Overall risk assessment
            if audit_report["risk_level"] == "low" and len(audit_report["recommendations"]) == 0:
                audit_report["recommendations"].append("Security posture is good - continue monitoring")
            
            return audit_report
            
        except Exception as e:
            logger.error(f"Security audit failed: {e}")
            return {"error": str(e)}
    
    async def shutdown(self) -> None:
        """Shutdown the security manager."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Security manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during security manager shutdown: {e}")