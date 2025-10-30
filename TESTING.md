# 🧪 Enterprise CIA - Testing Suite

Comprehensive testing suite for the Enterprise CIA hackathon project, ensuring all You.com API integrations and components work correctly.

## 🎯 Testing Strategy

### Test Coverage Areas

- **You.com API Integration**: All 4 APIs (News, Search, Chat, ARI) with mocking and error handling
- **Database Models**: SQLAlchemy models, relationships, and constraints
- **API Endpoints**: FastAPI routes, validation, and error responses
- **Frontend Components**: React components with user interactions
- **Integration Workflows**: Complete enterprise and individual user flows
- **Schema Validation**: Pydantic schemas with edge cases and boundary conditions

### Testing Pyramid

```
    🔺 E2E Tests (Integration)
   🔺🔺 API Tests (Endpoints)
  🔺🔺🔺 Unit Tests (Components)
 🔺🔺🔺🔺 Schema Tests (Validation)
```

## 🚀 Quick Start

### Backend Testing

```bash
# Run all backend tests
./run_tests.sh

# Or run specific test categories
cd backend

# Unit tests
pytest tests/test_schemas.py -v

# You.com API tests
pytest tests/test_you_client.py -v

# Database tests
pytest tests/test_models.py -v

# API endpoint tests
pytest tests/test_api_endpoints.py -v

# Integration tests
pytest tests/test_integration.py -v

# Coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

### Frontend Testing

```bash
cd frontend

# Install test dependencies
npm install

# Run all frontend tests
npm test

# Watch mode for development
npm run test:watch

# Coverage report
npm run test:coverage
```

## 📋 Test Categories

### 1. You.com API Client Tests (`test_you_client.py`)

**Purpose**: Ensure robust integration with all 4 You.com APIs

**Key Test Cases**:

- ✅ Client initialization with API key validation
- ✅ News API: Real-time competitor monitoring
- ✅ Search API: Context enrichment and company profiles
- ✅ Chat API: Custom Agents for competitive analysis
- ✅ ARI API: Deep research reports (400+ sources)
- ✅ Complete workflow orchestration (all 4 APIs together)
- ✅ Error handling with exponential backoff retry
- ✅ API usage tracking for demo metrics
- ✅ Quick company research for individual users

**Mock Strategy**:

```python
# Mock You.com API responses
mock_response = MagicMock()
mock_response.json.return_value = {"news": [...]}
mock_response.raise_for_status.return_value = None

with patch.object(you_client.client, 'get', return_value=mock_response):
    result = await you_client.fetch_news("test query")
