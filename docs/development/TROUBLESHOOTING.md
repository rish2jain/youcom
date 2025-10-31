# Enterprise CIA - Troubleshooting Guide

**Last Updated**: October 31, 2025  
**Consolidated from**: Multiple troubleshooting documents

## 🚨 Common Issues & Solutions

### You.com API Issues

#### Problem: API calls failing with 401 Unauthorized

**Symptoms**:

- Health check shows APIs as "unhealthy"
- Error: "authentication failed"
- 401 status codes in logs

**Solutions**:

1. **Verify API Key**:

   ```bash
   # Check if API key is set
   echo $YOU_API_KEY

   # Test API key directly
   curl -H "X-API-Key: $YOU_API_KEY" \
        "https://api.ydc-index.io/livenews?q=test&count=1"
   ```

2. **Check Environment File**:

   ```bash
   # Ensure .env file exists and has correct key
   cat .env | grep YOU_API_KEY

   # Restart backend after changing .env
   cd backend
   uvicorn app.main:app --reload
   ```

3. **Verify Key Format**:
   ```bash
   # API key should be alphanumeric string
   # No quotes, spaces, or special characters
   YOU_API_KEY=abc123def456  # Correct
   YOU_API_KEY="abc123def456"  # Wrong - remove quotes
   ```

#### Problem: API calls failing with 404 Not Found

**Symptoms**:

- Error: "404 Client Error: Not Found"
- Endpoints returning 404

**Solutions**:

1. **Check Endpoint URLs** (Common cause):

   ```python
   # Correct endpoints
   you_search_url = "https://api.ydc-index.io/v1/search"
   you_news_url = "https://api.ydc-index.io/livenews"
   you_chat_url = "https://api.you.com/v1/agents/runs"

   # Wrong endpoints (will cause 404)
   # "https://api.you.com/v1/news"  # Don't use
   # "https://api.you.com/v1/search"  # Don't use
   ```

2. **Verify Configuration**:
   ```bash
   # Check backend config
   cd backend
   python -c "from app.config import settings; print(settings.you_search_url)"
   ```

#### Problem: API calls timing out

**Symptoms**:

- Requests taking too long
- Timeout errors in logs
- WebSocket connections dropping

**Solutions**:

1. **Check Network Connection**:

   ```bash
   # Test direct connectivity
   curl -I https://api.you.com
   curl -I https://api.ydc-index.io
   ```

2. **Adjust Timeouts**:

   ```python
   # In backend/app/services/you_client.py
   timeouts = {
       "news": 30.0,      # Standard timeout
       "search": 30.0,    # Standard timeout
       "chat": 60.0,      # Longer for AI processing
       "ari": 120.0       # Longest for comprehensive reports
   }
   ```

3. **Enable Demo Mode** (temporary):
   ```bash
   # In .env file
   DEMO_MODE=true
   ```

### Database Issues

#### Problem: Database connection errors

**Symptoms**:

- "connection refused" errors
- Backend won't start
- Migration failures

**Solutions**:

1. **Use SQLite** (simplest):

   ```bash
   # Remove DATABASE_URL from .env
   # Backend will use SQLite automatically
   ```

2. **Start PostgreSQL**:

   ```bash
   # Using Docker
   docker-compose up postgres -d

   # Check if running
   docker ps | grep postgres
   ```

3. **Fix Connection String**:

   ```bash
   # Correct format in .env
   DATABASE_URL=postgresql://user:password@localhost:5432/cia_db

   # Test connection
   psql $DATABASE_URL -c "SELECT 1;"
   ```

#### Problem: Migration failures

**Symptoms**:

- "table already exists" errors
- Alembic revision conflicts
- Schema mismatch errors

**Solutions**:

1. **Reset Database**:

   ```bash
   cd backend

   # Drop and recreate database
   alembic downgrade base
   alembic upgrade head
   ```

2. **Fresh Start**:

   ```bash
   # Delete SQLite file (if using SQLite)
   rm cia.db

   # Run migrations
   cd backend
   alembic upgrade head
   ```

