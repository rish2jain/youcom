# Enterprise CIA - Testing Guide

**Last Updated**: October 30, 2025  
**Status**: ✅ Comprehensive Testing Suite

## 🎯 Testing Overview

Enterprise CIA uses a comprehensive testing strategy covering backend APIs, frontend components, integration workflows, and You.com API interactions. This guide covers all testing approaches, tools, and procedures.

## 🏗 Testing Architecture

### Testing Pyramid

```
    /\     E2E Tests (10%)
   /  \    Integration Tests (20%)
  /____\   Unit Tests (70%)
```

**Unit Tests (70%)**:

- Individual function testing
- Component isolation testing
- Mock external dependencies
- Fast execution (<1s per test)

**Integration Tests (20%)**:

- API endpoint testing
- Database integration testing
- You.com API integration testing
- Service interaction testing

**End-to-End Tests (10%)**:

- Complete user workflows
- Cross-browser testing
- Real API interactions
- Performance validation

## 🔧 Backend Testing

### Test Structure

```
backend/tests/
├── unit/
│   ├── test_models.py          # Database model tests
│   ├── test_services.py        # Business logic tests
│   └── test_utils.py           # Utility function tests
├── integration/
│   ├── test_api_endpoints.py   # API endpoint tests
│   ├── test_you_client.py      # You.com API tests
│   └── test_database.py        # Database integration tests
└── fixtures/
    ├── sample_data.py          # Test data fixtures
    └── mock_responses.py       # Mock API responses
```

### Running Backend Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test function
pytest tests/unit/test_models.py::test_watch_item_creation
```

### Test Configuration

**pytest.ini**:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    you_api: Tests requiring You.com API
```

### Mock Strategies

**You.com API Mocking**:

```python
# Mock You.com API responses
@pytest.fixture
def mock_you_client():
    with patch('app.services.you_client.YouClient') as mock:
        mock.return_value.search.return_value = {
            "results": [{"title": "Test", "url": "test.com"}]
        }
        yield mock

# Use in tests
def test_company_research(mock_you_client):
    result = research_service.research_company("TestCorp")
    assert result["company_name"] == "TestCorp"
    mock_you_client.return_value.search.assert_called_once()
```

**Database Mocking**:

```python
@pytest.fixture
def db_session():
    # Load test database URL from configuration/env
    # For production-like testing, use PostgreSQL test database
    test_db_url = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

    engine = create_engine(test_db_url)
    TestingSessionLocal = sessionmaker(bind=engine)

    # Apply migrations/schema for PostgreSQL, create_all for SQLite
    if test_db_url.startswith("postgresql"):
        # Run Alembic migrations against test database
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
        command.upgrade(alembic_cfg, "head")
    else:
        # SQLite in-memory fallback (note: may mask PostgreSQL-specific issues)
        Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Note: For comprehensive testing, set TEST_DATABASE_URL to a PostgreSQL test instance
# Example: TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/test_db
```

## 🎨 Frontend Testing

### Test Structure

```
components/__tests__/
├── WatchList.test.tsx          # Watchlist component tests
├── ImpactCardDisplay.test.tsx  # Impact card tests
├── CompanyResearch.test.tsx    # Research component tests
├── APIUsageDashboard.test.tsx  # Dashboard tests
└── __mocks__/
    ├── api.ts                  # API mock implementations
    └── socket.ts               # WebSocket mocks
```

### Testing Tools

- **Vitest**: Fast unit test runner
- **React Testing Library**: Component testing utilities
- **MSW**: API mocking for integration tests
- **Playwright**: End-to-end testing

### Running Frontend Tests

```bash
# Install dependencies
npm install

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run specific test file
npm test WatchList.test.tsx

# Run tests matching pattern
npm test -- --grep "Impact Card"
```

### Component Testing Examples

**React Component Test**:

