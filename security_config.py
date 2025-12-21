"""
Security Configuration for KeLiva Project
Contains all security-related settings and utilities
"""

import os
import hashlib
import secrets
from typing import List, Dict, Any
import re

class SecurityConfig:
    """Central security configuration class"""
    
    # Environment-based configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    JWT_SECRET = os.getenv("JWT_SECRET", "change-this-jwt-secret-in-production")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///keliva.db")
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,.railway.app,.vercel.app").split(",")
    
    # Rate Limiting
    RATE_LIMITS = {
        "health": "60/minute",
        "auth": "5/minute",
        "chat": "30/minute",
        "voice": "20/minute",
        "general": "100/minute"
    }
    
    # Security Headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    }
    
    # File Upload Security
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'audio/wav', 'audio/mp3']
    
    # Password Security
    MIN_PASSWORD_LENGTH = 8
    PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
    
    @staticmethod
    def generate_secret_key() -> str:
        """Generate a secure random secret key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            salt, password_hash = hashed.split(":")
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except ValueError:
            return False
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters long")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[@$!%*?&]', password):
            errors.append("Password must contain at least one special character (@$!%*?&)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def sanitize_input(input_text: str) -> str:
        """Sanitize user input to prevent XSS attacks"""
        if not isinstance(input_text, str):
            return str(input_text)
        
        # Remove potentially dangerous HTML/JS
        sanitized = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', input_text, flags=re.IGNORECASE)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
        
        # Remove SQL injection patterns
        sanitized = re.sub(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_file_upload(file_content: bytes, content_type: str) -> Dict[str, Any]:
        """Validate file upload for security"""
        errors = []
        
        # Check file size
        if len(file_content) > SecurityConfig.MAX_FILE_SIZE:
            errors.append(f"File size exceeds maximum allowed size of {SecurityConfig.MAX_FILE_SIZE // (1024*1024)}MB")
        
        # Check file type
        if content_type not in SecurityConfig.ALLOWED_FILE_TYPES:
            errors.append(f"File type {content_type} is not allowed")
        
        # Check for malicious content (basic check)
        if b'<script' in file_content.lower() or b'javascript:' in file_content.lower():
            errors.append("File contains potentially malicious content")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def get_client_ip(request) -> str:
        """Extract real client IP from request (handles proxies)"""
        # Check for forwarded IP (from proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def is_suspicious_request(request) -> bool:
        """Detect potentially suspicious requests"""
        user_agent = request.headers.get("User-Agent", "").lower()
        
        # Check for common bot/scanner patterns
        suspicious_patterns = [
            "sqlmap", "nikto", "nmap", "masscan", "zap", "burp",
            "python-requests", "curl", "wget", "scanner"
        ]
        
        for pattern in suspicious_patterns:
            if pattern in user_agent:
                return True
        
        # Check for suspicious URL patterns
        url_path = str(request.url.path).lower()
        suspicious_paths = [
            "admin", "phpmyadmin", "wp-admin", ".env", "config",
            "backup", "test", "debug", "api/v1/admin"
        ]
        
        for path in suspicious_paths:
            if path in url_path:
                return True
        
        return False

# Security middleware functions
def apply_security_headers(response):
    """Apply security headers to response"""
    for header, value in SecurityConfig.SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "INFO"):
    """Log security events for monitoring"""
    import logging
    logger = logging.getLogger("security")
    
    log_message = f"SECURITY_EVENT: {event_type} | Details: {details}"
    
    if severity == "CRITICAL":
        logger.critical(log_message)
    elif severity == "ERROR":
        logger.error(log_message)
    elif severity == "WARNING":
        logger.warning(log_message)
    else:
        logger.info(log_message)

# Export configuration
__all__ = ['SecurityConfig', 'apply_security_headers', 'log_security_event']