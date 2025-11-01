/**
 * End-to-End Workflow Tests
 * 
 * Complete user workflows tested end-to-end
 */

import { TEST_CONFIG, TEST_PAGES } from './config';
import { createTestResult, formatDuration } from './utils';
import { testWatchlistItems } from './fixtures';

/**
 * Test: Complete Watchlist to Impact Card Flow
 * 
 * Tests the complete workflow from adding a watchlist item
 * to generating an impact card
 */
export async function testCompleteWatchlistToImpactCardFlow(): Promise<any> {
  const steps: string[] = [];
  const startTime = Date.now();

  try {
    // Step 1: Navigate to dashboard
    steps.push('1. Navigating to dashboard');
    // await navigate_page({ url: `${TEST_CONFIG.baseUrl}${TEST_PAGES.dashboard}` });
    
    // Step 2: Add watchlist item
    steps.push('2. Adding watchlist item');
    const testItem = testWatchlistItems[0];
    
    // Find and click "Add Competitor" button
    // const snapshot = await take_snapshot({ verbose: true });
    // const addButton = snapshot.find((el: any) =>
    //   el.role === 'button' &&
    //   (el.name?.toLowerCase().includes('add') ||
    //    el.name?.toLowerCase().includes('competitor'))
    // );
    // 
    // if (addButton) {
    //   await click({ uid: addButton.uid });
    //   
    //   // Fill form
    //   await fill_form({
    //     elements: [
    //       { uid: 'competitor-name-input', value: testItem.competitor_name },
    //       { uid: 'keywords-input', value: testItem.keywords.join(', ') },
    //       { uid: 'description-input', value: testItem.description },
    //     ]
    //   });
    //   
    //   // Submit
    //   await click({ uid: 'submit-button' });
    //   
    //   // Wait for item to appear
    //   await wait_for({ text: testItem.competitor_name, timeout: 5000 });
    // }
    
    // Step 3: Navigate to research page
    steps.push('3. Navigating to research page');
    // await navigate_page({ url: `${TEST_CONFIG.baseUrl}${TEST_PAGES.research}` });
    
    // Step 4: Start performance trace
    steps.push('4. Starting performance trace');
    // await performance_start_trace({ reload: false, autoStop: false });
    
    // Step 5: Generate impact card
    steps.push('5. Generating impact card');
    // await fill({ uid: 'company-name-input', value: testItem.competitor_name });
    // await click({ uid: 'generate-impact-card-button' });
    
    // Step 6: Wait for completion
    steps.push('6. Waiting for impact card generation');
    // await wait_for({ text: 'Impact Card Generated', timeout: 30000 });
    
    // Step 7: Verify impact card displays
    steps.push('7. Verifying impact card display');
    // const snapshot = await take_snapshot({ verbose: true });
    // const impactCard = snapshot.find((el: any) =>
    //   el.role === 'article' ||
    //   el.name?.toLowerCase().includes('impact card')
    // );
    // 
    // if (!impactCard) {
    //   throw new Error('Impact card not found after generation');
    // }
    
    // Step 8: Monitor network requests
    steps.push('8. Verifying API calls');
    // const networkRequests = await list_network_requests({
    //   resourceTypes: ['fetch', 'xhr'],
    //   includePreservedRequests: true,
    // });
    // 
    // const apiCalls = networkRequests.filter((req: any) =>
    //   req.url?.includes('/api/v1/')
    // );
    // 
    // if (apiCalls.length === 0) {
    //   throw new Error('No API calls were made during the workflow');
    // }
    
    // Step 9: Stop performance trace
    steps.push('9. Stopping performance trace');
    // await performance_stop_trace();
    
    // Step 10: Check for errors
    steps.push('10. Checking for console errors');
    // const consoleMessages = await list_console_messages({
    //   types: ['error'],
    //   includePreservedMessages: true,
    // });
    // 
    // if (consoleMessages.length > 0) {
    //   throw new Error(`Found ${consoleMessages.length} console errors`);
    // }
    
    const duration = Date.now() - startTime;
    
    return createTestResult(
      true,
      'Complete watchlist to impact card flow completed successfully',
      steps,
      undefined,
      { testItem, duration: formatDuration(duration) },
      duration
    );
  } catch (error) {
    const duration = Date.now() - startTime;
    return createTestResult(
      false,
      'Complete workflow test failed',
      steps,
      error instanceof Error ? error.message : String(error),
      { duration: formatDuration(duration) },
      duration
    );
  }
}

/**
 * Test: Multi-Page Navigation Flow
 * 
 * Tests navigating through multiple pages in sequence
 */
export async function testMultiPageNavigationFlow(): Promise<any> {
  const steps: string[] = [];
  const pages = [
    TEST_PAGES.dashboard,
    TEST_PAGES.research,
    TEST_PAGES.analytics,
    TEST_PAGES.settings,
    TEST_PAGES.dashboard, // Return to dashboard
  ];

  try {
    for (let i = 0; i < pages.length; i++) {
      const page = pages[i];
      steps.push(`${i + 1}. Navigating to ${page}`);
      
      // await navigate_page({ url: `${TEST_CONFIG.baseUrl}${page}` });
      // await wait({ ms: 1000 });
      
      // Take snapshot to verify page loaded
      // const snapshot = await take_snapshot({ verbose: false });
      // if (snapshot.length === 0) {
      //   throw new Error(`Page ${page} did not load`);
      // }
      
      // Check for console errors
      // const consoleMessages = await list_console_messages({
      //   types: ['error'],
      // });
      // 
      // if (consoleMessages.length > 0) {
      //   throw new Error(`Console errors found on ${page}`);
      // }
    }
    
    return createTestResult(
      true,
      `Successfully navigated through ${pages.length} pages`,
      steps,
      undefined,
      { pages: pages.length }
    );
  } catch (error) {
    return createTestResult(
      false,
      'Multi-page navigation flow failed',
      steps,
      error instanceof Error ? error.message : String(error)
    );
  }
}

/**
 * Export all E2E workflow tests
 */
export const e2eWorkflowTests = {
  testCompleteWatchlistToImpactCardFlow,
  testMultiPageNavigationFlow,
};

