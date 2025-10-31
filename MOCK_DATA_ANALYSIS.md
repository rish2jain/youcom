# Mock Data Implementation Status - Technical Specification

## 🎯 Current Mock Data Status

**Status**: 🔄 **PRODUCTION TRANSITION REQUIRED**  
**Priority**: High - Replace mock data with You.com API integration  
**Impact**: Core platform functionality and demo credibility

## ✅ Mock Data Audit Results

### 🔴 Critical - Replace Immediately

| Component               | Mock Data Type       | Production Impact    | Status                         |
| ----------------------- | -------------------- | -------------------- | ------------------------------ |
| `WatchList.tsx`         | Industry competitors | Core functionality   | 🔄 Needs You.com News API      |
| `CompanyResearch.tsx`   | Research reports     | Core functionality   | 🔄 Needs You.com Search + ARI  |
| `ImpactCard.tsx`        | Risk analysis        | Core functionality   | 🔄 Needs You.com Custom Agents |
| `APIUsageDashboard.tsx` | Usage metrics        | Platform credibility | 🔄 Needs real tracking         |

### 🟡 Medium Priority - Production Enhancement

| Component                 | Mock Data Type | Production Impact | Status                       |
| ------------------------- | -------------- | ----------------- | ---------------------------- |
| `PredictiveAnalytics.tsx` | Market trends  | Advanced features | 🔄 Needs analytics engine    |
| `ActionTracker.tsx`       | Action items   | User workflow     | 🔄 Needs user-generated data |
| `PerformanceMonitor.tsx`  | System metrics | Monitoring        | 🔄 Needs real telemetry      |

### 🟢 Low Priority - Keep for Demo

| Component               | Mock Data Type     | Production Impact | Status                 |
| ----------------------- | ------------------ | ----------------- | ---------------------- |
| `PersonalPlaybooks.tsx` | Template playbooks | Demo value        | ✅ Keep as defaults    |
| `SuccessMetrics.tsx`    | Platform benefits  | Marketing         | ✅ Keep for onboarding |
| `DemoActions.tsx`       | Sample scenarios   | Demo mode         | ✅ Keep for demos      |

## 🔧 Implementation Roadmap

### Phase 1: Core API Integration (Week 1)

#### 1.1 Watchlist Data Replacement

**File**: `components/WatchList.tsx`

```typescript
// REMOVE: Mock data generation
const generateWatchlistData = useMemo(() => {
  return industryCompetitors.slice(0, 3).map((company, idx) => ({
    // ... mock data
  }));
}, [industryCompetitors, userContext.industry]);

// REPLACE WITH: You.com News API integration
const { data: watchItems } = useQuery({
  queryKey: ["watchItems"],
  queryFn: async () => {
    const response = await api.get("/api/v1/watch");
    return response.data;
  },
});
```

**Backend**: `app/api/v1/watch/route.ts`

```typescript
// REMOVE: mockWatchItems array
// REPLACE WITH: Database queries + You.com News API calls
```

#### 1.2 Company Research Replacement

**File**: `components/CompanyResearch.tsx`

```typescript
// REMOVE: Fallback mock research
const newResearch = {
  id: Date.now(),
  company_name,
  // ... mock fields
};

// REPLACE WITH: Real You.com API calls
const searchResponse = await fetch(
  `https://api.ydc-index.io/v1/search?query=${encodeURIComponent(
    company_name
  )}`,
  { headers: { "X-API-Key": YOU_API_KEY } }
);

const ariResponse = await fetch("https://api.you.com/v1/chat", {
  method: "POST",
  headers: { "X-API-Key": YOU_API_KEY },
  body: JSON.stringify({ query: `Research ${company_name}` }),
});
```

#### 1.3 Impact Analysis Replacement

**File**: `components/ImpactCard.tsx`

```typescript
// REMOVE: Static content in renderTabContent()
case "overview":
  return (
    <div className="space-y-6">
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <p className="text-gray-800">
          OpenAI's GPT-4 Turbo launch introduces... // REMOVE STATIC TEXT
        </p>
      </div>
    </div>
  );

// REPLACE WITH: Dynamic content from You.com Custom Agents API
const impactAnalysis = await api.post("/api/v1/impact/analyze", {
  competitor: data.title,
  context: newsData
});
```

