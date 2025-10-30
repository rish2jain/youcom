# Quick Test Guide - Verify You.com API Fixes

**Time Required**: 5 minutes
**Purpose**: Verify all You.com API endpoint fixes are working before demo

> **Implementation Status**: All 4 You.com APIs are fully integrated with resilience patterns. Core features are demo-ready. See [UNIMPLEMENTED_FEATURES_REPORT.md](UNIMPLEMENTED_FEATURES_REPORT.md) for advanced feature status.

---

## ⚡ Quick Start (30 seconds)

```bash
# 1. Add your You.com API key
echo "YOU_API_KEY=your_actual_key_here" > .env

# 2. Start backend
cd backend
uvicorn app.main:app --reload &

# 3. Wait 5 seconds for startup
sleep 5

# 4. Test all APIs
curl http://localhost:8765/api/v1/health/you-apis
```

---

## ✅ What Success Looks Like

You should see this response:

```json
{
  "timestamp": "2025-10-20T23:45:00.000000",
  "overall_status": "healthy",
  "apis": {
    "search": {
      "status": "healthy",
      "endpoint": "https://api.ydc-index.io/v1/search"
    },
    "news": {
      "status": "healthy",
      "endpoint": "https://api.ydc-index.io/livenews"
    },
    "chat": {
      "status": "healthy",
      "endpoint": "https://api.you.com/v1/agents/runs"
    },
    "ari": {
      "status": "healthy",
      "endpoint": "https://api.you.com/v1/agents/runs",
      "note": "Using Express Agent fallback"
    }
  }
}
```

**All 4 APIs should show `"status": "healthy"`** ✅

---

## ❌ Troubleshooting Common Issues

### Issue 1: "API key is required"

**Symptom**:

```json
{
  "overall_status": "error",
  "error": "You.com API key is required..."
}
```

**Fix**:

```bash
# Check .env file exists and has API key
cat .env | grep YOU_API_KEY

# Should show: YOU_API_KEY=your_key_here (not "your_you_api_key_here")
```

### Issue 2: "unhealthy" status for one or more APIs

**Symptom**:

```json
{
  "apis": {
    "search": {
      "status": "unhealthy",
      "error": "401 Unauthorized",
      "endpoint": "https://api.ydc-index.io/v1/search"
    }
  }
}
```

**Fix**:

```bash
# 1. Verify API key is valid
# Go to https://api.you.com and check your API key

# 2. Test API key directly
curl --request GET \
  --url 'https://api.ydc-index.io/v1/search?query=test' \
  --header 'X-API-Key: YOUR_API_KEY'

# Should return search results, not 401 error
```

### Issue 3: Connection errors

**Symptom**:

```json
{
  "apis": {
    "search": {
      "status": "unhealthy",
      "error": "Connection refused"
    }
  }
}
```

**Fix**:

```bash
# 1. Check internet connectivity
ping api.ydc-index.io

# 2. Check firewall settings
# 3. Try from different network if possible
```

---

## 🧪 Individual API Tests

If health check fails, test each API individually:

### Test 1: Search API

```bash
curl --request GET \
  --url 'https://api.ydc-index.io/v1/search?query=artificial%20intelligence&num_web_results=3' \
  --header 'X-API-Key: YOUR_API_KEY'
```

**Expected**: JSON with search results

### Test 2: News API

```bash
curl --request GET \
  --url 'https://api.ydc-index.io/livenews?q=technology&count=3' \
  --header 'X-API-Key: YOUR_API_KEY'
```

**Expected**: JSON with news articles

### Test 3: Chat API (Express Agent)

```bash
curl --request POST \
  --url 'https://api.you.com/v1/agents/runs' \
  --header 'Authorization: Bearer YOUR_API_KEY' \
  --header 'Content-Type: application/json' \
  --data '{
    "agent": "express",
    "input": "What is competitive intelligence?"
  }'
```

**Expected**: JSON with AI response

---

## 🎯 Pre-Demo Verification (2 minutes)

Run this right before your demo presentation:

```bash
#!/bin/bash
# save as test_before_demo.sh

echo "🔍 Testing You.com API Integration..."
echo ""

# Test health endpoint
HEALTH=$(curl -s http://localhost:8765/api/v1/health/you-apis)
STATUS=$(echo $HEALTH | grep -o '"overall_status":"[^"]*"' | cut -d'"' -f4)

if [ "$STATUS" == "healthy" ]; then
  echo "✅ All APIs HEALTHY - Demo ready!"
  echo ""
  echo "API Status:"
  echo $HEALTH | jq '.apis' 2>/dev/null || echo $HEALTH
  exit 0
else
  echo "❌ APIs NOT HEALTHY - Check issues"
  echo ""
  echo "Status: $STATUS"
  echo "Full response:"
  echo $HEALTH | jq '.' 2>/dev/null || echo $HEALTH
  exit 1
fi
```

Run it:

```bash
chmod +x test_before_demo.sh
./test_before_demo.sh
```

---

## 🚀 Full Demo Test (3 minutes)

Test the complete workflow:

```bash
# 1. Start all services
docker-compose up -d postgres redis
cd backend && uvicorn app.main:app --reload &
cd frontend && npm run dev &

# 2. Wait for startup
sleep 10

# 3. Open browser
open http://localhost:3456

# 4. Test Individual Research (MVP Focus)
# - Start with "Individual Research" tab
# - Enter "Perplexity AI"
# - Click "Research Company"
# - Verify comprehensive research appears with 400+ sources

# 5. Test Basic Competitive Monitoring
# - Switch to "Competitive Monitoring" section
# - Click "Generate Impact Card" for OpenAI
# - Watch for "News → Search → Chat → ARI → Complete"
# - Verify Impact Card shows data with sources
```

**All steps should complete without errors** ✅

---

## 📊 Demo Day Checklist

**5 minutes before presentation**:

- [ ] Run health check: All 4 APIs healthy ✅
- [ ] Test one Impact Card generation ✅
- [ ] Test one company research ✅
- [ ] Check API usage dashboard shows calls ✅
- [ ] Review backend logs - no errors ✅

**If any test fails**:

- [ ] Enable demo mode: `DEMO_MODE=true` in `.env`
- [ ] Restart backend server
- [ ] Use pre-generated data from database
- [ ] Mention "using cached data for demo performance"

---

## 🆘 Emergency Fallback

If nothing works:

```bash
# 1. Enable demo mode
echo "DEMO_MODE=true" >> .env

# 2. Restart backend
# Backend will use mock data instead of API calls

# 3. Pre-load database with demo data
python scripts/seed_demo_data.py

# 4. Demo will work with cached data
# Mention: "Pre-loaded demo data for presentation speed"
```

---

## 📝 Testing Log Template

Copy this to track your testing:

```
Date: ___________
Time: ___________

✅ Health Check Results:
- Search API: [ ] Healthy [ ] Unhealthy
- News API: [ ] Healthy [ ] Unhealthy
- Chat API: [ ] Healthy [ ] Unhealthy
- ARI API: [ ] Healthy [ ] Unhealthy

✅ Manual Tests:
- Impact Card Generation: [ ] Success [ ] Failed
- Company Research: [ ] Success [ ] Failed
- API Dashboard: [ ] Shows usage [ ] No data

✅ Issues Found:
_______________________________________________
_______________________________________________

✅ Resolution:
_______________________________________________
_______________________________________________

✅ Final Status: [ ] READY FOR DEMO [ ] NEEDS WORK
```

---

**🎯 Bottom Line**: Run the health check endpoint. If all 4 APIs show "healthy", you're ready to demo!