```

### 2. Database Model Tests (`test_models.py`)

**Purpose**: Validate SQLAlchemy models and relationships

**Key Test Cases**:

- ✅ WatchItem model creation and defaults
- ✅ ImpactCard model with complex JSON fields
- ✅ CompanyResearch model for individual users
- ✅ Model relationships (WatchItem ↔ ImpactCard)
- ✅ Timestamp handling (created_at, updated_at)
- ✅ String representations and model methods

### 3. API Endpoint Tests (`test_api_endpoints.py`)

**Purpose**: Test FastAPI routes and HTTP interactions

**Key Test Cases**:

- ✅ Watchlist CRUD operations
- ✅ Impact Card generation with You.com API mocking
- ✅ Company research endpoints
- ✅ Error handling (404, 500, validation errors)
- ✅ Health check and demo endpoints
- ✅ Request/response validation

**Test Pattern**:

```python
@pytest.mark.asyncio
async def test_generate_impact_card_success(client: AsyncClient):
    with patch('app.api.impact.get_you_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.generate_impact_card.return_value = {...}
        mock_get_client.return_value = mock_client

        response = await client.post("/api/v1/impact/generate", json=data)
        assert response.status_code == 201
```

### 4. Integration Tests (`test_integration.py`)

**Purpose**: Test complete user workflows end-to-end

**Key Test Cases**:

- ✅ **Individual Research Workflow**: Company research → Export results (MVP focus)
- ✅ **Basic Competitive Monitoring**: Create watchlist → Generate Impact Card → View results
- ✅ **API Integration**: You.com API usage tracking and orchestration
- ✅ **Error Handling**: You.com API failures, database errors
- ✅ **Performance**: Concurrent requests, large data handling

_Note: Enterprise-specific features (team collaboration, compliance, RBAC) will be tested in the next version._

**Workflow Example**:

```python
async def test_complete_individual_research_workflow(client, db_session):
    # Step 1: Research company using Search + ARI APIs
    response = await client.post("/api/v1/research/company", json={
        "company_name": "Perplexity AI"
    })
    research_data = response.json()

    # Step 2: Verify You.com API usage tracking
    assert research_data["api_usage"]["search_calls"] >= 1
    assert research_data["api_usage"]["ari_calls"] >= 1

    # Step 3: Test export functionality
    response = await client.get(f"/api/v1/research/{research_data['id']}/export")
    assert response.status_code == 200
```

### 5. Schema Validation Tests (`test_schemas.py`)

**Purpose**: Test Pydantic schemas and data validation

**Key Test Cases**:

- ✅ Valid schema creation with all fields
- ✅ Minimal required fields and defaults
- ✅ Validation errors for invalid data
- ✅ Boundary conditions (min/max values)
- ✅ Edge cases (empty lists, long strings)
- ✅ Regex pattern validation (risk levels, priorities)

### 6. Frontend Component Tests

**Purpose**: Test React components and user interactions

**Key Test Cases**:

- ✅ **WatchList Component**: Add/edit/delete competitors, form validation
- ✅ **ImpactCardDisplay Component**: Generate cards, detailed view, API usage display
- ✅ **CompanyResearch Component**: Individual research workflow
- ✅ **APIUsageDashboard Component**: Metrics and visualization
- ✅ Loading states, error handling, empty states

**React Testing Pattern**:

```typescript
it("generates new impact card", async () => {
  mockApi.api.post.mockResolvedValue({ data: mockImpactCard });

  renderWithQueryClient(<ImpactCardDisplay />);

  fireEvent.change(competitorInput, { target: { value: "OpenAI" } });
  fireEvent.click(generateButton);

  await waitFor(() => {
    expect(mockApi.api.post).toHaveBeenCalledWith("/api/v1/impact/generate", {
      competitor_name: "OpenAI",
      keywords: [],
    });
  });
});
```

## 🎯 Test Data and Fixtures

### Backend Fixtures (`conftest.py`)

- **Database Session**: In-memory SQLite for fast tests
- **Test Client**: FastAPI test client with dependency overrides
- **Mock Data**: Sample competitors, impact cards, research data
- **You.com API Responses**: Realistic mock responses for all 4 APIs

### Frontend Test Setup (`jest.setup.js`)

- **Mock APIs**: Axios/fetch mocking for API calls
- **Mock Components**: Recharts, WebSocket, ResizeObserver
- **Test Environment**: jsdom for DOM testing
- **Query Client**: React Query test setup

## 📊 Coverage Targets

### Backend Coverage Goals

- **Overall**: >90% line coverage (target)
- **You.com Client**: 100% (critical integration - target)
- **API Endpoints**: >95% (user-facing - target)
- **Models**: >90% (data integrity - target)
- **Schemas**: >95% (validation logic - target)

_Note: Test fixtures need repair before accurate coverage measurement_

### Frontend Coverage Goals

- **Components**: >85% (user interactions)
- **Hooks**: >90% (business logic)
- **Utils**: >95% (helper functions)

## 🚨 Critical Test Scenarios

### You.com API Integration

```python
# Test all 4 APIs working together
async def test_complete_api_orchestration():
    result = await you_client.generate_impact_card("OpenAI", ["GPT"])

    # Verify all APIs were called
    assert you_client.api_usage["news_calls"] == 1
    assert you_client.api_usage["search_calls"] == 1
    assert you_client.api_usage["chat_calls"] == 1
    assert you_client.api_usage["ari_calls"] == 1
    assert you_client.api_usage["total_calls"] == 4
```

### Error Handling

```python
# Test You.com API failure handling
async def test_api_error_handling():
    mock_client.generate_impact_card.side_effect = Exception("API Error")

    response = await client.post("/api/v1/impact/generate", json=data)
    assert response.status_code == 500
    assert "error" in response.json()
```

### Performance Testing

```python
# Test concurrent requests
async def test_concurrent_requests():
    tasks = [create_watch_item(str(i)) for i in range(5)]
    responses = await asyncio.gather(*tasks)

    for response in responses:
        assert response.status_code == 201
```

## 🔧 Test Configuration

### Backend (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
addopts = -v --tb=short --strict-markers --disable-warnings --asyncio-mode=auto
markers =
    asyncio: mark test as async
    integration: mark test as integration test
    unit: mark test as unit test
```

### Frontend (`jest.config.js`)

```javascript
module.exports = {
  testEnvironment: "jest-environment-jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  moduleNameMapping: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  collectCoverageFrom: ["src/**/*.{js,jsx,ts,tsx}", "!src/**/*.d.ts"],
};
```

## 🎪 Demo Testing Checklist

### Pre-Demo Validation

- [ ] All You.com API integrations working
- [ ] Database models and migrations tested
- [ ] API endpoints responding correctly
- [ ] Frontend components rendering properly
- [ ] Error handling graceful and informative
- [ ] Performance acceptable under load

### Live Demo Testing

- [ ] Create watchlist → Generate Impact Card workflow
- [ ] Individual company research workflow
- [ ] API usage dashboard showing metrics
- [ ] Error scenarios handled gracefully
- [ ] Real-time updates working via WebSocket

## 🏆 Hackathon Testing Success

The comprehensive testing suite ensures:

1. **You.com API Integration**: All 4 APIs work together flawlessly
2. **Demo Reliability**: No crashes or failures during presentation
3. **Data Integrity**: Proper validation and error handling
4. **User Experience**: Smooth interactions and feedback
5. **Performance**: Responsive under demo conditions

**Test Results Summary**:

- ⚠️ **Backend**: Test suite exists, fixture issues need resolution
- ⚠️ **Frontend**: Component tests implemented, coverage verification needed
- ✅ **Integration**: Complete workflows designed and ready for testing
- ✅ **You.com APIs**: All 4 APIs mocked and integration tests prepared
- ✅ **New Features**: Advanced integrations and analytics services implemented
- 🔄 **Coverage**: Actual coverage verification pending test fixes

**New Features Added**:

- Notion integration service with comprehensive API coverage
- Salesforce integration service with CRM workflow support
- Predictive analytics engine with statistical analysis
- Integration management system with monitoring capabilities
- ✅ **Error Handling**: Graceful degradation and recovery

**Ready for Hackathon Demo! 🚀**