### Frontend Issues

#### Problem: Frontend won't start

**Symptoms**:

- npm run dev fails
- Port already in use
- Module not found errors

**Solutions**:

1. **Check Node Version**:

   ```bash
   node --version  # Should be 18+
   npm --version   # Should be 9+
   ```

2. **Clear Cache and Reinstall**:

   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Use Different Port**:
   ```bash
   npm run dev -- --port 3457
   ```

#### Problem: API calls from frontend failing

**Symptoms**:

- Network errors in browser console
- CORS errors
- Connection refused

**Solutions**:

1. **Verify Backend is Running**:

   ```bash
   curl http://localhost:8765/health
   ```

2. **Check API Base URL**:

   ```typescript
   // In lib/api.ts - should point to backend
   const backendApi = axios.create({
     baseURL: "http://localhost:8765", // Correct
     // baseURL: "https://api.you.com",  // Wrong - don't call directly
   });
   ```

3. **Check Browser Console**:
   - Open Developer Tools (F12)
   - Look for network errors
   - Verify requests go to localhost:8765, not external APIs

### WebSocket Issues

#### Problem: Real-time updates not working

**Symptoms**:

- Progress indicators not updating
- No live API orchestration feedback
- WebSocket connection errors

**Solutions**:

1. **Check Redis Connection**:

   ```bash
   # Test Redis
   redis-cli ping  # Should return "PONG"

   # Or use Docker
   docker-compose up redis -d
   ```

2. **Verify WebSocket Endpoint**:

   ```bash
   # Test WebSocket connection
   curl --include \
        --no-buffer \
        --header "Connection: Upgrade" \
        --header "Upgrade: websocket" \
        --header "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
        --header "Sec-WebSocket-Version: 13" \
        http://localhost:8765/ws
   ```

3. **Use In-Memory Cache** (fallback):
   ```bash
   # Remove REDIS_URL from .env
   # Backend will use in-memory cache
   ```

### Performance Issues

#### Problem: Slow API responses

**Symptoms**:

- Long wait times for results
- Timeouts during processing
- Poor user experience

**Solutions**:

1. **Check Cache Hit Rate**:

   ```bash
   # View cache statistics
   curl http://localhost:8765/api/v1/analytics/api-usage
   ```

2. **Optimize Cache Settings**:

   ```python
   # Adjust TTLs in backend/app/config.py
   news_cache_ttl: int = 900      # 15 minutes
   search_cache_ttl: int = 3600   # 1 hour
   ari_cache_ttl: int = 604800    # 7 days
   ```

3. **Enable Parallel Processing**:
   ```python
   # Ensure async/await patterns are used
   # Check backend/app/services/you_client.py
   ```

### Integration Issues

#### Problem: Notion integration failing

**Symptoms**:

- Notion sync errors
- Authentication failures
- Database creation errors

**Solutions**:

1. **Verify Notion API Key**:

   ```bash
   # Check if key is set
   echo $NOTION_API_KEY

   # Test Notion API
   curl -H "Authorization: Bearer $NOTION_API_KEY" \
        -H "Notion-Version: 2022-06-28" \
        https://api.notion.com/v1/users/me
   ```

2. **Check Integration Status**:
   ```bash
   curl http://localhost:8765/api/v1/integrations/notion/test
   ```

#### Problem: Salesforce integration failing

**Symptoms**:

- OAuth errors
- CRM sync failures
- Authentication timeouts

**Solutions**:

1. **Verify Salesforce Credentials**:

   ```bash
   # Check environment variables
   echo $SALESFORCE_CLIENT_ID
   echo $SALESFORCE_CLIENT_SECRET
   ```

2. **Test Connection**:
   ```bash
   curl http://localhost:8765/api/v1/integrations/salesforce/test
   ```

## 🔧 Development Issues

### Problem: Tests failing

**Symptoms**:

- pytest failures
- Import errors
- Database test issues

**Solutions**:

