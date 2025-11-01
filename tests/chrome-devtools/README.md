# Chrome DevTools MCP Tests

This directory contains comprehensive tests using Chrome DevTools MCP for browser automation and testing.

## Setup

### 1. Install Chrome DevTools MCP

```bash
npm install -g chrome-devtools-mcp
```

### 2. Configure MCP Server

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

### 3. Environment Configuration

Copy `.env.test.example` to `.env.test` and update values:

```bash
cp .env.test.example .env.test
```

Or set environment variables:

```bash
export FRONTEND_URL=http://localhost:3456
export BACKEND_URL=http://localhost:8000
```

### 4. Install Dependencies

```bash
npm install
```

## Running Tests

### Run All Tests

```bash
npm run test:chrome-devtools
```

### Run Specific Test Suites

```bash
# Functional tests only
npm run test:chrome-devtools functional

# Performance tests only
npm run test:chrome-devtools performance

# Accessibility tests only
npm run test:chrome-devtools accessibility

# All tests
npm run test:chrome-devtools all
```

### Run Individual Test Suites

```bash
# Performance suite
npm run test:chrome-devtools:performance

# Accessibility suite
npm run test:chrome-devtools:accessibility
```

## Test Structure

```
tests/chrome-devtools/
├── config.ts                  # Test configuration
├── utils.ts                   # Test utilities and helpers
├── fixtures.ts                # Test data fixtures
├── functional-tests.ts        # Functional test suite
├── performance-suite.ts       # Performance benchmarking tests
├── accessibility-suite.ts     # Accessibility compliance tests
├── e2e-workflows.test.ts      # End-to-end workflow tests
├── run-tests.ts               # Main test runner
├── example-test.ts            # Example implementations (reference)
├── tsconfig.json              # TypeScript configuration
├── .env.test.example          # Environment variable template
├── results/                    # Test results (generated)
└── screenshots/               # Test screenshots (generated)
```

## Test Categories

### 1. Functional Tests
- Watchlist management flow
- Impact card generation
- API endpoint health checks
- Navigation flow

### 2. Performance Tests
- Core Web Vitals (LCP, FID, CLS, FCP, TTI)
- Page load performance
- API response times
- Impact card generation performance

### 3. Accessibility Tests
- WCAG 2.1 AA compliance
- ARIA compliance
- Keyboard navigation
- Screen reader compatibility

### 4. End-to-End Tests
- Complete watchlist to impact card flow
- Multi-page navigation workflows

## Test Results

Test results are saved to `tests/chrome-devtools/results/` as JSON files.

Reports include:
- Test summary (total, passed, failed, duration)
- Individual test results
- Performance metrics
- Accessibility issues
- Error messages and stack traces

## CI/CD Integration

Tests are automatically run in GitHub Actions on:
- Push to `main` or `develop` branches
- Pull requests to `main` branch
- Manual workflow dispatch

See `.github/workflows/chrome-devtools-tests.yml` for workflow configuration.

## Documentation

For detailed documentation, see:
- [Chrome DevTools MCP Testing Plan](../../docs/testing/chrome-devtools-mcp-testing-plan.md)

## Troubleshooting

### Tests Not Running

1. Verify Chrome DevTools MCP is installed: `npm list -g chrome-devtools-mcp`
2. Check environment variables are set correctly
3. Ensure frontend and backend services are running
4. Verify MCP server is configured in your client

### Tests Failing

1. Check test results in `tests/chrome-devtools/results/`
2. Verify services are accessible at configured URLs
3. Check console for error messages
4. Review test logs for specific failures

### Performance Tests Failing

1. Check Core Web Vitals thresholds in `config.ts`
2. Verify network conditions are stable
3. Ensure no heavy background processes are running
4. Check browser DevTools for performance bottlenecks