```typescript
import { render, screen, fireEvent } from "@testing-library/react";
import { WatchList } from "../WatchList";

describe("WatchList Component", () => {
  test("renders watchlist items", () => {
    const mockWatchItems = [{ id: 1, name: "OpenAI", keywords: ["GPT", "AI"] }];

    render(<WatchList items={mockWatchItems} />);

    expect(screen.getByText("OpenAI")).toBeInTheDocument();
    expect(screen.getByText("GPT, AI")).toBeInTheDocument();
  });

  test("handles add competitor", async () => {
    const mockOnAdd = jest.fn();
    render(<WatchList onAdd={mockOnAdd} />);

    fireEvent.click(screen.getByText("Add Competitor"));
    fireEvent.change(screen.getByLabelText("Company Name"), {
      target: { value: "TestCorp" },
    });
    fireEvent.click(screen.getByText("Save"));

    expect(mockOnAdd).toHaveBeenCalledWith({
      name: "TestCorp",
      keywords: [],
    });
  });
});
```

**API Integration Test**:

```typescript
import { rest } from "msw";
import { setupServer } from "msw/node";
import { apiClient } from "../lib/api";

const server = setupServer(
  rest.get("/api/v1/watch/", (req, res, ctx) => {
    return res(ctx.json([{ id: 1, name: "OpenAI", keywords: ["GPT"] }]));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test("fetches watchlist items", async () => {
  const items = await apiClient.getWatchItems();
  expect(items).toHaveLength(1);
  expect(items[0].name).toBe("OpenAI");
});
```

## 🔗 Integration Testing

### You.com API Integration

**Test Categories**:

- API authentication and headers
- Rate limiting and error handling
- Response parsing and validation
- Circuit breaker functionality

**Example Integration Test**:

```python
@pytest.mark.integration
@pytest.mark.you_api
def test_you_api_news_integration():
    """Test actual You.com News API integration"""
    client = YouClient(api_key=os.getenv('YOU_API_KEY'))

    response = client.get_news(
        query="OpenAI",
        count=5
    )

    assert response is not None
    assert 'news' in response
    assert len(response['news']) <= 5

    # Validate response structure
    for item in response['news']:
        assert 'title' in item
        assert 'url' in item
        assert 'published_at' in item
```

### Database Integration

**Test Database Setup**:

```python
@pytest.fixture(scope="session")
def test_db():
    """Create test database for integration tests"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    """Create database session for each test"""
    connection = test_db.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

## 🎭 End-to-End Testing

### Playwright Configuration

**playwright.config.ts**:

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  retries: 2,
  use: {
    baseURL: "http://localhost:3456",
    headless: true,
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
  ],
});
```

### E2E Test Examples

**Complete User Workflow**:

```typescript
import { test, expect } from "@playwright/test";

test("complete competitive monitoring workflow", async ({ page }) => {
  // Navigate to application
  await page.goto("/");

  // Add competitor to watchlist
  await page.click('[data-testid="add-competitor"]');
  await page.fill('[data-testid="company-name"]', "OpenAI");
  await page.fill('[data-testid="keywords"]', "GPT, ChatGPT");
  await page.click('[data-testid="save-competitor"]');

  // Generate impact card
  await page.click('[data-testid="generate-impact-card"]');

  // Wait for processing to complete
  await page.waitForSelector('[data-testid="impact-card-complete"]', {
    timeout: 60000,
  });

  // Verify impact card content
  await expect(page.locator('[data-testid="risk-score"]')).toBeVisible();
  await expect(page.locator('[data-testid="evidence-panel"]')).toBeVisible();
  await expect(page.locator('[data-testid="recommendations"]')).toBeVisible();
});

test("individual company research workflow", async ({ page }) => {
  await page.goto("/");

  // Navigate to individual research
  await page.click('[data-testid="individual-research-tab"]');

  // Research company
  await page.fill('[data-testid="company-search"]', "Perplexity AI");
  await page.click('[data-testid="research-button"]');

  // Wait for research completion
  await page.waitForSelector('[data-testid="research-complete"]', {
    timeout: 120000,
  });

  // Verify research content
  await expect(page.locator('[data-testid="company-overview"]')).toBeVisible();
  await expect(page.locator('[data-testid="funding-history"]')).toBeVisible();
  await expect(
    page.locator('[data-testid="competitor-analysis"]')
  ).toBeVisible();

  // Test export functionality
  await page.click('[data-testid="export-pdf"]');
  const download = await page.waitForEvent("download");
  expect(download.suggestedFilename()).toContain("Perplexity_AI");
});
```

## 📊 Test Coverage

### Coverage Goals

- **Overall Coverage**: ≥90%
- **Critical Paths**: 100% (You.com API integration, Impact Card generation)
- **Business Logic**: ≥95%
- **UI Components**: ≥85%

