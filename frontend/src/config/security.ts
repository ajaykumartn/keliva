/**
 * Frontend Security Configuration
 * Handles client-side security measures and API communication
 */

export interface SecurityConfig {
  API_BASE_URL: string;
  MAX_FILE_SIZE: number;
  ALLOWED_FILE_TYPES: string[];
  SESSION_TIMEOUT: number;
  ENABLE_CSP: boolean;
  DEBUG_MODE: boolean;
}

export const SECURITY_CONFIG: SecurityConfig = {
  API_BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  MAX_FILE_SIZE: parseInt(import.meta.env.VITE_MAX_FILE_SIZE) || 5 * 1024 * 1024, // 5MB
  ALLOWED_FILE_TYPES: import.meta.env.VITE_ALLOWED_FILE_TYPES?.split(',') || ['image/jpeg', 'image/png', 'image/gif'],
  SESSION_TIMEOUT: parseInt(import.meta.env.VITE_SESSION_TIMEOUT) || 30 * 60 * 1000, // 30 minutes
  ENABLE_CSP: import.meta.env.VITE_ENABLE_CSP === 'true',
  DEBUG_MODE: import.meta.env.VITE_DEBUG_MODE === 'true'
};

/**
 * Input Sanitization
 */
export const sanitizeInput = (input: string): string => {
  if (typeof input !== 'string') {
    return String(input);
  }

  return input
    // Remove script tags
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    // Remove javascript: protocol
    .replace(/javascript:/gi, '')
    // Remove event handlers
    .replace(/on\w+\s*=/gi, '')
    // Remove potentially dangerous HTML
    .replace(/<iframe\b[^>]*>/gi, '')
    .replace(/<object\b[^>]*>/gi, '')
    .replace(/<embed\b[^>]*>/gi, '')
    // Trim whitespace
    .trim();
};

/**
 * Validate file upload
 */
