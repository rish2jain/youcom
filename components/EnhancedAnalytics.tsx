"use client";

import { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  AlertTriangle,
  Target,
  Zap,
  BarChart3,
  PieChart,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
} from "recharts";

export function EnhancedAnalytics() {
  const [selectedTimeRange, setSelectedTimeRange] = useState("30d");
  const [isLoading, setIsLoading] = useState(true);

  // Sample data for demo
  const competitorActivityData = [
    { date: "2024-10-01", OpenAI: 8, Anthropic: 5, Google: 12, Meta: 3 },
    { date: "2024-10-08", OpenAI: 15, Anthropic: 8, Google: 10, Meta: 6 },
    { date: "2024-10-15", OpenAI: 12, Anthropic: 12, Google: 8, Meta: 4 },
    { date: "2024-10-22", OpenAI: 20, Anthropic: 15, Google: 14, Meta: 8 },
    { date: "2024-10-29", OpenAI: 18, Anthropic: 10, Google: 16, Meta: 5 },
  ];

  const threatScoreData = [
    { date: "Week 1", score: 6.2 },
    { date: "Week 2", score: 7.1 },
    { date: "Week 3", score: 8.8 },
    { date: "Week 4", score: 7.5 },
    { date: "Week 5", score: 8.2 },
  ];

  const marketShareData = [
    { name: "OpenAI", value: 35, color: "#3B82F6" },
    { name: "Google", value: 28, color: "#10B981" },
    { name: "Anthropic", value: 18, color: "#8B5CF6" },
    { name: "Meta", value: 12, color: "#F59E0B" },
    { name: "Others", value: 7, color: "#6B7280" },
  ];

  const apiUsageData = [
    { api: "News API", calls: 156, cost: 23.4, success: 98.7 },
    { api: "Search API", calls: 89, cost: 31.15, success: 100 },
    { api: "Chat API", calls: 67, cost: 45.2, success: 96.3 },
    { api: "ARI API", calls: 34, cost: 102.0, success: 94.1 },
  ];

  useEffect(() => {
    // Simulate loading
    setTimeout(() => setIsLoading(false), 1000);
  }, []);

  const formatCurrency = (value: number) => `$${value.toFixed(2)}`;

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-white p-6 rounded-xl shadow-sm animate-pulse"
          >
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Time Range Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">
          Analytics Dashboard
        </h2>
        <select
          value={selectedTimeRange}
          onChange={(e) => setSelectedTimeRange(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
        </select>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total API Calls</p>
              <p className="text-3xl font-bold text-gray-900">346</p>
              <p className="text-sm text-green-600 flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />
                +12% vs last month
              </p>
            </div>
            <Activity className="w-12 h-12 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Success Rate</p>
              <p className="text-3xl font-bold text-gray-900">97.3%</p>
              <p className="text-sm text-green-600 flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />
                +2.1% vs last month
              </p>
            </div>
            <Target className="w-12 h-12 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Threat Score</p>
              <p className="text-3xl font-bold text-gray-900">7.6/10</p>
              <p className="text-sm text-red-600 flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />
                +0.8 vs last month
              </p>
            </div>
            <AlertTriangle className="w-12 h-12 text-orange-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">API Costs</p>
              <p className="text-3xl font-bold text-gray-900">$201.75</p>
              <p className="text-sm text-green-600 flex items-center gap-1">
                <TrendingDown className="w-4 h-4" />
                -8% vs last month
              </p>
            </div>
            <Zap className="w-12 h-12 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Competitor Activity Trends */}
      <div className="bg-white p-6 rounded-xl shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            Competitor Activity Trends
          </h3>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span>Powered by News + Search APIs</span>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={competitorActivityData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="OpenAI"
              stroke="#3B82F6"
              strokeWidth={3}
            />
            <Line
              type="monotone"
              dataKey="Anthropic"
              stroke="#8B5CF6"
              strokeWidth={3}
            />
            <Line
              type="monotone"
              dataKey="Google"
              stroke="#10B981"
              strokeWidth={3}
            />
            <Line
              type="monotone"
              dataKey="Meta"
              stroke="#F59E0B"
              strokeWidth={3}
            />
          </LineChart>
        </ResponsiveContainer>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">83</div>
            <div className="text-sm text-gray-600">OpenAI Activities</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">50</div>
            <div className="text-sm text-gray-600">Anthropic Activities</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">60</div>
            <div className="text-sm text-gray-600">Google Activities</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">26</div>
            <div className="text-sm text-gray-600">Meta Activities</div>
          </div>
        </div>
      </div>

      {/* Threat Score Evolution */}
      <div className="bg-white p-6 rounded-xl shadow-sm">
        <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-orange-600" />
          Market Threat Score Evolution
        </h3>

        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={threatScoreData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis domain={[0, 10]} />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="score"
              stroke="#F59E0B"
              fill="#FEF3C7"
              strokeWidth={3}
            />
          </AreaChart>
        </ResponsiveContainer>

        <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
          <div className="flex items-center gap-2 text-orange-800 text-sm">
            <AlertTriangle className="w-4 h-4" />
            <span className="font-medium">
              Current threat level: HIGH (8.2/10)
            </span>
          </div>
          <p className="text-orange-700 text-sm mt-1">
            Increased competitive activity from OpenAI and Anthropic requires
            strategic response
          </p>
        </div>
      </div>

      {/* Market Share Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <PieChart className="w-6 h-6 text-green-600" />
            Market Share Analysis
          </h3>

          <ResponsiveContainer width="100%" height={250}>
            <RechartsPieChart>
              <Pie
                data={marketShareData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}%`}
              >
                {marketShareData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </RechartsPieChart>
          </ResponsiveContainer>
        </div>

        {/* API Usage & Costs */}
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Zap className="w-6 h-6 text-purple-600" />
            API Usage & Costs
          </h3>

          <div className="space-y-4">
            {apiUsageData.map((api, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">{api.api}</span>
                  <span className="text-sm text-gray-600">
                    {api.success}% success
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{api.calls} calls</span>
                  <span className="font-medium text-gray-900">
                    {formatCurrency(api.cost)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full"
                    style={{ width: `${api.success}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="text-sm text-purple-800">
              <div className="font-medium">Cost Optimization Insights:</div>
              <ul className="mt-2 space-y-1 text-xs">
                <li>
                  • ARI API: High value per call, optimize for complex queries
                </li>
                <li>
                  • News API: Most cost-effective, increase usage for monitoring
                </li>
                <li>• Caching reduced costs by 40% this month</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Strategic Recommendations */}
      <div className="bg-white p-6 rounded-xl shadow-sm">
        <h3 className="text-xl font-bold text-gray-900 mb-6">
          Strategic Recommendations
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <span className="font-bold text-red-900">High Priority</span>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Monitor OpenAI Closely
            </h4>
            <p className="text-sm text-gray-700">
              83 activities in 30 days indicates major product development.
              Increase monitoring frequency.
            </p>
          </div>

          <div className="p-4 bg-orange-50 border-l-4 border-orange-500 rounded-r-lg">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-orange-600" />
              <span className="font-bold text-orange-900">Medium Priority</span>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Anthropic Partnership Risk
            </h4>
            <p className="text-sm text-gray-700">
              Growing activity suggests potential partnerships. Assess strategic
              response options.
            </p>
          </div>

          <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-5 h-5 text-blue-600" />
              <span className="font-bold text-blue-900">Opportunity</span>
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Meta Underactivity
            </h4>
            <p className="text-sm text-gray-700">
              Low activity (26 events) may indicate market opportunity or
              strategic pivot.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
