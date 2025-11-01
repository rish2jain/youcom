/**
 * Test Fixtures
 * 
 * Reusable test data for Chrome DevTools MCP tests
 */

export interface WatchlistItem {
  competitor_name: string;
  keywords: string[];
  description: string;
  risk_threshold?: number;
}

export interface ImpactCardData {
  competitor_name: string;
  keywords: string[];
  description?: string;
}

export const testWatchlistItems: WatchlistItem[] = [
  {
    competitor_name: 'TestCorp',
    keywords: ['AI', 'ML', 'SaaS'],
    description: 'Test competitor for automated testing',
    risk_threshold: 5,
  },
  {
    competitor_name: 'DemoInc',
    keywords: ['Enterprise', 'Cloud'],
    description: 'Demo competitor for testing watchlist operations',
    risk_threshold: 3,
  },
  {
    competitor_name: 'SampleTech',
    keywords: ['Technology', 'Innovation'],
    description: 'Sample technology company for test scenarios',
    risk_threshold: 4,
  },
];

export const testImpactCardData: ImpactCardData[] = [
  {
    competitor_name: 'TestCorp',
    keywords: ['AI', 'Machine Learning'],
    description: 'Test company for impact card generation',
  },
  {
    competitor_name: 'Perplexity AI',
    keywords: ['Search', 'AI'],
    description: 'AI-powered search engine',
  },
];

export const testCompanyResearchData = [
  'Perplexity AI',
  'Anthropic',
  'OpenAI',
  'Stripe',
  'Notion',
];

/**
 * Generate unique test data with timestamps
 */
export function generateTestWatchlistItem(
  baseName: string = 'TestCorp'
): WatchlistItem {
  const timestamp = Date.now();
  return {
    competitor_name: `${baseName}_${timestamp}`,
    keywords: ['AI', 'ML', 'Testing'],
    description: `Automated test item created at ${new Date(timestamp).toISOString()}`,
    risk_threshold: 5,
  };
}

/**
 * Generate unique impact card data
 */
export function generateTestImpactCardData(
  baseName: string = 'TestCorp'
): ImpactCardData {
  const timestamp = Date.now();
  return {
    competitor_name: `${baseName}_${timestamp}`,
    keywords: ['AI', 'Machine Learning'],
    description: `Test impact card data generated at ${new Date(timestamp).toISOString()}`,
  };
}

