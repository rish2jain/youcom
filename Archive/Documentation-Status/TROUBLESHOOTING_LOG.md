# Troubleshooting Log - Demo Recording Script

## Issue: ERR_CONNECTION_REFUSED (October 31, 2025)

### Problem
Recording script failed with connection error:
```
⚠️  Navigation failed: net::ERR_CONNECTION_REFUSED at http://localhost:3456
❌ Failed to load application
```

### Root Cause Analysis
1. **Incorrect Port Configuration**: Script was configured to use port 3456
2. **Actual Server Port**: Development server runs on port 3000
3. **Port Mismatch**: `record-demo.js` default: 3456 vs Next.js default: 3000

### Diagnosis Steps
```bash
# Check what's running on expected port
lsof -i :3456  # Nothing found

# Check standard Next.js port
lsof -i :3000  # Found Node.js process

# Verify server responds
curl http://localhost:3000  # HTTP 200 OK
```

### Solution Applied

#### Fix 1: Updated Default Port
Changed default URL in `scripts/record-demo.js`:
```javascript
// Before
this.baseUrl = options.url || "http://localhost:3456?skip-onboarding=true";

// After
this.baseUrl = options.url || "http://localhost:3000?skip-onboarding=true";
```

#### Fix 2: Increased Navigation Timeout
Next.js applications need more time to fully load:
```javascript
// Before
await this.page.goto(url, {
  waitUntil: "networkidle2",
  timeout: 15000,
});

// After
await this.page.goto(url, {
  waitUntil: "domcontentloaded",
  timeout: 30000,
});
await this.wait(3); // Extra time for full render
```

#### Fix 3: Updated Documentation
Updated all port references in `DEMO_RECORDING_GUIDE.md`:
- Changed `localhost:3456` → `localhost:3000`

### Verification
```bash
# Test with quick demo
npm run record:quick

# Results
✅ Chrome launched successfully
✅ Loaded: Enterprise CIA Dashboard
✅ Recording started
🎙️  Narration markers working
📸 Screenshot capture working
```

### Lessons Learned
1. **Port Consistency**: Always verify the actual port the dev server uses
2. **Timeout Values**: Next.js apps need 20-30s for initial load, not 15s
3. **Wait Strategy**: Use `domcontentloaded` + extra wait instead of `networkidle2`
4. **Documentation Sync**: Update docs when changing default configurations

### Prevention
- Add port detection to script startup
- Show warning if expected port is not responding
- Add `--port` flag as alternative to `--url`

### Future Improvements
```javascript
// Potential enhancement: Auto-detect running server
async detectServerPort() {
  const portsToCheck = [3000, 3001, 3456, 8080];
  for (const port of portsToCheck) {
    try {
      const response = await fetch(`http://localhost:${port}`);
      if (response.ok) return port;
    } catch (e) {}
  }
  return null;
}
```

## Status: ✅ RESOLVED

**Date:** October 31, 2025
**Time to Resolution:** ~15 minutes
**Impact:** None (caught in testing)
**Affected Users:** None (pre-release)
