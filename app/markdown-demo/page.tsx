"use client";

import MarkdownRenderer from "@/components/MarkdownRenderer";

const sampleAriReport = `# Deep Research Analysis: Perplexity AI

## Executive Summary

Perplexity AI demonstrates **exceptional competitive positioning** in the conversational search market. Our analysis of 400+ sources reveals rapid growth trajectory, innovative AI capabilities, and strategic market expansion opportunities.

### Key Metrics
- **Valuation**: $3B+ (Series B funding)
- **Growth Rate**: 300%+ YoY user growth
- **Market Position**: Leading AI-powered search platform

## Competitive Landscape Analysis

> "Perplexity is redefining how users interact with information, combining the best of search engines and conversational AI." - TechCrunch Analysis

### Major Competitors

| Company | Market Share | Strengths | Weaknesses |
|---------|-------------|-----------|------------|
| Google Search | 92% | Massive index, speed | Static results |
| ChatGPT | 15% | Conversational | No real-time data |
| Bing Chat | 8% | Microsoft integration | Limited adoption |

### Competitive Advantages

1. **Real-time Information**: Unlike ChatGPT, provides current data
2. **Source Citations**: Transparent sourcing builds trust
3. **Conversational Interface**: More intuitive than traditional search
4. **Mobile-First Design**: Optimized for modern usage patterns

## Technical Innovation

### AI Architecture
\`\`\`python
# Perplexity's approach combines multiple AI models
def search_and_synthesize(query):
    # 1. Retrieve relevant sources
    sources = web_search(query)
    
    # 2. Process with LLM
    context = extract_context(sources)
    
    # 3. Generate response with citations
    response = llm_generate(query, context)
    
    return response_with_citations(response, sources)
\`\`\`

### Key Features
- **Multi-source synthesis**: Combines information from multiple sources
- **Real-time updates**: Fresh information from the web
- **Citation tracking**: Full transparency on source material
- **Follow-up questions**: Contextual conversation flow

## Market Opportunity

### Total Addressable Market (TAM)
- **Search Market**: $200B+ globally
- **AI Assistant Market**: $50B+ by 2027
- **Enterprise Search**: $15B+ opportunity

### Growth Drivers
1. **Consumer Adoption**: Shift from traditional search
2. **Enterprise Integration**: B2B search solutions
3. **API Monetization**: Developer platform expansion
4. **International Expansion**: Global market penetration

## Strategic Recommendations

### Immediate Actions (0-3 months)
- ✅ **Monitor product releases** - Track new features and capabilities
- ✅ **Analyze user adoption** - Watch growth metrics and engagement
- ✅ **Competitive benchmarking** - Compare response quality and speed

### Medium-term Strategy (3-12 months)
- 🔄 **Enterprise positioning** - Develop B2B competitive response
- 🔄 **API strategy** - Consider developer platform implications
- 🔄 **Partnership monitoring** - Track strategic alliances

### Long-term Considerations (12+ months)
- 📊 **Market consolidation** - Potential acquisition scenarios
- 📊 **Technology evolution** - Next-generation AI capabilities
- 📊 **Regulatory landscape** - AI governance and compliance

## Risk Assessment

### High-Impact Risks
- ⚠️ **Google Response**: Search giant's competitive reaction
- ⚠️ **Funding Challenges**: Maintaining growth trajectory
- ⚠️ **Technical Scaling**: Infrastructure and cost management

### Mitigation Strategies
- **Differentiation**: Maintain unique value proposition
- **Partnerships**: Strategic alliances for distribution
- **Innovation**: Continuous product development

## Financial Analysis

### Funding History
- **Series A**: $25M (2022)
- **Series B**: $73.6M (2023) 
- **Current Valuation**: $3B+ (2024)

### Revenue Model
- **Subscription Plans**: Pro tier at $20/month
- **Enterprise Licensing**: Custom B2B solutions
- **API Access**: Developer platform monetization

## Sources & Methodology

This comprehensive analysis synthesizes information from **400+ verified sources** including:

- 📰 **News Articles**: TechCrunch, The Information, Bloomberg
- 📊 **Financial Reports**: Funding announcements, valuation data
- 🔬 **Technical Analysis**: Product reviews, feature comparisons
- 👥 **User Feedback**: App store reviews, social media sentiment
- 🏢 **Industry Reports**: Market research, competitive analysis

### Source Quality Distribution
- **Tier 1 Sources (WSJ, Bloomberg)**: 35%
- **Tier 2 Sources (TechCrunch, VentureBeat)**: 40%
- **Tier 3 Sources (Verified blogs, forums)**: 25%

---

*Report generated using You.com ARI API with comprehensive source verification and real-time data synthesis*

**Confidence Score**: 92% | **Last Updated**: October 31, 2024 | **Sources**: 400+`;

