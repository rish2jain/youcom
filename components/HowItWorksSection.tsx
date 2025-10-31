"use client";

import { ArrowDown, Code, Database, Zap } from "lucide-react";

interface WorkflowStepProps {
  stepNumber: number;
  icon: string;
  title: string;
  apiName: string;
  description: string;
  codeExample: string;
  bgColor: string;
  borderColor: string;
}

function WorkflowStep({
  stepNumber,
  icon,
  title,
  apiName,
  description,
  codeExample,
  bgColor,
  borderColor,
}: WorkflowStepProps) {
  return (
    <div
      className={`flex items-start gap-6 p-6 ${bgColor} border-2 ${borderColor} rounded-xl shadow-sm`}
    >
      <div
        className={`w-16 h-16 ${bgColor.replace(
          "50",
          "200"
        )} border-2 ${borderColor} rounded-xl flex items-center justify-center text-4xl flex-shrink-0 shadow-sm`}
      >
        {icon}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-3 mb-3">
          <span
            className={`w-8 h-8 ${borderColor.replace(
              "border",
              "bg"
            )} text-white rounded-full flex items-center justify-center text-sm font-bold`}
          >
            {stepNumber}
          </span>
          <h3 className="font-bold text-xl text-gray-900">{title}</h3>
        </div>
        <div className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Code className="w-4 h-4" />
          {apiName}
        </div>
        <p className="text-gray-700 leading-relaxed mb-4">{description}</p>
        <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
          <pre className="text-sm font-mono text-green-400 whitespace-pre-wrap">
            {codeExample}
          </pre>
        </div>
      </div>
    </div>
  );
}

function Connector() {
  return (
    <div className="flex justify-center my-6">
      <div className="flex flex-col items-center">
        <ArrowDown className="w-6 h-6 text-gray-400 animate-bounce" />
        <div className="w-1 h-8 bg-gradient-to-b from-gray-300 to-gray-400 rounded-full mt-2"></div>
      </div>
    </div>
  );
}

export function HowItWorksSection() {
  return (
    <div
      id="how-it-works"
      className="bg-white border-2 border-gray-200 rounded-xl p-8 scroll-mt-8 shadow-lg"
    >
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">
          How CIA Orchestrates You.com APIs
        </h2>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
          Four APIs working in perfect coordination to deliver complete
          competitive intelligence. Watch how real-time detection flows into
          deep synthesis.
        </p>
      </div>

      <div className="max-w-5xl mx-auto">
        <div className="relative">
          {/* Step 1: Real-Time Detection */}
          <WorkflowStep
            stepNumber={1}
            icon="📰"
            title="Real-Time Detection"
            apiName="News API"
            description="Continuously monitors news sources for competitor mentions, product launches, and strategic moves. Detection happens in under 60 seconds with intelligent filtering."
            codeExample={`// News API - Real-time monitoring
const news = await youNewsAPI.getRecent({
  query: "OpenAI GPT-4 launch",
  timeRange: "24h",
  sources: ["techcrunch", "reuters", "bloomberg"]
});
// Returns: 12 articles detected with relevance scoring`}
            bgColor="bg-blue-50"
            borderColor="border-blue-500"
          />

          <Connector />

          {/* Step 2: Context Enrichment */}
          <WorkflowStep
            stepNumber={2}
            icon="🔍"
            title="Context Enrichment"
            apiName="Search API"
            description="Enriches each signal with market context, pricing data, competitive positioning, and industry trends from across the web with intelligent source ranking."
            codeExample={`// Search API - Market context enrichment
const context = await youSearchAPI.search({
  query: "OpenAI pricing strategy competitive analysis",
  depth: "comprehensive",
  sourceTypes: ["news", "analysis", "official"]
});
// Returns: 8 high-quality sources with credibility scores`}
            bgColor="bg-green-50"
            borderColor="border-green-500"
          />

          <Connector />

          {/* Step 3: Strategic Analysis */}
          <WorkflowStep
            stepNumber={3}
            icon="🤖"
            title="Strategic Analysis"
            apiName="Chat API (Custom Agent)"
            description="Custom intelligence agent analyzes implications: What does this mean for your business? Calculates threat scores and generates strategic recommendations with confidence levels."
            codeExample={`// Chat API - Strategic analysis with custom agent
const analysis = await youChatAPI.analyze({
  agent: "competitive-intelligence-v2",
  context: { news, marketData: context },
  framework: "threat-assessment"
});
// Returns: Threat score (8.8/10) + strategic recommendations`}
            bgColor="bg-purple-50"
            borderColor="border-purple-500"
          />

          <Connector />

          {/* Step 4: Deep Synthesis */}
          <WorkflowStep
            stepNumber={4}
            icon="🧠"
            title="Deep Synthesis"
            apiName="ARI (Advanced Reasoning Intelligence)"
            description="Synthesizes comprehensive analysis across 400+ web sources, providing deep market intelligence, trend analysis, and evidence-based conclusions with full provenance."
            codeExample={`// ARI API - Deep synthesis across 400+ sources
const synthesis = await youARIAPI.synthesize({
  query: "OpenAI GPT-4 competitive market impact analysis",
  sources: 400,
  context: { news, search: context, analysis },
  depth: "comprehensive"
});
// Returns: Multi-dimensional analysis with source citations`}
            bgColor="bg-orange-50"
            borderColor="border-orange-500"
          />

          {/* Final Result */}
          <div className="mt-12">
            <div className="border-4 border-green-500 rounded-xl p-8 bg-gradient-to-r from-green-50 to-emerald-50 shadow-lg">
              <div className="flex items-start gap-6">
                <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Zap className="w-10 h-10 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-3xl text-gray-900 mb-3">
                    Complete Impact Card in &lt;3 Minutes
                  </h3>
                  <p className="text-lg text-gray-700 leading-relaxed mb-6">
                    Threat-scored analysis with strategic recommendations, 400+
                    source citations, and actionable next steps—ready to share
                    with stakeholders or integrate into your workflow via Slack,
                    Salesforce, or Notion.
                  </p>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="flex items-center gap-2 px-4 py-3 bg-white border-2 border-green-500 rounded-lg">
                      <Zap className="w-5 h-5 text-green-600" />
                      <div>
                        <div className="font-bold text-green-900">2-3 min</div>
                        <div className="text-xs text-green-700">Generation</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 px-4 py-3 bg-white border-2 border-green-500 rounded-lg">
                      <Database className="w-5 h-5 text-green-600" />
                      <div>
                        <div className="font-bold text-green-900">400+</div>
                        <div className="text-xs text-green-700">Sources</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 px-4 py-3 bg-white border-2 border-green-500 rounded-lg">
                      <div className="w-5 h-5 bg-green-600 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs font-bold">🎯</span>
                      </div>
                      <div>
                        <div className="font-bold text-green-900">8.8/10</div>
                        <div className="text-xs text-green-700">
                          Threat Score
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 px-4 py-3 bg-white border-2 border-green-500 rounded-lg">
                      <div className="w-5 h-5 bg-green-600 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs font-bold">📊</span>
                      </div>
                      <div>
                        <div className="font-bold text-green-900">92%</div>
                        <div className="text-xs text-green-700">Confidence</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
