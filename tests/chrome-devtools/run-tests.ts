#!/usr/bin/env ts-node
/**
 * Chrome DevTools MCP Test Runner
 * 
 * Main entry point for running all test suites
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { functionalTests } from './functional-tests';
import { performanceTests } from './performance-suite';
import { accessibilityTests } from './accessibility-suite';
import { TEST_CONFIG } from './config';
import { createTestResult } from './utils';

interface TestReport {
  summary: {
    total: number;
    passed: number;
    failed: number;
    duration: number;
  };
  results: Array<{
    name: string;
    success: boolean;
    message: string;
    duration?: number;
    error?: string;
    data?: any;
  }>;
  timestamp: string;
  config: {
    baseUrl: string;
    backendUrl: string;
  };
}

const TEST_RESULTS_DIR = join(__dirname, 'results');
const TEST_SCREENSHOTS_DIR = join(__dirname, 'screenshots');

/**
 * Initialize test directories
 */
function initializeDirectories() {
  try {
    mkdirSync(TEST_RESULTS_DIR, { recursive: true });
    mkdirSync(TEST_SCREENSHOTS_DIR, { recursive: true });
    console.log('✅ Test directories initialized');
  } catch (error) {
    console.error('❌ Failed to create test directories:', error);
  }
}

/**
 * Run a single test
 */
async function runTest(
  name: string,
  testFn: () => Promise<any>
): Promise<{ name: string; result: any }> {
  console.log(`\n🧪 Running: ${name}`);
  const startTime = Date.now();
  
  try {
    const result = await testFn();
    const duration = Date.now() - startTime;
    
    if (result.success) {
      console.log(`✅ ${name} - PASSED (${result.duration || duration}ms)`);
    } else {
      console.log(`❌ ${name} - FAILED (${result.duration || duration}ms)`);
      if (result.error) {
        console.log(`   Error: ${result.error}`);
      }
    }
    
    return {
      name,
      result: {
        ...result,
        duration: result.duration || duration,
      },
    };
  } catch (error) {
    const duration = Date.now() - startTime;
    console.log(`❌ ${name} - ERROR (${duration}ms)`);
    console.log(`   Error: ${error instanceof Error ? error.message : String(error)}`);
    
    return {
      name,
      result: createTestResult(
        false,
        'Test execution failed',
        [],
        error instanceof Error ? error.message : String(error),
        undefined,
        duration
      ),
    };
  }
}

/**
 * Run functional tests
 */
async function runFunctionalTests(): Promise<any[]> {
  console.log('\n📋 Running Functional Tests');
  console.log('='.repeat(50));
  
  const tests = [
    { name: 'Watchlist Management Flow', fn: functionalTests.testWatchlistManagementFlow },
    { name: 'Impact Card Generation', fn: functionalTests.testImpactCardGeneration },
    { name: 'API Endpoint Health', fn: functionalTests.testAPIEndpointHealth },
    { name: 'Navigation Flow', fn: functionalTests.testNavigationFlow },
  ];
  
  const results = [];
  for (const test of tests) {
    const result = await runTest(test.name, test.fn);
    results.push(result);
  }
  
  return results;
}

/**
 * Run performance tests
 */
async function runPerformanceTests(): Promise<any[]> {
  console.log('\n⚡ Running Performance Tests');
  console.log('='.repeat(50));
  
  const tests = [
    { name: 'Performance Benchmark Suite', fn: performanceTests.testPerformanceBenchmark },
    { name: 'Impact Card Generation Performance', fn: performanceTests.testImpactCardGenerationPerformance },
    { name: 'Network Request Performance', fn: performanceTests.testNetworkRequestPerformance },
  ];
  
  const results = [];
  for (const test of tests) {
    const result = await runTest(test.name, test.fn);
    results.push(result);
  }
  
  return results;
}

/**
 * Run accessibility tests
 */
async function runAccessibilityTests(): Promise<any[]> {
  console.log('\n♿ Running Accessibility Tests');
  console.log('='.repeat(50));
  
  const tests = [
    { name: 'Accessibility Compliance Suite', fn: accessibilityTests.testAccessibilityCompliance },
  ];
  
  const results = [];
  for (const test of tests) {
    const result = await runTest(test.name, test.fn);
    results.push(result);
  }
  
  return results;
}

/**
 * Generate test report
 */
function generateReport(allResults: any[]): TestReport {
  const passed = allResults.filter((r: any) => r.result.success).length;
  const failed = allResults.length - passed;
  const totalDuration = allResults.reduce(
    (sum: number, r: any) => sum + (r.result.duration || 0),
    0
  );
  
  const report: TestReport = {
    summary: {
      total: allResults.length,
      passed,
      failed,
      duration: totalDuration,
    },
    results: allResults.map((r: any) => ({
      name: r.name,
      success: r.result.success,
      message: r.result.message,
      duration: r.result.duration,
      error: r.result.error,
      data: r.result.data,
    })),
    timestamp: new Date().toISOString(),
    config: {
      baseUrl: TEST_CONFIG.baseUrl,
      backendUrl: TEST_CONFIG.backendUrl,
    },
  };
  
  return report;
}

/**
 * Save test report
 */
function saveReport(report: TestReport) {
  const reportPath = join(TEST_RESULTS_DIR, `report-${Date.now()}.json`);
  writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\n📄 Test report saved to: ${reportPath}`);
  return reportPath;
}

/**
 * Print test summary
 */
function printSummary(report: TestReport) {
  console.log('\n' + '='.repeat(50));
  console.log('📊 Test Summary');
  console.log('='.repeat(50));
  console.log(`Total Tests: ${report.summary.total}`);
  console.log(`Passed: ${report.summary.passed} ✅`);
  console.log(`Failed: ${report.summary.failed} ${report.summary.failed > 0 ? '❌' : ''}`);
  console.log(`Duration: ${(report.summary.duration / 1000).toFixed(2)}s`);
  console.log(`\nTimestamp: ${report.timestamp}`);
  console.log(`Base URL: ${report.config.baseUrl}`);
  console.log(`Backend URL: ${report.config.backendUrl}`);
  
  if (report.summary.failed > 0) {
    console.log('\n❌ Failed Tests:');
    report.results
      .filter((r: any) => !r.success)
      .forEach((r: any) => {
        console.log(`  - ${r.name}: ${r.error || r.message}`);
      });
  }
}

/**
 * Main test runner
 */
async function main() {
  const args = process.argv.slice(2);
  const testType = args[0] || 'all';
  
  console.log('🚀 Chrome DevTools MCP Test Runner');
  console.log('='.repeat(50));
  console.log(`Test Type: ${testType}`);
  console.log(`Base URL: ${TEST_CONFIG.baseUrl}`);
  console.log(`Backend URL: ${TEST_CONFIG.backendUrl}`);
  
  // Initialize directories
  initializeDirectories();
  
  const allResults: any[] = [];
  
  try {
    // Run tests based on type
    if (testType === 'all' || testType === 'functional') {
      const results = await runFunctionalTests();
      allResults.push(...results);
    }
    
    if (testType === 'all' || testType === 'performance') {
      const results = await runPerformanceTests();
      allResults.push(...results);
    }
    
    if (testType === 'all' || testType === 'accessibility') {
      const results = await runAccessibilityTests();
      allResults.push(...results);
    }
    
    // Generate and save report
    const report = generateReport(allResults);
    saveReport(report);
    printSummary(report);
    
    // Exit with appropriate code
    process.exit(report.summary.failed > 0 ? 1 : 0);
  } catch (error) {
    console.error('\n❌ Test runner failed:', error);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { main as runTests };