### Phase 2: Metrics & Analytics (Week 2)

#### 2.1 Real API Usage Tracking

**File**: `components/APIUsageDashboard.tsx`

```typescript
// REMOVE: mockMetrics object
const mockMetrics = {
  impact_cards: 23,
  total_calls: 2847,
  // ... all mock data
};

// REPLACE WITH: Real usage tracking
const { data: metrics } = useQuery({
  queryKey: ["apiUsageMetrics"],
  queryFn: () => api.get("/api/v1/metrics/usage").then((res) => res.data),
});
```

**Backend Implementation**:

```python
# Add to backend/app/services/metrics.py
class APIUsageTracker:
    def track_call(self, api_name: str, endpoint: str, response_time: float):
        # Store in database
        pass

    def get_usage_metrics(self, time_range: str):
        # Query real data from database
        pass
```

#### 2.2 Performance Monitoring

**File**: `components/PerformanceMonitor.tsx`

```typescript
// REMOVE: Simulated metrics
setMetrics((prev) => ({
  apiResponseTime: Math.random() * 2000 + 500,
  successRate: 95 + Math.random() * 5,
  // ... simulated data
}));

// REPLACE WITH: Real telemetry
const { data: performance } = useQuery({
  queryKey: ["performanceMetrics"],
  queryFn: () => api.get("/api/v1/metrics/performance"),
  refetchInterval: 5000,
});
```

### Phase 3: User-Generated Content (Week 3)

#### 3.1 Custom Actions

**File**: `components/ActionTracker.tsx`

```typescript
// REMOVE: sampleActions array
const sampleActions: Action[] = [
  {
    id: 1,
    title: "Compare GPT-4 Turbo features...",
    // ... static actions
  },
];

// REPLACE WITH: User-generated actions
const { data: actions } = useQuery({
  queryKey: ["userActions"],
  queryFn: () => api.get("/api/v1/actions/user"),
});
```

#### 3.2 Custom Playbooks

**File**: `components/PersonalPlaybooks.tsx`

```typescript
// KEEP: defaultPlaybooks as templates
// ADD: User-created playbooks
const { data: userPlaybooks } = useQuery({
  queryKey: ["userPlaybooks"],
  queryFn: () => api.get("/api/v1/playbooks/user"),
});

const allPlaybooks = [...defaultPlaybooks, ...(userPlaybooks || [])];
```

## 📋 Implementation Checklist

### ✅ Backend API Routes

- [ ] **`/api/v1/watch`**: Replace mock with database + You.com News API
- [ ] **`/api/v1/research`**: Connect to You.com Search + ARI APIs
- [ ] **`/api/v1/impact`**: Implement You.com Custom Agents integration
- [ ] **`/api/v1/metrics/usage`**: Add real API usage tracking
- [ ] **`/api/v1/metrics/performance`**: Implement system telemetry

### ✅ Frontend Components

- [ ] **WatchList**: Remove `generateWatchlistData`, use real API
- [ ] **CompanyResearch**: Remove fallback mock research
- [ ] **ImpactCard**: Replace static content with dynamic analysis
- [ ] **APIUsageDashboard**: Connect to real metrics endpoint
- [ ] **PerformanceMonitor**: Use real telemetry data

### ✅ Database Schema

```sql
-- Add usage tracking tables
CREATE TABLE api_usage_logs (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(50),
    endpoint VARCHAR(100),
    response_time_ms INTEGER,
    status_code INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add user actions table
CREATE TABLE user_actions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    title VARCHAR(200),
    description TEXT,
    priority VARCHAR(20),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 Quick Implementation Commands

### 1. Backend API Integration

```bash
# Add You.com API service
touch backend/app/services/you_api_client.py

# Add usage tracking
touch backend/app/services/usage_tracker.py

# Update API routes
# Edit: backend/app/api/v1/watch.py
# Edit: backend/app/api/v1/research.py
# Edit: backend/app/api/v1/metrics.py
```

### 2. Frontend Updates

```bash
# Update components to use real APIs
# Edit: components/WatchList.tsx
# Edit: components/CompanyResearch.tsx
# Edit: components/ImpactCard.tsx
# Edit: components/APIUsageDashboard.tsx