const beforeExample = `Deep Research Analysis (You.com ARI API)

Comprehensive analysis of Perplexity AI reveals strong competitive positioning in the current market landscape. Analysis of 400+ sources shows significant growth trajectory, innovative product development, and strategic market expansion. Key opportunities include emerging AI capabilities, enterprise adoption, and international expansion.

Perplexity AI demonstrates exceptional competitive positioning in the conversational search market. Our analysis of 400+ sources reveals rapid growth trajectory, innovative AI capabilities, and strategic market expansion opportunities. Key Metrics - Valuation: $3B+ (Series B funding) - Growth Rate: 300%+ YoY user growth - Market Position: Leading AI-powered search platform

Major Competitors Company Market Share Strengths Weaknesses Google Search 92% Massive index, speed Static results ChatGPT 15% Conversational No real-time data Bing Chat 8% Microsoft integration Limited adoption

[Text continues without proper formatting, no scrolling, content gets cut off...]`;

export default function MarkdownDemoPage() {
  return (
    <div className="container mx-auto p-8 max-w-6xl">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <h1 className="text-3xl font-bold">
            ARI Report Display: Before vs After
          </h1>
          <span className="px-3 py-1 bg-purple-100 text-purple-800 text-sm font-semibold rounded-full border border-purple-300">
            🎨 DEMO PAGE
          </span>
        </div>
        <div className="bg-purple-50 border-l-4 border-purple-400 p-4 mb-6 rounded-r">
          <p className="text-purple-800 text-sm font-medium mb-2">
            ⚠️ Demo Mode: This page demonstrates markdown rendering capabilities with static sample data.
          </p>
          <p className="text-gray-600 text-sm">
            Demonstrating the improvement in Deep Research Analysis (You.com ARI
            API) display with proper markdown rendering and scrolling.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Before - Raw Text Display */}
        <div>
          <h2 className="text-xl font-semibold mb-4 text-red-600">
            ❌ Before: Raw Text (Current Issue)
          </h2>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
              Deep Research Analysis (You.com ARI API)
            </h4>
            <div className="p-4 bg-gray-50 rounded-lg max-h-96 overflow-hidden">
              <div className="space-y-3">
                <p className="text-sm text-gray-700 leading-relaxed">
                  {beforeExample}
                </p>
              </div>
            </div>
            <div className="mt-2 text-xs text-red-600">
              ⚠️ Issues: No markdown formatting, text cuts off, no scrolling, no
              copy functionality
            </div>
          </div>
        </div>

        {/* After - Markdown Renderer */}
        <div>
          <h2 className="text-xl font-semibold mb-4 text-green-600">
            ✅ After: Markdown Renderer (Fixed)
          </h2>
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <h4 className="font-semibold text-gray-900 flex items-center">
                Deep Research Analysis (You.com ARI API)
              </h4>
            </div>
            <MarkdownRenderer
              content={sampleAriReport}
              className="p-4"
              maxHeight="max-h-96"
              showCopyButton={true}
            />
            <div className="p-2 text-xs text-green-600 border-t border-gray-200">
              ✅ Features: Proper markdown formatting, scrollable content, copy
              button, syntax highlighting
            </div>
          </div>
        </div>
      </div>

      {/* Feature Comparison */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold mb-6">Feature Comparison</h2>
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Feature
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Before
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  After
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Markdown Formatting
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-red-600">
                  ❌
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-green-600">
                  ✅
                </td>
              </tr>
              <tr className="bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Scrollable Content
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-red-600">
                  ❌
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-green-600">
                  ✅
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Copy Functionality
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-red-600">
                  ❌
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-green-600">
                  ✅
                </td>
              </tr>
              <tr className="bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Syntax Highlighting
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-red-600">
                  ❌
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-green-600">
                  ✅
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Table Formatting
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-red-600">
                  ❌
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-green-600">
                  ✅
                </td>
              </tr>
              <tr className="bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  External Links
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-red-600">
                  ❌
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-green-600">
                  ✅
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  Content Truncation
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-red-600">
                  ❌ (Cuts off)
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-green-600">
                  ✅ (Full content)
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Implementation Details */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold mb-6">Implementation Details</h2>
        <div className="bg-gray-900 text-gray-100 p-6 rounded-lg">
          <h3 className="text-lg font-semibold mb-4 text-green-400">
            Key Changes Made:
          </h3>
          <ul className="space-y-2 text-sm">
            <li>
              • <span className="text-blue-400">Added react-markdown</span> with
              GitHub Flavored Markdown support
            </li>
            <li>
              •{" "}
              <span className="text-blue-400">
                Implemented scrollable containers
              </span>{" "}
              with custom scrollbar styling
            </li>
            <li>
              •{" "}
              <span className="text-blue-400">
                Added copy-to-clipboard functionality
              </span>{" "}
              with visual feedback
            </li>
            <li>
              • <span className="text-blue-400">Enhanced table rendering</span>{" "}
              with proper styling and overflow handling
            </li>
            <li>
              • <span className="text-blue-400">Added syntax highlighting</span>{" "}
              for code blocks using highlight.js
            </li>
            <li>
              • <span className="text-blue-400">Improved link handling</span>{" "}
              with external link indicators
            </li>
            <li>
              • <span className="text-blue-400">Responsive design</span> that
              works on all screen sizes
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