### Coverage Reporting

```bash
# Backend coverage
pytest --cov=app --cov-report=html tests/
open htmlcov/index.html

# Frontend coverage
npm run test:coverage
open coverage/lcov-report/index.html

# Combined coverage report
npm run coverage:combined
```

### Coverage Exclusions

```python
# .coveragerc
[run]
omit =
    */tests/*
    */migrations/*
    */venv/*
    */node_modules/*
    */build/*
    */dist/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## 🚨 Test Data Management

### Fixtures and Factories

**Test Data Factory**:

```python
import factory
from app.models import WatchItem, ImpactCard

class WatchItemFactory(factory.Factory):
    class Meta:
        model = WatchItem

    name = factory.Sequence(lambda n: f"Company {n}")
    keywords = ["AI", "ML", "Tech"]
    created_at = factory.Faker('date_time')

class ImpactCardFactory(factory.Factory):
    class Meta:
        model = ImpactCard

    watch_item = factory.SubFactory(WatchItemFactory)
    risk_score = factory.Faker('random_int', min=0, max=100)
    impact_areas = ["Product", "Market"]
```

### Database Seeding

**Test Data Seeding**:

```python
def seed_test_data(db_session):
    """Seed database with test data"""
    # Create test watchlist items
    watch_items = WatchItemFactory.create_batch(5)
    db_session.add_all(watch_items)

    # Create test impact cards
    impact_cards = [
        ImpactCardFactory.create(watch_item=item)
        for item in watch_items
    ]
    db_session.add_all(impact_cards)

    db_session.commit()
    return watch_items, impact_cards
```

## 🔄 Continuous Integration

### GitHub Actions Workflow

**.github/workflows/test.yml**:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run tests
        run: pytest --cov=app tests/
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
          YOU_API_KEY: ${{ secrets.YOU_API_KEY }}

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm run test:coverage

      - name: Run E2E tests
        run: npm run test:e2e
```

## 🎯 Performance Testing

### Load Testing

**Artillery Configuration**:

```yaml
# artillery.yml
config:
  target: "http://localhost:8765"
  phases:
    - duration: 60
      arrivalRate: 10
    - duration: 120
      arrivalRate: 50
    - duration: 60
      arrivalRate: 100

scenarios:
  - name: "API Load Test"
    requests:
      - get:
          url: "/api/v1/watch/"
      - post:
          url: "/api/v1/impact/generate"
          json:
            watch_item_id: 1
```

**Running Load Tests**:

```bash
# Install Artillery
npm install -g artillery

# Run load test
artillery run artillery.yml

# Generate HTML report
artillery run --output report.json artillery.yml
artillery report report.json
```

## 🐛 Debugging Tests

### Common Issues

**Test Database Issues**:

```bash
# Reset test database
dropdb test_cia_db
createdb test_cia_db
alembic upgrade head
```

**Mock Issues**:

```python
# Debug mock calls
mock_you_client.assert_called_with(expected_args)
print(mock_you_client.call_args_list)
```

**Async Test Issues**:

```python
# Use pytest-asyncio for async tests
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Test Debugging Tools

- **pytest-pdb**: Interactive debugging
- **pytest-xvfb**: Headless browser testing
- **pytest-html**: HTML test reports
- **pytest-cov**: Coverage reporting

## 📋 Test Checklist

### Pre-Commit Checklist

- [ ] All tests pass locally
- [ ] Coverage meets minimum thresholds
- [ ] No test warnings or deprecations
- [ ] Mock objects properly configured
- [ ] Test data properly cleaned up

### Release Testing Checklist

- [ ] Full test suite passes
- [ ] Integration tests with real APIs
- [ ] E2E tests in multiple browsers
- [ ] Performance tests meet SLAs
- [ ] Security tests pass
- [ ] Load tests complete successfully

---

## 📞 Support

**Test Issues**: Check test logs and error messages  
**CI/CD Problems**: Review GitHub Actions workflow logs  
**Coverage Issues**: Use coverage reports to identify gaps  
**Performance Problems**: Run load tests and profiling

**Questions?** Review test documentation or contact the development team.

---

**Last Updated**: October 30, 2025  
**Maintained By**: Enterprise CIA Development Team  
**Test Coverage**: 90%+ across all components