# Test API integration
npm run test:integration
```

### 3. Database Migration

```bash
# Create migration for usage tracking
cd backend
alembic revision --autogenerate -m "Add usage tracking tables"
alembic upgrade head
```

## 🎯 Success Criteria

### ✅ Phase 1 Complete When:

- [ ] Watchlist shows real competitor data from You.com News API
- [ ] Company research generates actual reports using Search + ARI APIs
- [ ] Impact cards display real analysis from Custom Agents API
- [ ] No mock data visible in core user workflows

### ✅ Phase 2 Complete When:

- [ ] API usage dashboard shows real metrics
- [ ] Performance monitoring displays actual system telemetry
- [ ] Cost tracking reflects real You.com API usage
- [ ] Rate limiting shows actual quota consumption

### ✅ Phase 3 Complete When:

- [ ] Users can create custom actions from insights
- [ ] Custom playbooks can be saved and shared
- [ ] All user-generated content persists across sessions
- [ ] Demo mode still works with sample data

## 🔍 Testing Strategy

### Unit Tests

```bash
# Test API integrations
pytest backend/tests/test_you_api_integration.py

# Test component data flow
npm test -- --testPathPattern=components/.*\.test\.tsx
```

### Integration Tests

```bash
# Test end-to-end workflows
pytest backend/tests/test_e2e_workflows.py

# Test frontend-backend integration
npm run test:e2e
```

### Manual Testing

```bash
# Verify no mock data in production mode
YOU_API_KEY=real_key npm run dev

# Test fallback behavior when APIs unavailable
YOU_API_KEY=invalid npm run dev
```

## 📊 Detailed Mock Data Locations

### Core Components with Mock Data

#### `components/WatchList.tsx`

```typescript
// Lines 45-60: Industry-specific mock data generation
const generateWatchlistData = useMemo(() => {
  return industryCompetitors.slice(0, 3).map((company, idx) => ({
    id: idx + 1,
    competitor_name: company,
    keywords: [company, "product", "announcement", "launch"],
    description: `${company} - Key competitor in ${userContext.industry}`,
    is_active: true,
    created_at: new Date(
      Date.now() - (idx + 1) * 7 * 24 * 60 * 60 * 1000
    ).toISOString(),
    last_checked: new Date(Date.now() - idx * 2 * 60 * 60 * 1000).toISOString(),
    status: "completed",
    latest_activity:
      idx === 0
        ? `${company} major product update detected - High threat (${
            7.5 + idx
          }/ 10)`
        : `${company} pricing changes detected - Medium threat (${
            6.0 + idx
          }/10)`,
    impact_cards_generated: 3 - idx,
  }));
}, [industryCompetitors, userContext.industry]);
```

#### `components/CompanyResearch.tsx`

```typescript
// Lines 120-150: Fallback mock research when APIs fail
const newResearch = {
  id: Date.now(),
  company_name,
  status: "completed",
  summary:
    chatData.answer?.substring(0, 200) + "..." ||
    `Comprehensive analysis of ${company_name}`,
  confidence_score: 85,
  total_sources: searchResults.length || 400,
  api_usage: {
    search_calls: 1,
    ari_calls: 1,
    total_calls: 2,
  },
  created_at: new Date().toISOString(),
  search_results: {
    results: searchResults.map((hit: any) => ({
      title: hit.title || "",
      snippet: hit.snippets?.[0] || hit.description || "",
      url: hit.url || "",
    })),
  },
  research_report: {
    report: chatData.answer || "Research report generated using You.com APIs.",
  },
};
```

#### `components/ImpactCard.tsx`

```typescript
// Lines 80-120: Static content in tab rendering
case "overview":
  return (
    <div className="space-y-6">
      <div>
        <h4 className="font-semibold text-gray-900 mb-3">Key Insights</h4>
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <p className="text-gray-800">
            OpenAI's GPT-4 Turbo launch introduces significant competitive
            pressure with improved performance and reduced pricing that
            could impact our market position.
          </p>
        </div>
      </div>
      // ... more static content
    </div>
  );