export const validateFileUpload = (file: File): { valid: boolean; errors: string[] } => {
  const errors: string[] = [];

  // Check file size
  if (file.size > SECURITY_CONFIG.MAX_FILE_SIZE) {
    errors.push(`File size exceeds maximum allowed size of ${SECURITY_CONFIG.MAX_FILE_SIZE / (1024 * 1024)}MB`);
  }

  // Check file type
  if (!SECURITY_CONFIG.ALLOWED_FILE_TYPES.includes(file.type)) {
    errors.push(`File type ${file.type} is not allowed`);
  }

  // Check file name for suspicious patterns
  const suspiciousPatterns = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.js', '.vbs'];
  const fileName = file.name.toLowerCase();
  
  for (const pattern of suspiciousPatterns) {
    if (fileName.endsWith(pattern)) {
      errors.push('File type is not allowed for security reasons');
      break;
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
};

/**
 * Secure API Call Wrapper
 */
export const secureApiCall = async (
  endpoint: string, 
  options: RequestInit = {},
  requireAuth: boolean = false
): Promise<Response> => {
  const url = `${SECURITY_CONFIG.API_BASE_URL}${endpoint}`;
  
  // Default headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...(options.headers as Record<string, string> || {})
  };

  // Add authentication if required
  if (requireAuth) {
    const token = localStorage.getItem('keliva_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    } else {
      throw new Error('Authentication required but no token found');
    }
  }

  // Sanitize request body if it's JSON
  let body = options.body;
  if (body && typeof body === 'string') {
    try {
      const jsonData = JSON.parse(body);
      const sanitizedData = sanitizeObject(jsonData);
      body = JSON.stringify(sanitizedData);
    } catch (e) {
      // Not JSON, leave as is
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
    body,
    credentials: 'include' // Include cookies for CSRF protection
  });

  // Log security events in debug mode
  if (SECURITY_CONFIG.DEBUG_MODE) {
    console.log(`API Call: ${options.method || 'GET'} ${endpoint} - Status: ${response.status}`);
  }

  return response;
};

/**
 * Sanitize object recursively
 */
const sanitizeObject = (obj: any): any => {
  if (typeof obj === 'string') {
    return sanitizeInput(obj);
  }
  
  if (Array.isArray(obj)) {
    return obj.map(sanitizeObject);
  }
  
  if (obj && typeof obj === 'object') {
    const sanitized: any = {};
    for (const [key, value] of Object.entries(obj)) {
      sanitized[sanitizeInput(key)] = sanitizeObject(value);
    }
    return sanitized;
  }
  
  return obj;
};

/**
 * Session Management
 */
export class SessionManager {
  private static instance: SessionManager;
  private sessionTimer: number | null = null;

  static getInstance(): SessionManager {
    if (!SessionManager.instance) {
      SessionManager.instance = new SessionManager();
    }
    return SessionManager.instance;
  }

  startSession(): void {
    this.resetSessionTimer();
  }

  resetSessionTimer(): void {
    if (this.sessionTimer) {
      clearTimeout(this.sessionTimer);
    }

    this.sessionTimer = window.setTimeout(() => {
      this.expireSession();
    }, SECURITY_CONFIG.SESSION_TIMEOUT);
  }

  expireSession(): void {
    // Clear all authentication data
    localStorage.removeItem('keliva_token');
    localStorage.removeItem('keliva_user');
    localStorage.removeItem('keliva_authenticated');
    
    // Redirect to login
    window.location.href = '/login';
    
    // Show notification
    alert('Your session has expired. Please log in again.');
  }

  extendSession(): void {
    const token = localStorage.getItem('keliva_token');
    if (token) {
      this.resetSessionTimer();
    }
  }

  endSession(): void {
    if (this.sessionTimer) {
      clearTimeout(this.sessionTimer);
      this.sessionTimer = null;
    }
    
    // Clear authentication data
    localStorage.removeItem('keliva_token');
    localStorage.removeItem('keliva_user');
    localStorage.removeItem('keliva_authenticated');
  }
}

/**
 * Content Security Policy
 */
export const applyCSP = (): void => {
  if (!SECURITY_CONFIG.ENABLE_CSP) return;

  const cspMeta = document.createElement('meta');
  cspMeta.httpEquiv = 'Content-Security-Policy';
  cspMeta.content = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "connect-src 'self' https://api.groq.com wss:",
    "font-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'"
  ].join('; ');

  document.head.appendChild(cspMeta);
};

/**
 * XSS Protection
 */
export const escapeHtml = (text: string): string => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

/**
 * Rate Limiting (Client-side)
 */
export class RateLimiter {
  private requests: Map<string, number[]> = new Map();

  isAllowed(key: string, maxRequests: number, windowMs: number): boolean {
    const now = Date.now();
    const windowStart = now - windowMs;
    
    // Get existing requests for this key
    const keyRequests = this.requests.get(key) || [];
    
    // Filter out old requests
    const recentRequests = keyRequests.filter(time => time > windowStart);
    
    // Check if limit exceeded
    if (recentRequests.length >= maxRequests) {
      return false;
    }
    
    // Add current request
    recentRequests.push(now);
    this.requests.set(key, recentRequests);
    
    return true;
  }

  reset(key: string): void {
    this.requests.delete(key);
  }
}

/**
 * Security Event Logging
 */
export const logSecurityEvent = (event: string, details: any = {}): void => {
  if (SECURITY_CONFIG.DEBUG_MODE) {
    console.warn(`SECURITY EVENT: ${event}`, details);
  }
  
  // In production, you might want to send this to a logging service
  // secureApiCall('/api/security/log', {
  //   method: 'POST',
  //   body: JSON.stringify({ event, details, timestamp: new Date().toISOString() })
  // }).catch(() => {}); // Fail silently for logging
};

// Initialize session management
const sessionManager = SessionManager.getInstance();

// Auto-extend session on user activity
const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
activityEvents.forEach(event => {
  document.addEventListener(event, () => {
    sessionManager.extendSession();
  }, { passive: true });
});

// Apply CSP on load
document.addEventListener('DOMContentLoaded', applyCSP);

export { sessionManager };