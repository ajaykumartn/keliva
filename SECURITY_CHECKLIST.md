# 🔒 KeLiva Security Deployment Checklist

## Pre-Deployment Security Setup

### 1. Environment Variables
- [ ] Generate strong SECRET_KEY (32+ characters)
- [ ] Generate strong JWT_SECRET (32+ characters)  
- [ ] Set production DATABASE_URL
- [ ] Configure ALLOWED_ORIGINS (no wildcards in production)
- [ ] Set ALLOWED_HOSTS to your domains only
- [ ] Add your GROQ_API_KEY
- [ ] Set DEBUG_MODE=false

### 2. Database Security
- [ ] Use PostgreSQL in production (not SQLite)
- [ ] Enable SSL connections (`sslmode=require`)
- [ ] Use strong database passwords
- [ ] Limit database user permissions
- [ ] Enable connection pooling

### 3. API Security
- [ ] Enable rate limiting
- [ ] Implement JWT authentication
- [ ] Add request logging
- [ ] Sanitize all user inputs
- [ ] Use parameterized queries only

## Railway Deployment Security

### 1. Environment Variables Setup
```bash
# Set secure environment variables
railway variables set SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
railway variables set JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
railway variables set GROQ_API_KEY=your-actual-groq-key
railway variables set ALLOWED_ORIGINS=https://your-frontend.vercel.app
railway variables set DEBUG_MODE=false
```

### 2. Database Configuration
```bash
# Railway will provide DATABASE_URL automatically for PostgreSQL
railway add postgresql
```

### 3. Domain Security
- [ ] Use custom domain with SSL
- [ ] Enable HSTS headers
- [ ] Configure proper CORS origins

## Vercel Frontend Security

### 1. Environment Variables
```bash
# Set frontend environment variables
vercel env add VITE_API_URL production
# Enter: https://your-backend.railway.app

vercel env add VITE_ENABLE_CSP production
# Enter: true

vercel env add VITE_DEBUG_MODE production  
# Enter: false
```

### 2. Security Headers
Add to `vercel.json`:
```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options", 
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

## Post-Deployment Security

### 1. SSL/TLS
- [ ] Verify HTTPS is working
- [ ] Check SSL certificate validity
- [ ] Test HTTP to HTTPS redirect

### 2. Security Testing
- [ ] Test rate limiting (try rapid requests)
- [ ] Verify CORS is working correctly
- [ ] Test authentication endpoints
- [ ] Check for SQL injection vulnerabilities
- [ ] Test XSS protection

### 3. Monitoring Setup
- [ ] Set up UptimeRobot monitoring
- [ ] Configure security event logging
- [ ] Set up error alerting
- [ ] Monitor unusual traffic patterns

## Security Maintenance

### Weekly Tasks
- [ ] Review security logs
- [ ] Check for failed authentication attempts
- [ ] Monitor API usage patterns
- [ ] Update dependencies if needed

### Monthly Tasks  
- [ ] Rotate API keys
- [ ] Review and update CORS origins
- [ ] Check SSL certificate expiry
- [ ] Update security dependencies

### Quarterly Tasks
- [ ] Security audit and penetration testing
- [ ] Review and update security policies
- [ ] Update documentation
- [ ] Train team on security best practices

## Emergency Response

### If Security Breach Detected:
1. **Immediate Actions:**
   - [ ] Rotate all API keys and secrets
   - [ ] Check logs for unauthorized access
   - [ ] Temporarily disable affected endpoints
   - [ ] Notify users if data was compromised

2. **Investigation:**
   - [ ] Analyze attack vectors
   - [ ] Identify compromised data
   - [ ] Document incident details
   - [ ] Implement additional security measures

3. **Recovery:**
   - [ ] Patch vulnerabilities
   - [ ] Restore from clean backups if needed
   - [ ] Re-enable services gradually
   - [ ] Monitor for continued attacks

## Security Tools & Resources

### Automated Security Scanning
- **Snyk**: Dependency vulnerability scanning
- **OWASP ZAP**: Web application security testing
- **Bandit**: Python security linting

### Manual Testing Tools
- **Burp Suite**: Web application security testing
- **Postman**: API security testing
- **curl**: Command-line HTTP testing

### Security Headers Testing
- **securityheaders.com**: Test security headers
- **ssllabs.com**: SSL/TLS configuration testing

## Compliance & Best Practices

### Data Protection
- [ ] Implement data encryption at rest
- [ ] Use HTTPS for all communications
- [ ] Minimize data collection
- [ ] Implement data retention policies

### Access Control
- [ ] Use principle of least privilege
- [ ] Implement role-based access control
- [ ] Regular access reviews
- [ ] Strong password policies

### Incident Response
- [ ] Document incident response procedures
- [ ] Regular security training
- [ ] Backup and recovery testing
- [ ] Security contact information

---

## 🚨 Critical Security Reminders

1. **NEVER commit secrets to Git**
2. **Always use HTTPS in production**
3. **Keep dependencies updated**
4. **Monitor security logs regularly**
5. **Test security measures regularly**

## Quick Security Verification Commands

```bash
# Test API security
curl -H "Content-Type: application/json" https://your-api.railway.app/api/health

# Test rate limiting
for i in {1..100}; do curl https://your-api.railway.app/api/test; done

# Check security headers
curl -I https://your-frontend.vercel.app

# Test CORS
curl -H "Origin: https://malicious-site.com" https://your-api.railway.app/api/test
```

**Remember: Security is an ongoing process, not a one-time setup!** 🛡️