```

#### `components/APIUsageDashboard.tsx`

```typescript
// Lines 30-80: Comprehensive mock metrics
const mockMetrics = {
  impact_cards: 23,
  company_research: 15,
  total_calls: 2847,
  success_rate: 95.9,
  average_latency_ms: 1250,
  p95_latency_ms: 2800,
  p99_latency_ms: 4200,
  by_service: {
    news: 1205,
    search: 892,
    chat: 456,
    ari: 294,
  },
  usage_last_24h: [
    { time: "00:00", news: 45, search: 32, chat: 18, ari: 12 },
    { time: "04:00", news: 38, search: 28, chat: 15, ari: 8 },
    // ... more time series data
  ],
  // ... extensive mock data structure
};
```

### API Routes with Mock Data

#### `app/api/v1/watch/route.ts`

```typescript
const mockWatchItems = [
  {
    id: 1,
    competitor_name: "OpenAI",
    keywords: ["GPT", "ChatGPT", "artificial intelligence"],
    description: "Leading AI company with GPT models",
    created_at: "2024-01-10T10:00:00Z",
    is_active: true,
    last_checked: "2024-01-10T15:30:00Z",
  },
  // ... more mock items
];
```

#### `app/api/v1/metrics/api-usage/route.ts`

```typescript
const mockMetrics = {
  impact_cards: 23,
  company_research: 15,
  total_calls: 2847,
  // ... detailed mock metrics with time-based variations
  apis: {
    news: {
      requests: 1205,
      success_rate: 97.2,
      avg_response_time: 340,
      cost: 28.8,
      description: "Real-time competitive news monitoring",
    },
    // ... detailed API breakdown
  },
};
```

### Context and Utility Mock Data

#### `contexts/UserContext.tsx`

```typescript
// Industry-specific competitor mapping
const competitorMap: Record<string, string[]> = {
  "Artificial Intelligence & ML": [
    "OpenAI",
    "Anthropic",
    "Google DeepMind",
    "Cohere",
    "Mistral AI",
    "Stability AI",
  ],
  "SaaS & Cloud Services": [
    "Salesforce",
    "Microsoft Azure",
    "AWS",
    "Google Cloud",
    "ServiceNow",
    "Workday",
  ],
  // ... 11 total industry categories
};
```

#### `app/page.tsx`

```typescript
// Industry-specific alert templates
const alertTemplates = useMemo(() => {
  const templates: Record<string, any[]> = {
    "Artificial Intelligence & ML": [
      {
        company: "OpenAI",
        risk: 8.8,
        level: "high",
        summary: "GPT-4 Turbo released with 128K context window",
      },
      {
        company: "Anthropic",
        risk: 7.5,
        level: "high",
        summary: "Claude 3 family announced with improved performance",
      },
      // ... more templates
    ],
    // ... templates for each industry
  };
  return (
    templates[userContext.industry] || templates["Artificial Intelligence & ML"]
  );
}, [userContext.industry]);
```

## 🔄 Migration Strategy

### Immediate Actions (This Week)

1. **Audit Current Mock Usage**: ✅ Complete (this document)
2. **Prioritize Critical Components**: Focus on WatchList, CompanyResearch, ImpactCard
3. **Setup You.com API Integration**: Implement real API calls with fallback to mock
4. **Test Hybrid Approach**: Real APIs when available, mock when not

### Short Term (Next 2 Weeks)

1. **Replace Core Mock Data**: Implement Phase 1 changes
2. **Add Usage Tracking**: Real API metrics and performance monitoring
3. **User Testing**: Validate real data improves user experience
4. **Performance Optimization**: Ensure real APIs meet performance targets

### Long Term (Next Month)

1. **Advanced Analytics**: Replace predictive analytics mock data
2. **User-Generated Content**: Enable custom actions and playbooks
3. **Production Deployment**: Full transition to real data in production
4. **Monitoring & Alerting**: Real-time monitoring of API health and costs

This comprehensive analysis provides the technical specification needed to transition from mock data to production-ready You.com API integration while maintaining demo capabilities and ensuring a smooth user experience.
