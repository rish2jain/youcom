# Chrome DevTools MCP Testing Plan

## Comprehensive Testing Strategy for You.com Intelligence Platform

Based on [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp), this document outlines a detailed testing approach for the web application.

---

## Table of Contents

1. [Overview](#overview)
2. [Setup & Configuration](#setup--configuration)
3. [Testing Categories](#testing-categories)
4. [Test Implementation Strategy](#test-implementation-strategy)
5. [Comprehensive Feature Testing Matrix](#comprehensive-feature-testing-matrix)
   - [Page-by-Page Testing](#page-by-page-testing)
   - [Component Testing Matrix](#component-testing-matrix)
   - [Feature-Specific Testing](#feature-specific-testing)
   - [Complete Workflow Testing](#complete-workflow-testing)
   - [API Endpoint Testing Matrix](#api-endpoint-testing-matrix)
   - [Responsive Design Testing](#responsive-design-testing)
   - [Cross-Browser Testing](#cross-browser-testing)
   - [Security Testing](#security-testing)
   - [Load & Stress Testing](#load--stress-testing)
6. [Specific Test Scenarios](#specific-test-scenarios)
7. [Performance Testing](#performance-testing)
8. [Accessibility Testing](#accessibility-testing)
9. [Integration Testing](#integration-testing)
10. [CI/CD Integration](#cicd-integration)
11. [Test Execution and Reporting](#test-execution-and-reporting)
12. [Test Coverage Summary](#test-coverage-summary)

---

## Overview

### What is Chrome DevTools MCP?

Chrome DevTools MCP is a Model Context Protocol server that provides programmatic access to Chrome DevTools Protocol, enabling:

- **Browser Automation**: Full control over Chrome instances
- **Performance Monitoring**: Core Web Vitals, performance traces, and metrics
- **Network Analysis**: Request/response inspection, latency tracking
- **Element Interaction**: Click, fill forms, navigate, take screenshots
- **Console Debugging**: Capture console messages and errors
- **Accessibility Testing**: Snapshot accessibility tree

### Why Use It for Testing?

1. **Real Browser Environment**: Tests run in actual Chrome, not headless simulations
2. **Performance Metrics**: Built-in Core Web Vitals monitoring
3. **Network Insights**: Track API calls, latency, and errors
4. **Visual Regression**: Screenshot comparison capabilities
5. **Accessibility Compliance**: Built-in a11y tree inspection

### Testing Approach: Direct Tool Execution

**IMPORTANT**: This testing plan emphasizes **direct execution** using Chrome DevTools MCP tools rather than creating test scripts.

**Key Principles**:

- ✅ Use Chrome DevTools MCP tools directly via MCP client (e.g., Claude)
- ✅ Execute tests interactively with real-time feedback
- ✅ Generate reports from actual test execution results
- ❌ **DO NOT** create test scripts that only document steps
- ❌ **DO NOT** write code that doesn't execute tests

**Workflow**:

1. **Execute tests directly** using MCP tools (`navigate_page`, `click`, `take_snapshot`, etc.)
2. **Capture results** from actual tool executions
3. **Generate reports** based on real test results
4. **Document findings** in markdown reports (not scripts)

**Example Direct Execution**:

```
✅ navigate_page({ url: 'http://localhost:3456/dashboard' })
✅ take_snapshot({ verbose: true })
✅ list_network_requests()
✅ performance_start_trace({ reload: true })
✅ performance_stop_trace()
→ Generate report from actual results
```

This approach provides:

- Real-time test execution
- Immediate feedback on failures
- Actual performance metrics
- Real network request data
- Genuine accessibility snapshots

---

## Setup & Configuration

### 1. Install Chrome DevTools MCP

```bash
npm install -g chrome-devtools-mcp
```

### 2. MCP Server Configuration

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "chrome-devtools-mcp@latest",
        "--headless=true",
        "--isolated=true",
        "--viewport=1920x1080",
        "--categoryPerformance=true",
        "--categoryNetwork=true"
      ]
    }
  }
}
```

### 3. Start Frontend and Backend Services

**IMPORTANT**: Before running tests, ensure both frontend and backend services are running.

#### Start Backend Service

```bash
# From project root directory
cd backend

# Install Python dependencies (if not already installed)
pip install -r requirements.txt

# Start backend server
# Using default port 8765
uvicorn app.main:app --reload --host 0.0.0.0 --port 8765

# Option: Using socket app (if using WebSocket features)
uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8765
```

**Verify backend is running:**

```bash
# Check health endpoint
curl http://localhost:8765/health

# Or check API docs
curl http://localhost:8765/docs
```

#### Start Frontend Service

```bash
# From project root directory (if not already running)

# Install Node.js dependencies (if not already installed)
npm install

# Start frontend development server
npm run dev

# Frontend will be available at http://localhost:3456
# (or the port shown in the terminal output)
```

**Verify frontend is running:**

```bash
# Check frontend
curl http://localhost:3456
```

#### Quick Service Check Script

```bash
#!/bin/bash
# Check if services are running

echo "Checking services..."

# Check backend
if curl -f http://localhost:8765/health > /dev/null 2>&1; then
  echo "✅ Backend is running on http://localhost:8765"
else
  echo "❌ Backend is not running"
fi

# Check frontend
if curl -f http://localhost:3456 > /dev/null 2>&1; then
  echo "✅ Frontend is running on http://localhost:3456"
else
  echo "❌ Frontend is not running"
fi
```

**Note**: Tests require both services to be running for full functionality. Some tests (performance, accessibility) can run with only the frontend, but API integration tests require the backend.

### 4. Test Environment Setup

```bash
# Create test configuration
mkdir -p tests/chrome-devtools
cd tests/chrome-devtools
```

### 5. Environment Variables

Create `.env.test`:

```bash
# Test environment
NEXT_PUBLIC_API_URL=http://localhost:8765
BACKEND_URL=http://localhost:8765
FRONTEND_URL=http://localhost:3456

# Test credentials (if needed)
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=test123
```

---

## Testing Categories

### 1. **Functional Testing**

- User workflows and interactions
- Form submissions
- Navigation flows
- Data display and updates

### 2. **Performance Testing**

- Page load times
- Core Web Vitals (LCP, FID, CLS)
- API response times
- Resource loading optimization

### 3. **Network Testing**

- API endpoint availability
- Request/response validation
- Error handling
- Rate limiting compliance

### 4. **Accessibility Testing**

- ARIA compliance
- Keyboard navigation
- Screen reader compatibility
- Color contrast validation

### 5. **Visual Regression Testing**

- Screenshot comparisons
- Layout consistency
- Responsive design validation

### 6. **Integration Testing**

- Frontend-backend communication
- Real-time updates (WebSocket)
- Data persistence
- Authentication flows

---

## Test Implementation Strategy

### Direct Execution Workflow

**CRITICAL**: All tests should be executed directly using Chrome DevTools MCP tools. Do not create scripts that only document steps.

**Standard Test Execution Pattern**:

1. **Navigate to Page**

   ```typescript
   navigate_page({ url: "http://localhost:3456/dashboard", timeout: 15000 });
   ```

2. **Capture Initial State**

   ```typescript
   take_snapshot({ verbose: true });
   list_console_messages({ types: ["error", "warn"] });
   list_network_requests({ includePreservedRequests: true });
   ```

3. **Perform Actions**

   ```typescript
   click({ uid: "button-uid" });
   fill_form({ elements: [{ uid: "input-uid", value: "test" }] });
   wait_for({ text: "Expected text", timeout: 5000 });
   ```

4. **Capture Results**

   ```typescript
   take_snapshot();
   list_network_requests({ resourceTypes: ["fetch", "xhr"] });
   take_screenshot({ fullPage: true });
   ```

5. **Performance Testing**

   ```typescript
   performance_start_trace({ reload: true, autoStop: false });
   navigate_page({ url: "http://localhost:3456/page" });
   wait_for({ text: "Page loaded", timeout: 10000 });
   performance_stop_trace();
   performance_analyze_insight({ insightName: "LCPBreakdown" });
   ```

6. **Generate Report**
   - Create markdown report with actual results
   - Include metrics, screenshots, and findings
   - Document failures and recommendations

### Phase 1: Foundation Tests

#### 1.1 Page Load Tests

**Execute directly using**:

- `navigate_page()` - Load each page
- `list_console_messages()` - Check for errors
- `list_network_requests()` - Validate API calls
- `take_snapshot()` - Verify page structure

**Example Execution**:

```typescript
// Navigate to page
navigate_page({ url: "http://localhost:3456/dashboard" });

// Check for errors
const consoleErrors = list_console_messages({ types: ["error"] });
// Verify no errors found

// Check network requests
const requests = list_network_requests();
// Verify API calls succeeded

// Verify page loaded
const snapshot = take_snapshot();
// Check for expected content
```

#### 1.2 Navigation Tests

**Execute directly using**:

- `navigate_page()` - Navigate between pages
- `wait_for()` - Wait for page content
- `take_snapshot()` - Verify URL changes

**Example Execution**:

```typescript
// Navigate between pages
navigate_page({ url: "http://localhost:3456/dashboard" });
wait_for({ text: "Dashboard", timeout: 10000 });
navigate_page({ url: "http://localhost:3456/research" });
wait_for({ text: "Research", timeout: 10000 });
// Verify navigation successful
```

#### 1.3 Core Component Tests

**Execute directly using**:

- `take_snapshot()` - Find component UIDs
- `click()` - Interact with components
- `list_network_requests()` - Verify API calls
- `take_screenshot()` - Visual verification

### Phase 2: Interactive Tests

#### 2.1 Form Interactions

**Execute directly using**:

- `click()` - Open forms
- `fill_form()` - Fill form fields
- `click()` - Submit forms
- `wait_for()` - Wait for success/error messages
- `list_network_requests()` - Verify form submission API calls

#### 2.2 Data Operations

**Execute directly using**:

- `click()` - Interact with data controls
- `fill_form()` - Update data
- `take_snapshot()` - Verify data changes
- `list_network_requests()` - Verify CRUD operations

### Phase 3: Performance Tests

#### 3.1 Page Load Performance

**Execute directly using**:

- `performance_start_trace()` - Begin performance monitoring
- `navigate_page()` - Load pages
- `wait_for()` - Wait for page interactive
- `performance_stop_trace()` - End monitoring
- `performance_analyze_insight()` - Analyze Core Web Vitals

**Example Execution**:

```typescript
// Start performance trace
performance_start_trace({ reload: true, autoStop: false });

// Navigate to page
navigate_page({ url: "http://localhost:3456/dashboard" });
wait_for({ text: "Dashboard", timeout: 10000 });

// Stop trace and analyze
performance_stop_trace();

// Get metrics
const lcp = performance_analyze_insight({ insightName: "LCPBreakdown" });
const cls = performance_analyze_insight({ insightName: "CLSBreakdown" });

// Verify thresholds
// LCP < 2500ms, CLS < 0.1
```

#### 3.2 API Performance

**Execute directly using**:

- `list_network_requests()` - Capture API requests
- `get_network_request()` - Inspect specific requests
- `evaluate_script()` - Analyze response times

### Phase 4: Advanced Tests

#### 4.1 Real-time Features

**Execute directly using**:

- `list_network_requests()` - Monitor WebSocket connections
- `wait_for()` - Wait for real-time updates
- `take_snapshot()` - Verify UI updates

#### 4.2 Error Scenarios

**Execute directly using**:

- `navigate_page()` - Trigger error conditions
- `list_console_messages()` - Capture error messages
- `list_network_requests()` - Monitor failed requests
- `take_snapshot()` - Verify error UI

---

## Specific Test Scenarios

### Scenario 1: Watchlist Management Flow

**Objective**: Test complete watchlist CRUD operations

**Steps**:

1. Navigate to `/dashboard`
2. Take snapshot to verify initial state
3. Click "Add Competitor" button
4. Fill form with test data:
   - Competitor name: "TestCorp"
   - Keywords: "AI, ML, SaaS"
   - Description: "Test description"
5. Submit form
6. Verify new item appears in list
7. Capture network requests to verify API call
8. Take screenshot for visual validation
9. Test edit functionality
10. Test delete functionality

**Chrome DevTools MCP Tools Used**:

- `navigate_page` - Navigate to dashboard
- `take_snapshot` - Verify UI state
- `fill_form` - Input form data
- `click` - Submit buttons
- `list_network_requests` - Verify API calls
- `take_screenshot` - Visual validation

**Expected Results**:

- Form submits successfully
- API returns 201 status
- Item appears in list immediately
- No console errors

---

### Scenario 2: Impact Card Generation

**Objective**: Test impact card generation workflow

**Steps**:

1. Navigate to `/research`
2. Start performance trace
3. Select competitor from watchlist
4. Click "Generate Impact Card"
5. Monitor progress indicators
6. Wait for completion
7. Verify impact card displays correctly
8. Check API usage metrics
9. Stop performance trace
10. Analyze performance data

**Chrome DevTools MCP Tools Used**:

- `navigate_page` - Navigate to research page
- `performance_start_trace` - Begin performance monitoring
- `click` - Trigger generation
- `wait_for` - Wait for completion message
- `list_network_requests` - Track API calls
- `take_snapshot` - Verify final state
- `performance_stop_trace` - End monitoring
- `performance_analyze_insight` - Analyze Core Web Vitals

**Expected Results**:

- Impact card generates within 30 seconds
- Multiple API calls executed (News, Search, Chat, ARI)
- LCP < 2.5s, FID < 100ms
- No failed API requests

---

### Scenario 3: API Integration Testing

**Objective**: Verify all API endpoints work correctly

**Test Endpoints**:

- `GET /api/v1/watch` - Watchlist retrieval
- `GET /api/v1/impact/` - Impact cards list
- `POST /api/v1/impact/generate` - Impact card generation
- `GET /api/v1/metrics/api-usage` - Usage metrics
- `GET /api/health` - Health check

**Steps**:

1. Navigate to each page that uses these endpoints
2. Use `list_network_requests` to capture API calls
3. Verify status codes (200, 201, etc.)
4. Check response times
5. Validate response structure
6. Test error scenarios (404, 500)

**Chrome DevTools MCP Tools Used**:

- `navigate_page` - Access pages
- `list_network_requests` - Monitor API calls
- `get_network_request` - Inspect specific requests
- `evaluate_script` - Validate response data

**Expected Results**:

- All endpoints return valid responses
- Response times < 1000ms for most endpoints
- Proper error handling for failures

---

### Scenario 4: Performance Benchmarking

**Objective**: Establish performance baselines

**Metrics to Track**:

- **LCP (Largest Contentful Paint)**: < 2.5s
- **FID (First Input Delay)**: < 100ms
- **CLS (Cumulative Layout Shift)**: < 0.1
- **TTI (Time to Interactive)**: < 3.5s
- **FCP (First Contentful Paint)**: < 1.8s

**Steps**:

1. Clear browser cache
2. Start performance trace with reload
3. Navigate to main pages:
   - Dashboard
   - Research
   - Analytics
   - Settings
4. Stop trace
5. Analyze each metric
6. Compare against thresholds
7. Generate performance report

**Chrome DevTools MCP Tools Used**:

- `performance_start_trace` - Begin with reload
- `navigate_page` - Test each page
- `performance_stop_trace` - End trace
- `performance_analyze_insight` - Get Core Web Vitals

**Expected Results**:

- All pages meet Core Web Vitals thresholds
- Consistent performance across pages
- Performance report generated

---

### Scenario 5: Accessibility Compliance

**Objective**: Ensure WCAG 2.1 AA compliance

**Checks**:

1. Take accessibility snapshot
2. Verify ARIA labels
3. Test keyboard navigation
4. Check color contrast
5. Validate semantic HTML

**Steps**:

1. Navigate to each major page
2. Use `take_snapshot` with `verbose=true`
3. Parse accessibility tree
4. Verify required ARIA attributes
5. Test keyboard-only navigation
6. Check focus indicators

**Chrome DevTools MCP Tools Used**:

- `take_snapshot` - Get a11y tree
- `evaluate_script` - Run a11y checks
- Keyboard navigation simulation

**Expected Results**:

- All interactive elements have ARIA labels
- Keyboard navigation works on all pages
- Focus indicators visible
- Color contrast meets WCAG AA standards

---

## Comprehensive Feature Testing Matrix

### Page-by-Page Testing

#### Page 1: Dashboard (`/dashboard`)

**Components to Test**:

- Header with navigation
- Sidebar navigation
- Intelligence Dashboard content
- Top Alerts section
- Recent Intelligence section
- Key Insights section
- Quick Actions section
- Breadcrumb navigation
- Notification center
- Floating chat widget

**Test Scenarios**:

1. **Dashboard Load Test**

   - Navigate to `/dashboard`
   - Verify all sections render
   - Check for console errors
   - Verify API calls complete
   - Take snapshot for accessibility

2. **Top Alerts Widget**

   - Verify alert cards display
   - Check alert severity indicators (HIGH, MEDIUM, LOW)
   - Test "View Full Analysis" links
   - Verify risk scores display correctly
   - Test alert timestamps

3. **Recent Intelligence Section**

   - Verify impact cards display
   - Test "View Report" links
   - Test "Share" buttons
   - Verify source count displays
   - Test card hover states

4. **Key Insights Widget**

   - Verify insight cards display
   - Check percentage indicators
   - Verify trend indicators
   - Test insight descriptions

5. **Quick Actions**

   - Test "Add Competitor" link
   - Test "Research New" link
   - Test "Go to Monitoring" link
   - Test "View Settings" link
   - Verify navigation works

6. **Dashboard Performance**
   - Measure LCP for dashboard
   - Check CLS during load
   - Monitor API call times
   - Verify caching works

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/dashboard" });
take_snapshot({ verbose: true });
list_console_messages({ types: ["error", "warn"] });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
performance_start_trace({ reload: true });
// Interact with widgets
click({ uid: "alert-card-uid" });
// Verify interactions
take_screenshot({ fullPage: true });
```

---

#### Page 2: Research (`/research`)

**Components to Test**:

- CompanyResearch component
- Search form
- Recent research list
- Research modal/detail view
- Export PDF functionality
- Share functionality
- Suggested companies widget
- Loading states
- Error states
- Empty states

**Test Scenarios**:

1. **Research Page Load**

   - Navigate to `/research`
   - Verify search form displays
   - Check for empty state if no research
   - Verify suggested companies show
   - Check console for errors

2. **Company Search Functionality**

   - Enter company name in search field
   - Click "Research Company" button
   - Verify loading state displays
   - Monitor API calls (Search API, ARI API)
   - Wait for completion
   - Verify results display

3. **Recent Research List**

   - Verify list displays correctly
   - Test pagination if present
   - Test clicking on research item
   - Verify research modal opens
   - Test closing modal

4. **Research Detail View**

   - Open research detail modal
   - Verify all sections display:
     - Company Overview
     - Key Findings
     - Research Report
     - Source Citations
     - API Usage Details
   - Test scrolling in modal
   - Test section navigation

5. **Export PDF Functionality**

   - Click "Export PDF" button
   - Verify download starts
   - Check PDF generation API call
   - Verify file downloads
   - Test error handling if API fails

6. **Share Functionality**

   - Click "Share" button
   - Verify share dialog opens
   - Test email input
   - Submit share form
   - Verify API call
   - Check success/error messages

7. **Suggested Companies Widget**

   - Verify companies display
   - Click suggested company
   - Verify search auto-fills
   - Test company name click
   - Verify URL parameter updates

8. **Error Handling**
   - Test invalid company names
   - Test API failures
   - Verify error messages display
   - Test retry functionality

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/research" });
take_snapshot({ verbose: true });
// Fill search form
fill_form({
  elements: [{ uid: "company-search-input-uid", value: "OpenAI" }],
});
click({ uid: "research-button-uid" });
wait_for({ text: "Research completed", timeout: 60000 });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
// Test interactions
click({ uid: "export-pdf-button-uid" });
click({ uid: "share-button-uid" });
fill_form({
  elements: [{ uid: "email-input-uid", value: "test@example.com" }],
});
take_screenshot({ fullPage: true });
```

---

#### Page 3: Monitoring (`/monitoring`)

**Components to Test**:

- WatchList component
- Competitor watchlist table
- Add competitor form
- Impact card generation
- PersonalPlaybooks component
- ActionTracker component
- Alert notifications
- Real-time updates (WebSocket)

**Test Scenarios**:

1. **Monitoring Page Load**

   - Navigate to `/monitoring`
   - Verify watchlist displays
   - Check for playbooks section
   - Verify action tracker displays
   - Check console for errors

2. **Watchlist Management**

   - Test "Add Competitor" button
   - Fill competitor form:
     - Competitor name
     - Keywords
     - Description
     - Risk threshold
   - Submit form
   - Verify item appears in list
   - Test edit functionality
   - Test delete functionality
   - Verify API calls

3. **Impact Card Generation**

   - Select competitor from watchlist
   - Click "Generate Impact Card"
   - Monitor progress indicators
   - Verify WebSocket updates
   - Wait for completion
   - Verify impact card displays
   - Check all impact card tabs:
     - Overview
     - Analysis
     - Evidence
     - Actions

4. **Personal Playbooks**

   - Verify playbooks list displays
   - Test "Create Playbook" button
   - Fill playbook form
   - Submit playbook
   - Verify playbook appears
   - Test playbook selection
   - Test playbook editing
   - Test playbook deletion

5. **Action Tracker**

   - Verify actions list displays
   - Test action completion
   - Test action priority changes
   - Test action filtering
   - Verify action status updates

6. **Real-time Updates**
   - Monitor WebSocket connections
   - Verify real-time notifications
   - Test alert delivery
   - Verify UI updates automatically

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/monitoring" });
take_snapshot({ verbose: true });
// Add competitor
click({ uid: "add-competitor-button-uid" });
fill_form({
  elements: [
    { uid: "competitor-name-uid", value: "Anthropic" },
    { uid: "keywords-uid", value: "Claude, LLM, AI" },
    { uid: "description-uid", value: "AI safety company" },
  ],
});
click({ uid: "submit-button-uid" });
wait_for({ text: "Anthropic", timeout: 5000 });
// Generate impact card
click({ uid: "generate-impact-button-uid" });
wait_for({ text: "Impact Card Generated", timeout: 30000 });
list_network_requests({ resourceTypes: ["websocket", "fetch", "xhr"] });
take_screenshot({ fullPage: true });
```

---

#### Page 4: Analytics (`/analytics`)

**Components to Test**:

- LiveAPITracker component
- APIUsageDashboard component
- PredictiveAnalytics component
- EnhancedAnalytics component
- Performance metrics charts
- Trend visualizations
- API health indicators

**Test Scenarios**:

1. **Analytics Page Load**

   - Navigate to `/analytics`
   - Verify dashboard displays
   - Check all metric widgets
   - Verify charts render
   - Check console for errors

2. **Live API Tracker**

   - Verify API calls display
   - Check success rate metrics
   - Verify response time displays
   - Test API filter options
   - Verify real-time updates

3. **API Usage Dashboard**

   - Verify usage metrics display
   - Check call counts per API
   - Verify time range filters
   - Test metric drill-downs
   - Verify trend indicators

4. **Predictive Analytics**

   - Verify predictions display
   - Check prediction confidence
   - Test prediction filters
   - Verify trend visualizations
   - Test prediction details

5. **Performance Metrics**

   - Verify all metrics display:
     - Total API Calls
     - Success Rate
     - Avg Response Time
     - Cache Hit Rate
   - Test metric tooltips
   - Verify metric updates

6. **Chart Interactions**
   - Test chart zooming
   - Test chart filtering
   - Verify chart tooltips
   - Test chart exports
   - Verify chart responsiveness

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/analytics" });
take_snapshot({ verbose: true });
// Interact with charts
click({ uid: "chart-zoom-button-uid" });
click({ uid: "metric-filter-uid" });
fill_form({
  elements: [{ uid: "time-range-select-uid", values: ["24h"] }],
});
wait_for({ text: "Updated", timeout: 3000 });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
take_screenshot({ fullPage: true });
performance_analyze_insight({ insightName: "LCPBreakdown" });
```

---

#### Page 5: Settings (`/settings`)

**Components to Test**:

- API Configuration section
- API key input
- Connection test button
- Data source toggle
- Notification preferences
- Email notifications toggle
- Slack integration toggle
- Risk threshold slider
- Save settings button

**Test Scenarios**:

1. **Settings Page Load**

   - Navigate to `/settings`
   - Verify all sections display
   - Check current settings values
   - Verify form fields render
   - Check console for errors

2. **API Configuration**

   - Enter API key
   - Click "Test Connection"
   - Verify connection test API call
   - Check success/error messages
   - Verify API key validation
   - Test invalid API key handling

3. **Data Source Toggle**

   - Toggle between "Demo" and "Live"
   - Verify mode changes
   - Check data updates
   - Verify UI reflects mode
   - Test mode persistence

4. **Notification Preferences**

   - Toggle email notifications
   - Toggle Slack integration
   - Adjust risk threshold slider
   - Verify slider value updates
   - Test slider min/max values

5. **Settings Persistence**

   - Change multiple settings
   - Click "Save Settings"
   - Verify API call
   - Reload page
   - Verify settings persist
   - Check local storage/API

6. **Form Validation**
   - Test invalid inputs
   - Verify validation messages
   - Test required fields
   - Verify form submission prevention

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/settings" });
take_snapshot({ verbose: true });
// Fill API key
fill({ uid: "api-key-input-uid", value: "test-key-123" });
click({ uid: "test-connection-button-uid" });
wait_for({ text: "Connection successful", timeout: 5000 });
// Toggle settings
click({ uid: "email-notifications-toggle-uid" });
drag({
  startElement: "risk-threshold-slider",
  startRef: ".slider-track",
  endElement: "risk-threshold-value",
  endRef: ".slider-thumb",
});
click({ uid: "save-settings-button-uid" });
wait_for({ text: "Settings saved", timeout: 3000 });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
```

---

#### Page 6: Integrations (`/integrations`)

**Components to Test**:

- IntegrationManager component
- Integration cards/list
- Integration setup wizards
- Integration health monitoring
- ObsidianIntegrationSetup
- HubSpotIntegrationSetup
- Integration status indicators

**Test Scenarios**:

1. **Integrations Page Load**

   - Navigate to `/integrations`
   - Verify integrations list displays
   - Check integration statuses
   - Verify setup buttons
   - Check console for errors

2. **Integration List**

   - Verify all integrations display
   - Check integration icons
   - Verify status indicators
   - Test integration filtering
   - Test integration search

3. **Integration Setup**

   - Click "Setup" on integration
   - Verify setup wizard opens
   - Fill setup form
   - Submit setup
   - Verify API calls
   - Check success/error handling

4. **Integration Health**

   - Verify health indicators
   - Check health monitoring
   - Test health refresh
   - Verify error states
   - Test health details

5. **Integration Management**
   - Test enable/disable
   - Test configuration editing
   - Test integration removal
   - Verify confirmation dialogs
   - Check API calls

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/integrations" });
take_snapshot({ verbose: true });
// Setup integration
click({ uid: "setup-integration-button-uid" });
fill_form({
  elements: [{ uid: "integration-config-uid", value: "config-value" }],
});
click({ uid: "submit-setup-button-uid" });
wait_for({ text: "Integration connected", timeout: 10000 });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
take_screenshot({ fullPage: true });
```

---

#### Page 7: Demo (`/demo`)

**Components to Test**:

- DemoActions component
- DemoGuidance component
- DemoWorkflows component
- APIOrchestrationStory component
- APIPipelineVisual component
- APIToggle component
- LiveDemoModal component
- DemoModeToggle component

**Test Scenarios**:

1. **Demo Page Load**

   - Navigate to `/demo`
   - Verify demo sections display
   - Check API showcase
   - Verify workflow visualizations
   - Check console for errors

2. **API Orchestration Story**

   - Verify story displays
   - Test story navigation
   - Verify API call visualizations
   - Test step-by-step progression
   - Verify API toggle functionality

3. **API Pipeline Visual**

   - Verify pipeline diagram displays
   - Test pipeline interactions
   - Verify API status indicators
   - Test pipeline step details
   - Verify flow animations

4. **Demo Workflows**

   - Select workflow
   - Execute workflow steps
   - Verify progress indicators
   - Check API calls
   - Verify completion state

5. **Demo Actions**
   - Test demo action buttons
   - Verify action execution
   - Check result displays
   - Test multiple actions
   - Verify error handling

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/demo" });
take_snapshot({ verbose: true });
// Test API toggle
click({ uid: "api-toggle-button-uid" });
wait_for({ text: "API enabled", timeout: 2000 });
// Execute demo workflow
click({ uid: "demo-workflow-button-uid" });
wait_for({ text: "Workflow complete", timeout: 30000 });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
take_screenshot({ fullPage: true });
```

---

#### Page 8: Tribe Demo (`/tribe-demo`)

**Components to Test**:

- TribeInterface component
- TribeInterfaceDemo component
- TribeModeSelector component
- RoleDetector component
- TribeInterfaceProvider
- Role-based UI adaptations

**Test Scenarios**:

1. **Tribe Demo Page Load**

   - Navigate to `/tribe-demo`
   - Verify interface displays
   - Check role selector
   - Verify UI adapts to role
   - Check console for errors

2. **Role Selection**

   - Test role dropdown/selector
   - Select different roles
   - Verify UI changes per role
   - Check role-specific features
   - Verify role persistence

3. **Role-Based UI Adaptation**

   - Verify UI elements change
   - Check feature visibility
   - Test role-specific widgets
   - Verify permissions display
   - Test role transitions

4. **Tribe Interface Features**
   - Test tribe-specific components
   - Verify collaboration features
   - Test shared workspaces
   - Verify role-based actions

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/tribe-demo" });
take_snapshot({ verbose: true });
// Select role
select_option({
  element: "role-selector",
  ref: ".role-dropdown",
  values: ["Product Manager"],
});
wait_for({ text: "Product Manager", timeout: 2000 });
take_snapshot({ verbose: true });
// Verify UI changes
click({ uid: "role-feature-button-uid" });
take_screenshot({ fullPage: true });
```

---

### Component Testing Matrix

#### Navigation Components

**Sidebar Component**:

- Test navigation links
- Verify active state highlighting
- Test collapsible sections
- Verify icon displays
- Test mobile responsive behavior
- Check keyboard navigation

**Header Component**:

- Test logo/brand display
- Verify "Start Analysis" button
- Test user menu
- Check notification bell
- Test mobile menu toggle

**Breadcrumb Component**:

- Verify breadcrumb trail
- Test breadcrumb links
- Check navigation on click
- Verify current page highlight

**Chrome DevTools MCP Tools**:

```typescript
take_snapshot({ verbose: true });
// Test sidebar navigation
click({ uid: "sidebar-dashboard-link-uid" });
wait_for({ text: "Dashboard", timeout: 5000 });
// Test header buttons
click({ uid: "start-analysis-button-uid" });
click({ uid: "user-menu-button-uid" });
take_screenshot({ fullPage: true });
```

---

#### Widget Components

**ImpactCard Component**:

- Verify card displays
- Test all tabs (Overview, Analysis, Evidence, Actions)
- Test tab switching
- Verify risk score display
- Test credibility indicators
- Verify source citations
- Test action recommendations
- Test card expansion/collapse

**WatchList Component**:

- Verify watchlist table
- Test sorting functionality
- Test filtering
- Test pagination
- Test row selection
- Test bulk actions

**APIUsageDashboard Component**:

- Verify metrics display
- Test metric cards
- Test chart visualizations
- Test time range filters
- Verify real-time updates

**DashboardInsights Component**:

- Verify insights display
- Test insight cards
- Test trend indicators
- Verify percentage displays

**RiskScoreWidget Component**:

- Verify risk score display
- Test score calculation
- Verify color coding
- Test score breakdown
- Verify tooltips

**Chrome DevTools MCP Tools**:

```typescript
// Test ImpactCard
take_snapshot({ verbose: true });
click({ uid: "impact-card-overview-tab-uid" });
click({ uid: "impact-card-analysis-tab-uid" });
click({ uid: "impact-card-evidence-tab-uid" });
click({ uid: "impact-card-actions-tab-uid" });
// Test widget interactions
click({ uid: "risk-score-expand-button-uid" });
take_screenshot({ fullPage: true });
```

---

#### Form Components

**Add Competitor Form**:

- Test all input fields
- Verify form validation
- Test required fields
- Verify error messages
- Test form submission
- Verify success handling

**Research Form**:

- Test company name input
- Verify search suggestions
- Test form submission
- Verify loading states
- Test error handling

**Settings Form**:

- Test API key input
- Test toggle switches
- Test slider inputs
- Test dropdown selects
- Verify form validation
- Test form submission

**Chrome DevTools MCP Tools**:

```typescript
// Test form filling
fill_form({
  elements: [
    { uid: "field-1-uid", value: "value1" },
    { uid: "field-2-uid", value: "value2" },
  ],
});
click({ uid: "submit-button-uid" });
wait_for({ text: "Success", timeout: 5000 });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
```

---

#### Modal/Dialog Components

**Research Detail Modal**:

- Test modal opening
- Verify modal content
- Test modal scrolling
- Test modal closing
- Verify modal backdrop
- Test escape key closing

**Share Dialog**:

- Test dialog opening
- Fill email fields
- Test form submission
- Verify success/error messages
- Test dialog closing

**Confirmation Dialogs**:

- Test dialog display
- Test confirm action
- Test cancel action
- Verify action execution

**Chrome DevTools MCP Tools**:

```typescript
// Open modal
click({ uid: "open-modal-button-uid" });
wait_for({ text: "Modal Title", timeout: 2000 });
take_snapshot({ verbose: true });
// Interact with modal
fill_form({
  elements: [{ uid: "modal-input-uid", value: "test" }],
});
click({ uid: "modal-submit-button-uid" });
// Close modal
press_key({ key: "Escape" });
take_screenshot({ fullPage: true });
```

---

#### Notification Components

**NotificationCenter Component**:

- Verify notifications display
- Test notification types (info, success, warning, error)
- Test notification dismissal
- Test notification stacking
- Verify auto-hide functionality
- Test notification actions

**Toast Component**:

- Verify toast displays
- Test toast positioning
- Test toast duration
- Test toast dismissal
- Verify toast animations

**FloatingChatWidget Component**:

- Test chat widget toggle
- Verify chat interface
- Test message sending
- Verify chat history
- Test chat closing

**Chrome DevTools MCP Tools**:

```typescript
// Trigger notification
click({ uid: "action-button-uid" });
wait_for({ text: "Notification message", timeout: 2000 });
take_snapshot({ verbose: true });
// Test notification interaction
click({ uid: "dismiss-notification-button-uid" });
// Test chat widget
click({ uid: "chat-widget-toggle-uid" });
fill({ uid: "chat-input-uid", value: "Test message" });
press_key({ key: "Enter" });
take_screenshot({ fullPage: true });
```

---

#### Loading & Error Components

**LoadingSkeleton Component**:

- Verify skeleton displays during load
- Test skeleton animations
- Verify skeleton disappears on load complete

**ErrorStates Component**:

- Test error state display
- Verify error messages
- Test retry buttons
- Test error recovery
- Verify error animations

**RouteLoadingBoundary Component**:

- Test error boundary trigger
- Verify error fallback display
- Test error recovery
- Verify error logging

**Chrome DevTools MCP Tools**:

```typescript
// Test loading state
navigate_page({ url: "http://localhost:3456/dashboard" });
take_snapshot({ verbose: true });
// Wait for load complete
wait_for({ text: "Dashboard", timeout: 10000 });
// Test error state (trigger API failure)
navigate_page({ url: "http://localhost:3456/research?error=true" });
wait_for({ text: "Error", timeout: 5000 });
take_snapshot({ verbose: true });
click({ uid: "retry-button-uid" });
```

---

### Feature-Specific Testing

#### API Orchestration Testing

**Test Scenarios**:

1. **Complete API Workflow**

   - Trigger impact card generation
   - Monitor News API call
   - Monitor Search API call
   - Monitor Chat API call
   - Monitor ARI API call
   - Verify orchestration sequence
   - Check WebSocket progress updates
   - Verify final result

2. **API Error Handling**

   - Simulate News API failure
   - Verify graceful degradation
   - Test retry logic
   - Verify error messages
   - Test partial success handling

3. **API Caching**
   - Verify cache hits
   - Test cache invalidation
   - Verify cache warming
   - Check cache statistics

**Chrome DevTools MCP Tools**:

```typescript
// Start orchestration
click({ uid: "generate-impact-button-uid" });
// Monitor network requests
list_network_requests({ resourceTypes: ["fetch", "xhr", "websocket"] });
// Wait for each API call
wait_for({ text: "News API complete", timeout: 10000 });
wait_for({ text: "Search API complete", timeout: 10000 });
wait_for({ text: "Chat API complete", timeout: 15000 });
wait_for({ text: "ARI API complete", timeout: 30000 });
// Verify completion
wait_for({ text: "Impact Card Generated", timeout: 5000 });
take_screenshot({ fullPage: true });
```

---

#### Real-Time Features Testing

**WebSocket Testing**:

- Verify WebSocket connection
- Test real-time updates
- Verify progress indicators
- Test reconnection handling
- Verify connection status

**Live Updates Testing**:

- Monitor live data updates
- Verify UI refreshes
- Test update frequency
- Verify update batching

**Chrome DevTools MCP Tools**:

```typescript
list_network_requests({ resourceTypes: ["websocket"] });
// Trigger real-time update
click({ uid: "refresh-button-uid" });
wait_for({ text: "Updated", timeout: 5000 });
take_snapshot({ verbose: true });
```

---

#### Export & Sharing Testing

**PDF Export Testing**:

- Test PDF generation
- Verify download starts
- Test PDF content
- Verify API calls
- Test error handling

**Email Sharing Testing**:

- Test share dialog
- Fill email addresses
- Submit share form
- Verify API call
- Check success/error messages

**Chrome DevTools MCP Tools**:

```typescript
// Test PDF export
click({ uid: "export-pdf-button-uid" });
wait_for({ text: "PDF generated", timeout: 30000 });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
// Test email share
click({ uid: "share-button-uid" });
fill_form({
  elements: [{ uid: "email-input-uid", value: "test@example.com" }],
});
click({ uid: "share-submit-button-uid" });
wait_for({ text: "Shared successfully", timeout: 5000 });
```

---

#### Advanced Features Testing

**ML Features**:

- Test ML feedback panel
- Verify ML predictions
- Test ML performance dashboard
- Verify model training status

**Sentiment Analysis**:

- Test sentiment tracking
- Verify sentiment alerts
- Test sentiment trends
- Verify sentiment dashboard

**Predictive Analytics**:

- Test predictions display
- Verify prediction accuracy
- Test prediction filters
- Verify trend predictions

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/analytics" });
take_snapshot({ verbose: true });
// Test ML features
click({ uid: "ml-panel-toggle-uid" });
wait_for({ text: "ML Predictions", timeout: 2000 });
// Test sentiment
click({ uid: "sentiment-tab-uid" });
take_screenshot({ fullPage: true });
```

---

### Edge Cases & Error Scenarios

**Test Scenarios**:

1. **Network Failures**

   - Simulate network offline
   - Verify error messages
   - Test retry functionality
   - Verify offline mode

2. **API Timeouts**

   - Simulate slow API responses
   - Verify timeout handling
   - Test timeout messages
   - Verify retry logic

3. **Invalid Data**

   - Test invalid form inputs
   - Test invalid API responses
   - Verify validation errors
   - Test error recovery

4. **Empty States**

   - Test empty watchlist
   - Test empty research list
   - Test empty analytics
   - Verify helpful messages

5. **Boundary Conditions**
   - Test maximum inputs
   - Test minimum inputs
   - Test edge values
   - Verify limits

**Chrome DevTools MCP Tools**:

```typescript
// Simulate network failure
evaluate_script({
  function:
    "() => { window.fetch = () => Promise.reject(new Error('Network Error')); }",
});
click({ uid: "action-button-uid" });
wait_for({ text: "Network error", timeout: 5000 });
take_snapshot({ verbose: true });
// Test retry
click({ uid: "retry-button-uid" });
```

---

#### Page 9: API Showcase (`/api-showcase`)

**Components to Test**:

- APIOrchestrationStory component
- APIPipelineVisual component
- LiveAPITracker component
- API status indicators
- API toggle functionality
- Workflow visualizations

**Test Scenarios**:

1. **API Showcase Page Load**

   - Navigate to `/api-showcase`
   - Verify API visualization displays
   - Check all API status indicators
   - Verify workflow diagram
   - Check console for errors

2. **API Orchestration Story**

   - Navigate through story steps
   - Verify API call visualizations
   - Test step-by-step progression
   - Verify API status updates
   - Test story replay

3. **API Pipeline Visual**

   - Verify pipeline flow diagram
   - Test pipeline step interactions
   - Verify API status indicators
   - Test step detail tooltips
   - Verify animation states

4. **Live API Tracker**

   - Verify API calls display in real-time
   - Test API call filtering
   - Verify API response times
   - Test API call details
   - Verify success/failure indicators

5. **API Toggle Functionality**
   - Test enabling/disabling APIs
   - Verify UI updates
   - Test workflow continuation
   - Verify error handling

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/api-showcase" });
take_snapshot({ verbose: true });
// Test API story
click({ uid: "story-next-button-uid" });
wait_for({ text: "Step 2", timeout: 2000 });
// Test pipeline interaction
click({ uid: "pipeline-step-uid" });
take_screenshot({ fullPage: true });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
```

---

#### Page 10: Markdown Demo (`/markdown-demo`)

**Components to Test**:

- MarkdownRenderer component
- Markdown content display
- Markdown formatting
- Code blocks
- Tables
- Links
- Images

**Test Scenarios**:

1. **Markdown Demo Page Load**

   - Navigate to `/markdown-demo`
   - Verify markdown content displays
   - Check formatting renders correctly
   - Verify code blocks syntax highlighting
   - Check console for errors

2. **Markdown Formatting**

   - Verify headings render
   - Test bold/italic text
   - Verify lists display
   - Test code blocks
   - Verify tables render

3. **Markdown Interactions**
   - Test link clicks
   - Verify image loading
   - Test code block copy
   - Verify responsive layout

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/markdown-demo" });
take_snapshot({ verbose: true });
click({ uid: "markdown-link-uid" });
take_screenshot({ fullPage: true });
```

---

#### Additional Component Testing

##### Advanced Intelligence Components

**EnhancedImpactCard Component**:

- Verify enhanced card displays
- Test all enhanced features
- Test timeline integration
- Verify evidence badges
- Test action recommendations
- Verify explainability features

**InsightTimeline Component**:

- Verify timeline displays
- Test timeline navigation
- Verify timeline events
- Test event filtering
- Verify timeline zooming

**EvidenceBadge Component**:

- Verify evidence badges display
- Test badge click expansion
- Verify confidence scores
- Test source citations
- Verify badge tooltips

**ExplainabilityDashboard Component**:

- Verify explainability metrics
- Test reasoning chain visualization
- Verify prediction explanations
- Test explanation filters
- Verify explanation details

**Chrome DevTools MCP Tools**:

```typescript
// Test Enhanced ImpactCard
navigate_page({ url: "http://localhost:3456/dashboard" });
take_snapshot({ verbose: true });
click({ uid: "enhanced-impact-card-uid" });
wait_for({ text: "Enhanced View", timeout: 2000 });
// Test timeline
click({ uid: "timeline-tab-uid" });
click({ uid: "timeline-event-uid" });
// Test evidence badge
click({ uid: "evidence-badge-uid" });
take_screenshot({ fullPage: true });
```

---

##### Analytics & Metrics Components

**EnhancedAnalytics Component**:

- Verify analytics dashboard
- Test metric widgets
- Verify chart interactions
- Test date range filters
- Verify metric drill-downs

**BenchmarkDrillDown Component**:

- Verify benchmark displays
- Test benchmark comparisons
- Verify metric breakdowns
- Test benchmark filtering
- Verify benchmark exports

**SentimentTrendChart Component**:

- Verify sentiment chart displays
- Test chart interactions
- Verify trend indicators
- Test sentiment filtering
- Verify chart tooltips

**SourceQualityVisualization Component**:

- Verify quality visualization
- Test quality filters
- Verify source breakdowns
- Test quality indicators
- Verify quality tooltips

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/analytics" });
take_snapshot({ verbose: true });
// Test analytics widgets
click({ uid: "metric-widget-uid" });
fill_form({
  elements: [{ uid: "date-range-select-uid", values: ["7d"] }],
});
wait_for({ text: "Updated", timeout: 3000 });
// Test charts
click({ uid: "chart-zoom-button-uid" });
take_screenshot({ fullPage: true });
```

---

##### Collaboration Components

**CollaborationPane Component**:

- Verify collaboration interface
- Test shared workspaces
- Test team features
- Verify permissions
- Test collaboration actions

**CommentThreads Component**:

- Verify comment threads display
- Test adding comments
- Test replying to comments
- Verify comment threading
- Test comment editing

**SharedWatchlistManager Component**:

- Verify shared watchlists
- Test watchlist sharing
- Verify team members
- Test watchlist permissions
- Verify watchlist collaboration

**AnnotationSystem Component**:

- Verify annotation interface
- Test adding annotations
- Test annotation editing
- Verify annotation display
- Test annotation deletion

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/monitoring" });
take_snapshot({ verbose: true });
// Test collaboration
click({ uid: "collaboration-pane-toggle-uid" });
fill_form({
  elements: [{ uid: "comment-input-uid", value: "Test comment" }],
});
click({ uid: "submit-comment-button-uid" });
wait_for({ text: "Comment added", timeout: 2000 });
take_screenshot({ fullPage: true });
```

---

##### Integration Components

**IntegrationManager Component**:

- Verify integration list
- Test integration setup
- Verify integration health
- Test integration configuration
- Verify integration actions

**ObsidianIntegrationSetup Component**:

- Test Obsidian setup wizard
- Fill Obsidian configuration
- Verify connection test
- Test integration activation
- Verify integration status

**HubSpotIntegrationSetup Component**:

- Test HubSpot setup wizard
- Fill HubSpot configuration
- Verify OAuth flow
- Test integration activation
- Verify data sync

**IntegrationHealthMonitor Component**:

- Verify health indicators
- Test health refresh
- Verify health details
- Test health alerts
- Verify health history

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/integrations" });
take_snapshot({ verbose: true });
// Setup integration
click({ uid: "setup-obsidian-button-uid" });
fill_form({
  elements: [{ uid: "obsidian-path-uid", value: "/path/to/vault" }],
});
click({ uid: "test-connection-button-uid" });
wait_for({ text: "Connected", timeout: 5000 });
click({ uid: "activate-integration-button-uid" });
take_screenshot({ fullPage: true });
```

---

##### ML & Advanced Features Components

**MLFeedbackPanel Component**:

- Verify ML feedback interface
- Test feedback submission
- Verify feedback history
- Test feedback filtering
- Verify feedback impact

**MLPerformanceDashboard Component**:

- Verify ML metrics display
- Test model performance
- Verify training status
- Test model selection
- Verify prediction accuracy

**PredictiveAnalytics Component**:

- Verify predictions display
- Test prediction details
- Verify confidence scores
- Test prediction filters
- Verify trend predictions

**UncertaintyDetectionPanel Component**:

- Verify uncertainty indicators
- Test uncertainty details
- Verify uncertainty alerts
- Test uncertainty filtering
- Verify uncertainty explanations

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/analytics" });
take_snapshot({ verbose: true });
// Test ML features
click({ uid: "ml-panel-toggle-uid" });
click({ uid: "submit-feedback-button-uid" });
fill_form({
  elements: [{ uid: "feedback-input-uid", value: "Test feedback" }],
});
wait_for({ text: "Feedback submitted", timeout: 3000 });
// Test predictive analytics
click({ uid: "predictions-tab-uid" });
take_screenshot({ fullPage: true });
```

---

##### UI/UX Components

**OnboardingModal Component**:

- Verify onboarding display
- Test onboarding steps
- Verify step progression
- Test onboarding completion
- Verify onboarding persistence

**SuccessAnimation Component**:

- Verify success animations
- Test animation triggers
- Verify animation completion
- Test animation variations

**SuccessConfetti Component**:

- Verify confetti animation
- Test confetti triggers
- Verify confetti variations
- Test animation performance

**ProgressiveDisclosure Component**:

- Verify progressive disclosure
- Test expand/collapse
- Verify disclosure states
- Test keyboard navigation

**ProgressiveFeatureProvider Component**:

- Verify feature loading
- Test progressive enhancement
- Verify feature availability
- Test feature fallbacks

**Chrome DevTools MCP Tools**:

```typescript
// Test onboarding
navigate_page({ url: "http://localhost:3456/dashboard" });
wait_for({ text: "Welcome", timeout: 3000 });
take_snapshot({ verbose: true });
click({ uid: "onboarding-next-button-uid" });
click({ uid: "onboarding-complete-button-uid" });
// Test progressive disclosure
click({ uid: "expand-section-button-uid" });
wait_for({ text: "Expanded content", timeout: 2000 });
take_screenshot({ fullPage: true });
```

---

### Complete Workflow Testing

#### End-to-End Workflow 1: Complete Intelligence Gathering

**Objective**: Test complete workflow from watchlist creation to action execution

**Steps**:

1. **Create Watchlist Entry**

   - Navigate to `/monitoring`
   - Click "Add Competitor"
   - Fill form with competitor details
   - Submit form
   - Verify entry appears

2. **Generate Impact Card**

   - Select competitor
   - Click "Generate Impact Card"
   - Monitor API orchestration
   - Wait for completion
   - Verify impact card displays

3. **Review Impact Card**

   - Check Overview tab
   - Check Analysis tab
   - Check Evidence tab
   - Check Actions tab
   - Verify all sections

4. **Execute Actions**

   - Select action recommendation
   - Mark action as complete
   - Verify action tracking
   - Check action history

5. **Share Results**
   - Click "Share" button
   - Fill email addresses
   - Submit share
   - Verify share success

**Chrome DevTools MCP Tools**:

```typescript
// Step 1: Create watchlist
navigate_page({ url: "http://localhost:3456/monitoring" });
click({ uid: "add-competitor-button-uid" });
fill_form({
  elements: [
    { uid: "competitor-name-uid", value: "Anthropic" },
    { uid: "keywords-uid", value: "Claude, LLM" },
  ],
});
click({ uid: "submit-button-uid" });
wait_for({ text: "Anthropic", timeout: 5000 });

// Step 2: Generate impact card
click({ uid: "generate-impact-button-uid" });
wait_for({ text: "Impact Card Generated", timeout: 30000 });
list_network_requests({ resourceTypes: ["fetch", "xhr", "websocket"] });

// Step 3: Review impact card
click({ uid: "impact-card-tab-analysis-uid" });
click({ uid: "impact-card-tab-evidence-uid" });
click({ uid: "impact-card-tab-actions-uid" });
take_screenshot({ fullPage: true });

// Step 4: Execute action
click({ uid: "action-item-checkbox-uid" });
wait_for({ text: "Action completed", timeout: 2000 });

// Step 5: Share
click({ uid: "share-button-uid" });
fill_form({
  elements: [{ uid: "email-input-uid", value: "team@example.com" }],
});
click({ uid: "share-submit-button-uid" });
wait_for({ text: "Shared successfully", timeout: 5000 });
```

---

#### End-to-End Workflow 2: Company Research & Analysis

**Objective**: Test complete research workflow from search to export

**Steps**:

1. **Search Company**

   - Navigate to `/research`
   - Enter company name
   - Click "Research Company"
   - Monitor API calls
   - Wait for completion

2. **Review Research**

   - Verify research report displays
   - Check company overview
   - Verify key findings
   - Check source citations
   - Verify API usage details

3. **Export Research**

   - Click "Export PDF"
   - Verify PDF generation
   - Check download starts
   - Verify file content

4. **Save Research**
   - Verify research saved
   - Check research history
   - Test research retrieval
   - Verify research persistence

**Chrome DevTools MCP Tools**:

```typescript
// Step 1: Search company
navigate_page({ url: "http://localhost:3456/research" });
fill_form({
  elements: [{ uid: "company-search-input-uid", value: "Stripe" }],
});
click({ uid: "research-button-uid" });
wait_for({ text: "Research completed", timeout: 60000 });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });

// Step 2: Review research
take_snapshot({ verbose: true });
// Verify all sections display

// Step 3: Export PDF
click({ uid: "export-pdf-button-uid" });
wait_for({ text: "PDF generated", timeout: 30000 });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });

// Step 4: Verify saved
navigate_page({ url: "http://localhost:3456/research" });
wait_for({ text: "Stripe", timeout: 5000 });
take_screenshot({ fullPage: true });
```

---

#### End-to-End Workflow 3: Analytics & Insights

**Objective**: Test complete analytics workflow from metrics to insights

**Steps**:

1. **View Analytics Dashboard**

   - Navigate to `/analytics`
   - Verify all metrics display
   - Check API usage dashboard
   - Verify live API tracker
   - Check predictive analytics

2. **Analyze Metrics**

   - Filter by time range
   - Select specific APIs
   - Drill down into metrics
   - Export analytics data

3. **Review Insights**
   - Check key insights
   - Review trend analysis
   - Verify predictions
   - Check recommendations

**Chrome DevTools MCP Tools**:

```typescript
navigate_page({ url: "http://localhost:3456/analytics" });
take_snapshot({ verbose: true });
// Filter metrics
fill_form({
  elements: [
    { uid: "time-range-select-uid", values: ["7d"] },
    { uid: "api-filter-select-uid", values: ["Search API"] },
  ],
});
wait_for({ text: "Updated", timeout: 3000 });
// Drill down
click({ uid: "metric-card-uid" });
wait_for({ text: "Details", timeout: 2000 });
take_screenshot({ fullPage: true });
```

---

### API Endpoint Testing Matrix

#### Backend API Endpoints

**Watchlist Endpoints**:

- `GET /api/v1/watch/` - List watchlist items
- `POST /api/v1/watch/` - Create watchlist item
- `GET /api/v1/watch/{id}` - Get watchlist item
- `PUT /api/v1/watch/{id}` - Update watchlist item
- `DELETE /api/v1/watch/{id}` - Delete watchlist item

**Impact Card Endpoints**:

- `GET /api/v1/impact/` - List impact cards
- `POST /api/v1/impact/generate` - Generate impact card
- `GET /api/v1/impact/{id}` - Get impact card
- `POST /api/v1/impact/{id}/share` - Share impact card
- `GET /api/v1/impact/{id}/export` - Export impact card

**Research Endpoints**:

- `GET /api/v1/research/` - List research items
- `POST /api/v1/research/company` - Research company
- `GET /api/v1/research/{id}` - Get research item
- `POST /api/v1/research/{id}/share` - Share research
- `GET /api/v1/research/{id}/export` - Export research

**Metrics Endpoints**:

- `GET /api/v1/metrics/api-usage` - API usage metrics
- `GET /api/v1/metrics/performance` - Performance metrics
- `GET /api/v1/metrics/health` - Health metrics

**Chrome DevTools MCP Tools**:

```typescript
// Test each endpoint
navigate_page({ url: "http://localhost:3456/dashboard" });
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
// Trigger API calls
click({ uid: "action-button-uid" });
wait_for({ text: "Success", timeout: 5000 });
// Verify API calls
const requests = list_network_requests({ resourceTypes: ["fetch", "xhr"] });
// Verify status codes, response times, etc.
```

---

### Responsive Design Testing

#### Breakpoint Testing

**Test Scenarios**:

1. **Mobile View (320px - 768px)**

   - Verify mobile layout
   - Test hamburger menu
   - Verify touch interactions
   - Check form usability
   - Verify content readability

2. **Tablet View (768px - 1024px)**

   - Verify tablet layout
   - Test sidebar behavior
   - Verify widget layouts
   - Check navigation

3. **Desktop View (1024px+)**
   - Verify desktop layout
   - Test full sidebar
   - Verify widget arrangements
   - Check multi-column layouts

**Chrome DevTools MCP Tools**:

```typescript
// Test mobile view
resize({ width: 375, height: 667 });
navigate_page({ url: "http://localhost:3456/dashboard" });
take_snapshot({ verbose: true });
click({ uid: "mobile-menu-toggle-uid" });
take_screenshot({ fullPage: true });

// Test tablet view
resize({ width: 768, height: 1024 });
navigate_page({ url: "http://localhost:3456/dashboard" });
take_snapshot({ verbose: true });
take_screenshot({ fullPage: true });

// Test desktop view
resize({ width: 1920, height: 1080 });
navigate_page({ url: "http://localhost:3456/dashboard" });
take_snapshot({ verbose: true });
take_screenshot({ fullPage: true });
```

---

### Cross-Browser Testing

**Test Scenarios**:

1. **Chrome Browser**

   - Test all features
   - Verify performance
   - Check console errors
   - Verify compatibility

2. **Firefox Browser** (if supported)

   - Test core features
   - Verify rendering
   - Check compatibility

3. **Safari Browser** (if supported)
   - Test core features
   - Verify rendering
   - Check compatibility

**Note**: Chrome DevTools MCP primarily works with Chrome, but can test cross-browser compatibility by checking for browser-specific issues.

---

### Security Testing

**Test Scenarios**:

1. **XSS Prevention**

   - Test user input sanitization
   - Verify script injection prevention
   - Test HTML injection prevention

2. **CSRF Protection**

   - Verify CSRF tokens
   - Test form submissions
   - Verify API security

3. **Authentication**

   - Test login flow
   - Verify session management
   - Test logout functionality

4. **Data Privacy**
   - Verify sensitive data handling
   - Test data encryption
   - Verify privacy compliance

**Chrome DevTools MCP Tools**:

```typescript
// Test XSS prevention
fill_form({
  elements: [{ uid: "input-uid", value: "<script>alert('XSS')</script>" }],
});
click({ uid: "submit-button-uid" });
take_snapshot({ verbose: true });
// Verify script not executed
list_console_messages({ types: ["error"] });
```

---

### Load & Stress Testing

**Test Scenarios**:

1. **Concurrent Users**

   - Simulate multiple concurrent requests
   - Verify API rate limiting
   - Check error handling
   - Verify performance degradation

2. **Large Data Sets**

   - Test with large watchlists
   - Test with many impact cards
   - Verify pagination
   - Check performance

3. **Long-Running Operations**
   - Test long API calls
   - Verify timeout handling
   - Check progress indicators
   - Verify cancellation

**Chrome DevTools MCP Tools**:

```typescript
// Test concurrent requests
evaluate_script({
  function:
    "async () => { const promises = []; for(let i = 0; i < 10; i++) { promises.push(fetch('/api/v1/watch/')); } await Promise.all(promises); }",
});
list_network_requests({ resourceTypes: ["fetch", "xhr"] });
// Verify rate limiting or errors
take_snapshot({ verbose: true });
```

---

## Performance Testing

### Core Web Vitals Monitoring

**Execute directly using Chrome DevTools MCP tools** - Do not create scripts.

**Direct Execution Pattern**:

```typescript
// For each page, execute these tools directly:

// 1. Start performance trace
performance_start_trace({ reload: true, autoStop: false });

// 2. Navigate to page
navigate_page({ url: "http://localhost:3456/dashboard" });

// 3. Wait for page to be interactive
wait_for({ text: "Dashboard", timeout: 10000 });

// 4. Stop trace
performance_stop_trace();
// → Returns metrics including LCP, CLS, FCP, etc.

// 5. Analyze specific insights
performance_analyze_insight({ insightName: "LCPBreakdown" });
performance_analyze_insight({ insightName: "CLSBreakdown" });
performance_analyze_insight({ insightName: "FCPBreakdown" });
```

**Performance Thresholds**:

- **LCP** (Largest Contentful Paint): < 2,500 ms
- **FID** (First Input Delay): < 100 ms
- **CLS** (Cumulative Layout Shift): < 0.1
- **FCP** (First Contentful Paint): < 1,800 ms
- **TTI** (Time to Interactive): < 3,500 ms

**Test Each Page**:
Execute the pattern above for:

- `/dashboard`
- `/research`
- `/analytics`
- `/settings`
- `/integrations`

**Report Results**:
Document actual metrics in test report:

- Page name
- Actual LCP, CLS, FCP values
- Pass/fail against thresholds
- Recommendations if thresholds not met

---

## Accessibility Testing

### Automated A11y Checks

**Execute directly using Chrome DevTools MCP tools** - Do not create scripts.

**Direct Execution Pattern**:

```typescript
// 1. Navigate to page
navigate_page({ url: "http://localhost:3456/dashboard" });

// 2. Take verbose snapshot (includes full a11y tree)
const snapshot = take_snapshot({ verbose: true });

// 3. Analyze snapshot for accessibility issues
// Review snapshot output for:
// - Missing ARIA labels on interactive elements
// - Missing labels on form inputs
// - Missing alt text on images
// - Heading hierarchy issues
// - Focus indicators

// 4. Check console for a11y errors
const consoleMessages = list_console_messages({
  types: ["error", "warn"],
});
// Filter for accessibility-related messages

// 5. Document findings
// Create report with:
// - List of accessibility issues found
// - Element UIDs with issues
// - Recommendations for fixes
```

**Accessibility Checks to Perform**:

1. **ARIA Labels**: All interactive elements should have labels

   - Buttons, links, form inputs, etc.
   - Use `take_snapshot({ verbose: true })` and verify each element

2. **Form Labels**: All form inputs should be labeled

   - Check `labeledBy` attribute or associated label text

3. **Heading Hierarchy**: Headings should follow logical order

   - Check snapshot for heading levels (h1 → h2 → h3)

4. **Keyboard Navigation**: All interactive elements should be keyboard accessible

   - Use `take_snapshot()` to verify focusable elements

5. **Focus Indicators**: Keyboard focus should be visible
   - Verify focus states in snapshot

**Test Each Page**:
Execute the pattern above for all major pages and document findings.

---

## Integration Testing

### End-to-End Workflows

**Execute directly using Chrome DevTools MCP tools** - Do not create test scripts.

**Example: Complete Watchlist to Impact Card Flow**

Execute these tools directly in sequence:

```typescript
// 1. Navigate to dashboard
navigate_page({ url: "http://localhost:3456/dashboard" });
wait_for({ text: "Dashboard", timeout: 10000 });

// 2. Take initial snapshot to find button UIDs
const initialSnapshot = take_snapshot({ verbose: true });
// Find UID for "Add Competitor" button

// 3. Click "Add Competitor" button
click({ uid: "add-competitor-button-uid" });

// 4. Fill form with test data
fill_form({
  elements: [
    { uid: "competitor-name-input-uid", value: "TestCorp" },
    { uid: "keywords-input-uid", value: "AI, ML" },
    { uid: "description-input-uid", value: "Test description" },
  ],
});

// 5. Submit form
click({ uid: "submit-button-uid" });

// 6. Wait for item to appear
wait_for({ text: "TestCorp", timeout: 5000 });

// 7. Verify item appears in list
const snapshot = take_snapshot();
// Check for TestCorp in list

// 8. Monitor network requests
const requests = list_network_requests({ resourceTypes: ["fetch", "xhr"] });
// Verify API calls were made to /api/v1/watch

// 9. Navigate to research page
navigate_page({ url: "http://localhost:3456/research" });
wait_for({ text: "Research", timeout: 10000 });

// 10. Generate impact card
click({ uid: "generate-impact-card-button-uid" });

// 11. Monitor network requests during generation
const generationRequests = list_network_requests({
  resourceTypes: ["fetch", "xhr"],
});
// Verify multiple API calls (News, Search, Chat, ARI)

// 12. Wait for completion
wait_for({ text: "Impact Card Generated", timeout: 30000 });

// 13. Verify impact card displays
const finalSnapshot = take_snapshot({ verbose: true });
// Check for impact card content

// 14. Take screenshot for visual verification
take_screenshot({ fullPage: true });
```

**Key Points**:

- Execute tools directly, not via scripts
- Use actual UIDs from snapshots
- Capture real network requests
- Document actual results in report

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/chrome-devtools-tests.yml
name: Chrome DevTools MCP Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"

      - name: Install dependencies
        run: |
          npm ci
          cd backend && pip install -r requirements.txt

      - name: Start backend
        run: |
          cd backend
          uvicorn app.main:app --port 8765 &
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db

      - name: Build frontend
        run: npm run build

      - name: Start frontend
        run: npm run start &
        env:
          NEXT_PUBLIC_API_URL: http://localhost:8765

      - name: Wait for services
        run: |
          timeout 30 bash -c 'until curl -f http://localhost:3456; do sleep 1; done'
          timeout 30 bash -c 'until curl -f http://localhost:8765/health; do sleep 1; done'

      - name: Install Chrome DevTools MCP
        run: npm install -g chrome-devtools-mcp

      - name: Run tests
        run: |
          npm run test:chrome-devtools
        env:
          FRONTEND_URL: http://localhost:3456
          BACKEND_URL: http://localhost:8765

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: |
            tests/chrome-devtools/results/
            tests/chrome-devtools/screenshots/
```

---

## Test Execution and Reporting

### Direct Test Execution Workflow

**IMPORTANT**: Tests are executed directly using Chrome DevTools MCP tools, not through test scripts.

**Workflow**:

1. **Execute Tests Directly**

   - Use Chrome DevTools MCP tools via MCP client (e.g., Claude)
   - Execute tools in sequence for each test scenario
   - Capture actual results from tool executions

2. **Capture Results**

   - Network requests from `list_network_requests()`
   - Performance metrics from `performance_stop_trace()`
   - Accessibility data from `take_snapshot({ verbose: true })`
   - Screenshots from `take_screenshot()`
   - Console messages from `list_console_messages()`

3. **Generate Report**
   - Create markdown report in `tests/chrome-devtools/results/`
   - Include actual metrics and findings
   - Document failures with specific details
   - Include screenshots and network request details

**Example Report Structure**:

```markdown
# Chrome DevTools MCP Test Execution Report

## Test Results

### Scenario 1: Navigation Flow ✅

- **Status**: PASSED
- **Duration**: ~3 seconds
- **Steps Executed**: [list actual steps]
- **Findings**: [actual results]

### Scenario 2: Performance Benchmarking ✅

- **Status**: PASSED
- **LCP**: 491ms (threshold: <2500ms) ✅
- **CLS**: 0.00 (threshold: <0.1) ✅
- **Network Requests**: 25 captured
- **Issues Found**: [if any]

## Issues Identified

### 🔴 Critical Issue: Backend Connectivity

- **Problem**: [actual issue found]
- **Impact**: [real impact]
- **Recommendation**: [fix recommendation]

## Performance Baselines

| Page      | LCP   | CLS  | Status |
| --------- | ----- | ---- | ------ |
| Dashboard | 491ms | 0.00 | ✅     |
```

### Report Generation

**DO NOT** create scripts that only document test steps. Instead:

1. **Execute tests** using MCP tools directly
2. **Capture results** from actual tool executions
3. **Generate markdown report** with real data
4. **Save reports** to `tests/chrome-devtools/results/`

**Example Report Filename**:

- `DIRECT_MCP_TEST_EXECUTION_REPORT_YYYY-MM-DD.md`
- Include timestamp and execution method in filename

---

## Test Data Management

### Test Fixtures

```typescript
// tests/chrome-devtools/fixtures.ts
export const testWatchlistItems = [
  {
    competitor_name: "TestCorp",
    keywords: "AI, ML, SaaS",
    description: "Test competitor",
    risk_threshold: 5,
  },
  {
    competitor_name: "DemoInc",
    keywords: "Enterprise, Cloud",
    description: "Demo competitor",
    risk_threshold: 3,
  },
];

export const testImpactCardData = {
  competitor_name: "TestCorp",
  risk_level: "medium",
  credibility_score: 0.85,
  key_findings: ["Finding 1", "Finding 2"],
};
```

---

## Best Practices

### 1. **Direct Execution**

✅ **DO**: Execute tests directly using Chrome DevTools MCP tools  
❌ **DON'T**: Create scripts that only document test steps without execution

**Example**:

```typescript
✅ navigate_page({ url: 'http://localhost:3456/dashboard' })
✅ list_network_requests() // Capture actual requests
✅ performance_stop_trace() // Get real metrics
❌ // Create script that says "should navigate" but doesn't navigate
```

### 2. **Isolation**

- Use `--isolated=true` flag for clean test environments
- Each test should start with a fresh browser state
- Use `new_page()` for isolated test runs

### 3. **Error Handling**

- Always check console messages: `list_console_messages({ types: ['error', 'warn'] })`
- Capture network failures: `list_network_requests()` to find failed requests
- Document actual errors in test reports

### 4. **Performance Baselines**

- Execute performance tests directly and capture real metrics
- Document actual LCP, CLS, FCP values in reports
- Track performance regressions by comparing actual values over time

**Example**:

```typescript
performance_start_trace({ reload: true });
navigate_page({ url: "http://localhost:3456/dashboard" });
performance_stop_trace();
// → Document actual LCP: 491ms (not "should be < 2500ms")
```

### 5. **Screenshot Comparison**

- Take screenshots at key points using `take_screenshot({ fullPage: true })`
- Save screenshots to `tests/chrome-devtools/screenshots/`
- Include screenshots in test reports for visual verification

### 6. **Network Monitoring**

- Always verify API calls: `list_network_requests({ resourceTypes: ['fetch', 'xhr'] })`
- Check actual status codes from network requests
- Document actual response times in reports
- Capture failed requests for debugging

### 7. **Reporting**

- Generate reports from actual test execution
- Include real metrics, not placeholder values
- Document actual issues found during execution
- Provide actionable recommendations based on real findings

---

## Reporting & Documentation

### Test Report Template

```markdown
# Test Execution Report

**Date**: [Date]
**Environment**: [Environment]
**Build**: [Build Number]

## Summary

- Total Tests: X
- Passed: Y
- Failed: Z
- Duration: [Time]

## Performance Metrics

| Page      | LCP  | FID  | CLS  | Status |
| --------- | ---- | ---- | ---- | ------ |
| Dashboard | 1.2s | 50ms | 0.05 | ✅     |
| Research  | 2.1s | 80ms | 0.08 | ✅     |

## Failed Tests

[Details of failed tests]

## Screenshots

[Screenshot gallery]
```

---

## Next Steps

1. **Set up MCP server** in your development environment
2. **Execute tests directly** using Chrome DevTools MCP tools (not scripts)
3. **Establish performance baselines** by executing performance tests and documenting actual metrics
4. **Generate reports** from actual test execution results
5. **Fix issues found** during direct test execution
6. **Expand test coverage** by executing additional scenarios
7. **Monitor and maintain** by re-running tests and tracking actual metrics over time

## Execution Summary

**Key Principle**: This testing plan emphasizes **direct execution** using Chrome DevTools MCP tools rather than creating test scripts.

**When executing tests**:

- ✅ Use MCP tools directly (`navigate_page`, `click`, `take_snapshot`, etc.)
- ✅ Capture actual results from tool executions
- ✅ Generate reports with real metrics and findings
- ❌ Do not create scripts that only document steps
- ❌ Do not write code that doesn't actually execute tests

**Example Direct Execution**:

```
1. navigate_page({ url: 'http://localhost:3456/dashboard' })
2. take_snapshot({ verbose: true })
3. list_network_requests()
4. performance_start_trace({ reload: true })
5. performance_stop_trace()
6. → Document actual results in report
```

This approach ensures:

- Tests actually run and produce real results
- Issues are discovered immediately
- Metrics are accurate and actionable
- Reports reflect actual application state

---

## Resources

- [Chrome DevTools MCP Documentation](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [Chrome DevTools Protocol](https://developer.chrome.com/docs/devtools-protocol/)
- [Core Web Vitals](https://web.dev/vitals/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

## Appendix: Quick Reference

### Common Chrome DevTools MCP Commands

```typescript
// Navigation
navigate_page({ url: 'http://localhost:3456/dashboard' })

// Interaction
click({ uid: 'button-uid' })
fill({ uid: 'input-uid', value: 'text' })
fill_form({ elements: [...] })

// Monitoring
take_snapshot({ verbose: true })
take_screenshot({ fullPage: true })
list_network_requests()
list_console_messages()

// Performance
performance_start_trace({ reload: true })
performance_stop_trace()
performance_analyze_insight({ insightName: 'LCPBreakdown' })

// Evaluation
evaluate_script({
  function: '() => document.title'
})
```

---

---

## Test Coverage Summary

### Pages Tested (10 Pages)

1. ✅ **Dashboard** (`/dashboard`) - Complete testing matrix
2. ✅ **Research** (`/research`) - Complete testing matrix
3. ✅ **Monitoring** (`/monitoring`) - Complete testing matrix
4. ✅ **Analytics** (`/analytics`) - Complete testing matrix
5. ✅ **Settings** (`/settings`) - Complete testing matrix
6. ✅ **Integrations** (`/integrations`) - Complete testing matrix
7. ✅ **Demo** (`/demo`) - Complete testing matrix
8. ✅ **Tribe Demo** (`/tribe-demo`) - Complete testing matrix
9. ✅ **API Showcase** (`/api-showcase`) - Complete testing matrix
10. ✅ **Markdown Demo** (`/markdown-demo`) - Complete testing matrix

### Components Tested (100+ Components)

#### Navigation Components (3)

- ✅ Sidebar
- ✅ Header
- ✅ Breadcrumb

#### Widget Components (20+)

- ✅ ImpactCard
- ✅ EnhancedImpactCard
- ✅ WatchList
- ✅ APIUsageDashboard
- ✅ DashboardInsights
- ✅ RiskScoreWidget
- ✅ LiveAPITracker
- ✅ PredictiveAnalytics
- ✅ EnhancedAnalytics
- ✅ BenchmarkDrillDown
- ✅ SentimentTrendChart
- ✅ SourceQualityVisualization
- ✅ InsightTimeline
- ✅ EvidenceBadge
- ✅ ExplainabilityDashboard
- ✅ And more...

#### Form Components (5+)

- ✅ Add Competitor Form
- ✅ Research Form
- ✅ Settings Form
- ✅ Integration Setup Forms
- ✅ Share Forms

#### Modal/Dialog Components (5+)

- ✅ Research Detail Modal
- ✅ Share Dialog
- ✅ Confirmation Dialogs
- ✅ Onboarding Modal
- ✅ Live Demo Modal

#### Notification Components (3)

- ✅ NotificationCenter
- ✅ Toast
- ✅ FloatingChatWidget

#### Loading & Error Components (4)

- ✅ LoadingSkeleton
- ✅ ErrorStates
- ✅ RouteLoadingBoundary
- ✅ SuspenseBoundary

#### Advanced Features Components (30+)

- ✅ ML Feedback Panel
- ✅ ML Performance Dashboard
- ✅ Sentiment Analysis Components
- ✅ Collaboration Components
- ✅ Integration Components
- ✅ And more...

### Features Tested

#### Core Intelligence Features

- ✅ Watchlist Management (CRUD operations)
- ✅ Impact Card Generation
- ✅ Company Research
- ✅ API Orchestration (All 4 APIs)
- ✅ Real-time Updates (WebSocket)
- ✅ Export & Sharing (PDF, Email)
- ✅ Analytics & Metrics
- ✅ Performance Monitoring

#### Advanced Features

- ✅ ML Predictions
- ✅ Sentiment Analysis
- ✅ Predictive Analytics
- ✅ Explainability Dashboard
- ✅ Evidence Scoring
- ✅ Timeline Analysis
- ✅ Action Recommendations
- ✅ Collaboration Features

#### Integration Features

- ✅ Integration Setup
- ✅ Integration Health Monitoring
- ✅ Obsidian Integration
- ✅ HubSpot Integration
- ✅ API Integration Management

### Workflows Tested

1. ✅ **Complete Intelligence Gathering** - Watchlist → Impact Card → Actions → Share
2. ✅ **Company Research & Analysis** - Search → Review → Export → Save
3. ✅ **Analytics & Insights** - Metrics → Analysis → Insights → Export

### API Endpoints Tested

#### Backend Endpoints (50+)

- ✅ Watchlist Endpoints (5)
- ✅ Impact Card Endpoints (5)
- ✅ Research Endpoints (5)
- ✅ Metrics Endpoints (5+)
- ✅ Analytics Endpoints (10+)
- ✅ Integration Endpoints (10+)
- ✅ ML Endpoints (10+)
- ✅ And more...

### Testing Dimensions Covered

#### Functional Testing

- ✅ Page Load Tests
- ✅ Navigation Tests
- ✅ Component Tests
- ✅ Form Tests
- ✅ Interaction Tests
- ✅ Workflow Tests

#### Performance Testing

- ✅ Core Web Vitals (LCP, FID, CLS, FCP, TTI)
- ✅ Page Load Performance
- ✅ API Response Times
- ✅ Resource Loading
- ✅ Network Optimization

#### Accessibility Testing

- ✅ ARIA Compliance
- ✅ Keyboard Navigation
- ✅ Screen Reader Compatibility
- ✅ Color Contrast
- ✅ Semantic HTML

#### Network Testing

- ✅ API Endpoint Availability
- ✅ Request/Response Validation
- ✅ Error Handling
- ✅ Rate Limiting
- ✅ CORS Configuration

#### Visual Testing

- ✅ Screenshot Comparison
- ✅ Layout Consistency
- ✅ Responsive Design
- ✅ Visual Regression

#### Security Testing

- ✅ XSS Prevention
- ✅ CSRF Protection
- ✅ Authentication
- ✅ Data Privacy

#### Responsive Design Testing

- ✅ Mobile View (320px - 768px)
- ✅ Tablet View (768px - 1024px)
- ✅ Desktop View (1024px+)

#### Edge Cases & Error Scenarios

- ✅ Network Failures
- ✅ API Timeouts
- ✅ Invalid Data
- ✅ Empty States
- ✅ Boundary Conditions
- ✅ Load & Stress Testing

### Test Execution Matrix

| Test Category           | Total Tests | Execution Method               |
| ----------------------- | ----------- | ------------------------------ |
| **Page Tests**          | 100+        | Direct MCP tool execution      |
| **Component Tests**     | 200+        | Direct MCP tool execution      |
| **Workflow Tests**      | 20+         | Direct MCP tool execution      |
| **API Tests**           | 100+        | Network request monitoring     |
| **Performance Tests**   | 50+         | Performance trace analysis     |
| **Accessibility Tests** | 50+         | Snapshot analysis              |
| **Responsive Tests**    | 30+         | Viewport resizing              |
| **Security Tests**      | 20+         | Script injection testing       |
| **Edge Case Tests**     | 30+         | Error simulation               |
| **Total Tests**         | **600+**    | Direct execution via MCP tools |

### Test Coverage Statistics

- **Pages**: 10/10 (100%)
- **Core Components**: 50+/50+ (100%)
- **Advanced Components**: 50+/50+ (100%)
- **API Endpoints**: 50+/50+ (100%)
- **Workflows**: 3/3 (100%)
- **Features**: 100+/100+ (100%)

### Testing Priority Levels

#### 🔴 Critical Priority

- Core intelligence features (Watchlist, Impact Cards, Research)
- API orchestration
- Authentication & security
- Core Web Vitals

#### 🟡 High Priority

- Advanced features (ML, Analytics, Predictions)
- Integrations
- Real-time features
- Export & sharing

#### 🟢 Medium Priority

- UI/UX enhancements
- Collaboration features
- Demo features
- Markdown rendering

### Test Execution Checklist

Use this checklist to ensure comprehensive testing:

#### Phase 1: Foundation Tests ✅

- [ ] All pages load successfully
- [ ] Navigation works correctly
- [ ] Core components render
- [ ] No console errors
- [ ] API endpoints respond

#### Phase 2: Interactive Tests ✅

- [ ] Forms submit correctly
- [ ] Buttons trigger actions
- [ ] Modals open/close
- [ ] Workflows complete
- [ ] Real-time updates work

#### Phase 3: Performance Tests ✅

- [ ] Core Web Vitals pass thresholds
- [ ] Page load times acceptable
- [ ] API response times acceptable
- [ ] Resource optimization verified

#### Phase 4: Accessibility Tests ✅

- [ ] ARIA labels present
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Color contrast meets WCAG AA
- [ ] Focus indicators visible

#### Phase 5: Advanced Tests ✅

- [ ] ML features work
- [ ] Analytics display correctly
- [ ] Integrations function
- [ ] Collaboration features work
- [ ] Advanced widgets function

#### Phase 6: Edge Cases ✅

- [ ] Error handling works
- [ ] Empty states display
- [ ] Network failures handled
- [ ] Invalid data rejected
- [ ] Boundary conditions tested

### Reporting Checklist

For each test execution, document:

- [ ] Test scenario executed
- [ ] Actual results captured
- [ ] Metrics recorded (performance, network, etc.)
- [ ] Screenshots taken
- [ ] Errors documented
- [ ] Fixes applied
- [ ] Re-tests completed
- [ ] Final status (PASS/FAIL)

### Success Criteria

**All tests must**:

- ✅ Execute successfully using Chrome DevTools MCP tools
- ✅ Capture actual results (not placeholders)
- ✅ Document real metrics and findings
- ✅ Identify and fix all errors
- ✅ Meet performance thresholds
- ✅ Pass accessibility checks
- ✅ Complete workflows end-to-end

---

**Document Version**: 3.0  
**Last Updated**: 2025-01-31  
**Author**: Testing Team  
**Status**: Active - Comprehensive Direct Execution Approach

## Change Log

### Version 3.0 (2025-01-31)

- **Expanded**: Comprehensive feature testing matrix with 600+ test scenarios
- **Added**: Page-by-page testing for all 10 pages
- **Added**: Component testing matrix for 100+ components
- **Added**: Complete workflow testing scenarios
- **Added**: API endpoint testing matrix
- **Added**: Responsive design testing
- **Added**: Security testing scenarios
- **Added**: Load & stress testing
- **Added**: Test coverage summary
- **Updated**: Table of contents to reflect new sections
- **Enhanced**: All test scenarios with detailed Chrome DevTools MCP tool examples

### Version 2.0 (2025-01-31)

- **Updated approach**: Emphasizes direct execution using Chrome DevTools MCP tools
- **Removed**: Script-based test examples that only document steps
- **Added**: Direct execution patterns and examples
- **Added**: Workflow for executing tests directly via MCP client
- **Updated**: Best practices to emphasize real test execution
- **Updated**: Reporting section to focus on actual results from tool executions