1. **Run Tests with Proper Environment**:

   ```bash
   # Backend tests
   cd backend
   pytest tests/ -v

   # Frontend tests
   npm test
   ```

2. **Fix Test Database**:
   ```bash
   # Use test database
   export DATABASE_URL=postgresql://test:test@localhost:5432/test_cia
   pytest tests/
   ```

### Problem: Code formatting issues

**Symptoms**:

- Linting errors
- Style inconsistencies
- Pre-commit failures

**Solutions**:

1. **Run Formatters**:

   ```bash
   # Python formatting
   cd backend
   black app/ tests/
   isort app/ tests/

   # JavaScript formatting
   npm run lint -- --fix
   ```

2. **Install Pre-commit Hooks**:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## 🚨 Emergency Procedures

### Demo Day Issues

#### If APIs are completely down:

1. **Enable Demo Mode**:

   ```bash
   # In .env
   DEMO_MODE=true
   ```

2. **Use Cached Data**:

   ```bash
   # Show pre-generated results
   curl http://localhost:8765/api/v1/impact/?demo=true
   ```

3. **Fallback to Screenshots**:
   - Have backup slides ready
   - Show static results
   - Explain the architecture

#### If Frontend crashes:

1. **Quick Restart**:

   ```bash
   # Kill and restart
   pkill -f "npm run dev"
   npm run dev
   ```

2. **Use Backup Browser**:
   - Have multiple browser tabs open
   - Use different browser as backup

#### If Backend crashes:

1. **Quick Restart**:

   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8765
   ```

2. **Check Logs**:
   ```bash
   # View recent errors
   tail -f backend/logs/app.log
   ```

## 📊 Diagnostic Commands

### System Health Check

```bash
# Complete system status
curl http://localhost:8765/health

# You.com API status
curl http://localhost:8765/api/v1/health/you-apis

# Database status
curl http://localhost:8765/api/v1/health/database

# Cache status
curl http://localhost:8765/api/v1/health/cache
```

### Performance Monitoring

```bash
# API usage statistics
curl http://localhost:8765/api/v1/analytics/api-usage

# Response time metrics
curl http://localhost:8765/api/v1/analytics/performance

# Error rate monitoring
curl http://localhost:8765/api/v1/analytics/errors
```

### Log Analysis

```bash
# Backend logs
tail -f backend/logs/app.log

# API call logs
grep "you_api" backend/logs/app.log

# Error logs only
grep "ERROR" backend/logs/app.log
```

## 🔍 Debug Mode

### Enable Verbose Logging

```bash
# In .env file
LOG_LEVEL=DEBUG
VERBOSE_API_LOGGING=true

# Restart backend
cd backend
uvicorn app.main:app --reload
```

### Frontend Debug Mode

```bash
# Enable React debug mode
export NODE_ENV=development
npm run dev
```

### API Debug Mode

```python
# In backend/app/services/you_client.py
# Uncomment debug logging
logger.debug(f"API request: {method} {url}")
logger.debug(f"API response: {response.status_code}")
```

## 📞 Getting Help

### Self-Diagnosis Checklist

Before asking for help:

- [ ] Check system health endpoints
- [ ] Verify environment variables are set
- [ ] Review recent logs for errors
- [ ] Test individual components
- [ ] Try demo mode as fallback

### Information to Provide

When reporting issues:

1. **Error Message**: Exact error text
2. **Steps to Reproduce**: What you were doing
3. **Environment**: OS, Python/Node versions
4. **Logs**: Relevant log entries
5. **Configuration**: Sanitized .env file

### Quick Support Commands

```bash
# Generate diagnostic report
curl http://localhost:8765/api/v1/debug/system-info

# Export logs
tail -100 backend/logs/app.log > debug-logs.txt

# Check configuration
python -c "from backend.app.config import settings; print(settings.dict())"
```

---

**Remember**: Most issues are configuration-related. Check environment variables and API keys first!

**Last Updated**: October 31, 2025  
**Need More Help?** Check other documentation in the [docs](../README.md) directory
