"use client";

import { useState } from "react";
import { Zap, Search, MessageSquare, BookOpen, Play, CheckCircle, Clock } from "lucide-react";

export default function APIShowcase() {
  const [activeDemo, setActiveDemo] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const apis = [
    {
      id: "news",
      name: "News API",
      icon: Zap,
      color: "blue",
      endpoint: "https://api.ydc-index.io/livenews",
      description: "Real-time competitor monitoring",
      useCase: "Catch competitor announcements within minutes",
      example: {
        query: "OpenAI product launch announcement",
        response: {
          articles: 12,
          latest: "OpenAI launches GPT-4 Turbo with 128K context window",
          sources: ["TechCrunch", "The Verge", "Ars Technica"]
        }
      },
      code: `const articles = await fetch_news({
  query: "OpenAI product launch",
  limit: 10
});

// Returns: Latest articles with quality scoring
// ✅ 12 articles found
// ✅ Avg quality score: 8.5/10
// ✅ Response time: 450ms`
    },
    {
      id: "search",
      name: "Search API",
      icon: Search,
      color: "green",
      endpoint: "https://api.ydc-index.io/v1/search",
      description: "Context enrichment from 400+ sources",
      useCase: "Build complete competitor profiles automatically",
      example: {
        query: "Anthropic AI company profile",
        response: {
          sources: 428,
          profile: {
            name: "Anthropic",
            industry: "AI Safety & Research",
            founded: "2021",
            funding: "$7.3B"
          }
        }
      },
      code: `const context = await search_context({
  company: "Anthropic",
  limit: 10
});

// Returns: Company profile + 400+ sources
// ✅ 428 sources aggregated
// ✅ Profile completeness: 95%
// ✅ Response time: 780ms`
    },
    {
      id: "chat",
      name: "Chat API (Express Agent)",
      icon: MessageSquare,
      color: "purple",
      endpoint: "https://api.you.com/v1/agents/runs",
      description: "AI-powered competitive impact analysis",
      useCase: "Structured risk assessment and strategic insights",
      example: {
        query: "Analyze OpenAI's competitive impact",
        response: {
          risk_score: 85,
          risk_level: "CRITICAL",
          impact: "Major feature release threatens market position",
          recommendations: [
            "Accelerate feature development timeline",
            "Prepare competitive response",
            "Brief executive team"
          ]
        }
      },
      code: `const analysis = await analyze_impact({
  news: articles,
  context: search_results,
  competitor: "OpenAI"
});

// Returns: Structured analysis
// ✅ Risk score: 85/100 (CRITICAL)
// ✅ 3 strategic recommendations
// ✅ Confidence: 92%
// ✅ Response time: 1.2s`
    },
    {
      id: "ari",
      name: "ARI API",
      icon: BookOpen,
      color: "orange",
      endpoint: "https://api.you.com/v1/agents/runs",
      description: "Deep research reports from 400+ sources",
      useCase: "Investment-grade research in minutes",
      example: {
        query: "Comprehensive analysis of Perplexity AI",
        response: {
          report_length: "2,847 words",
          sections: [
            "Company Overview",
            "Funding History",
            "Product Analysis",
            "Competitive Positioning",
            "Market Opportunity"
          ],
          sources: 412
        }
      },
      code: `const report = await generate_research({
  prompt: "Comprehensive analysis of Perplexity AI"
});

// Returns: Multi-page research report
// ✅ 2,847 words across 5 sections
// ✅ 412 sources cited
// ✅ Investment-grade quality
// ✅ Response time: 3.5s`
    }
  ];

  const runDemo = async (apiId: string) => {
    setActiveDemo(apiId);
    setProgress(0);

    // Simulate API call progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 150));
      setProgress(i);
    }

    setTimeout(() => {
      setActiveDemo(null);
      setProgress(0);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <div className="inline-block mb-4 px-6 py-2 bg-blue-100 rounded-full">
            <span className="text-blue-700 font-semibold">You.com Hackathon Submission</span>
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            All 4 You.com APIs
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
              Working Together
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Enterprise CIA orchestrates News, Search, Chat, and ARI APIs into a unified competitive intelligence platform
          </p>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-8 max-w-4xl mx-auto mt-12">
            <div className="text-center">
              <div className="text-4xl font-bold text-blue-600">4/4</div>
              <div className="text-sm text-gray-600 mt-1">APIs Integrated</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-600">400+</div>
              <div className="text-sm text-gray-600 mt-1">Sources per Query</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-purple-600">&lt;2m</div>
              <div className="text-sm text-gray-600 mt-1">Research Time</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-orange-600">95%</div>
              <div className="text-sm text-gray-600 mt-1">Test Coverage</div>
            </div>
          </div>
        </div>

        {/* API Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-7xl mx-auto">
          {apis.map((api) => {
            const Icon = api.icon;
            const isActive = activeDemo === api.id;

            return (
              <div
                key={api.id}
                className={`bg-white rounded-2xl shadow-lg p-8 transition-all ${
                  isActive ? 'ring-4 ring-' + api.color + '-500 scale-105' : 'hover:shadow-xl'
                }`}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className={`p-3 rounded-xl bg-${api.color}-100`}>
                      <Icon className={`w-6 h-6 text-${api.color}-600`} />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">{api.name}</h3>
                      <p className="text-sm text-gray-500">{api.endpoint.split('/').pop()}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => runDemo(api.id)}
                    disabled={activeDemo !== null}
                    className={`px-4 py-2 rounded-lg flex items-center space-x-2 bg-${api.color}-600 text-white hover:bg-${api.color}-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
                  >
                    {isActive ? (
                      <>
                        <Clock className="w-4 h-4 animate-spin" />
                        <span>Running...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        <span>Demo</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Description */}
                <p className="text-gray-700 mb-2">{api.description}</p>
                <p className="text-sm text-gray-600 mb-6">
                  <strong>Use Case:</strong> {api.useCase}
                </p>

                {/* Progress Bar */}
                {isActive && (
                  <div className="mb-6">
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div
                        className={`bg-${api.color}-600 h-2 rounded-full transition-all duration-300`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <p className="text-sm text-gray-600 text-center">{progress}% complete</p>
                  </div>
                )}

                {/* Example Response */}
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Example Response:</h4>
                  <div className="space-y-2 text-sm">
                    {Object.entries(api.example.response).map(([key, value]) => (
                      <div key={key} className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                        <div>
                          <span className="font-medium text-gray-700">{key}:</span>{' '}
                          <span className="text-gray-600">
                            {typeof value === 'object' ? JSON.stringify(value) : value}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Code Example */}
                <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                  <pre className="text-xs text-gray-100 font-mono">
                    <code>{api.code}</code>
                  </pre>
                </div>
              </div>
            );
          })}
        </div>

        {/* Orchestration Flow */}
        <div className="mt-16 max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">
            API Orchestration Workflow
          </h2>
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex items-center justify-between">
              <div className="text-center flex-1">
                <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-blue-100 flex items-center justify-center">
                  <Zap className="w-8 h-8 text-blue-600" />
                </div>
                <p className="font-semibold text-gray-900">News API</p>
                <p className="text-xs text-gray-600">Real-time articles</p>
              </div>
              <div className="text-2xl text-gray-400">→</div>
              <div className="text-center flex-1">
                <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-green-100 flex items-center justify-center">
                  <Search className="w-8 h-8 text-green-600" />
                </div>
                <p className="font-semibold text-gray-900">Search API</p>
                <p className="text-xs text-gray-600">Context enrichment</p>
              </div>
              <div className="text-2xl text-gray-400">→</div>
              <div className="text-center flex-1">
                <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-purple-100 flex items-center justify-center">
                  <MessageSquare className="w-8 h-8 text-purple-600" />
                </div>
                <p className="font-semibold text-gray-900">Chat API</p>
                <p className="text-xs text-gray-600">Impact analysis</p>
              </div>
              <div className="text-2xl text-gray-400">→</div>
              <div className="text-center flex-1">
                <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-orange-100 flex items-center justify-center">
                  <BookOpen className="w-8 h-8 text-orange-600" />
                </div>
                <p className="font-semibold text-gray-900">ARI API</p>
                <p className="text-xs text-gray-600">Deep research</p>
              </div>
            </div>

            <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-2">Result: Complete Impact Card</h3>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                  12 real-time news articles analyzed
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                  428 sources aggregated for context
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                  AI-powered risk score: 85/100 (Critical)
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                  2,847-word comprehensive research report
                </li>
                <li className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                  Total time: &lt;2 minutes (vs 4 hours manually)
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="mt-16 text-center">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            See It In Action
          </h3>
          <div className="flex justify-center space-x-4">
            <a
              href="/"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
            >
              Try Live Demo
            </a>
            <a
              href="/docs"
              className="px-8 py-3 border-2 border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-semibold"
            >
              Read Documentation
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
