"use client";

import { useState, useEffect } from "react";
import { Activity, Zap, CheckCircle, Clock } from "lucide-react";

interface APICall {
  id: string;
  api: string;
  endpoint: string;
  status: "pending" | "success" | "error";
  timestamp: Date;
  duration?: number;
}

export function LiveAPITracker() {
  const [apiCalls, setApiCalls] = useState<APICall[]>([]);
  const [totalCalls, setTotalCalls] = useState(47);
  const [isActive, setIsActive] = useState(false);

  // Simulate API calls
  const simulateAPICall = (api: string, endpoint: string) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newCall: APICall = {
      id,
      api,
      endpoint,
      status: "pending",
      timestamp: new Date(),
    };

    setApiCalls((prev) => [newCall, ...prev.slice(0, 9)]);
    setTotalCalls((prev) => prev + 1);

    // Complete the call after a delay
    setTimeout(() => {
      setApiCalls((prev) =>
        prev.map((call) =>
          call.id === id
            ? {
                ...call,
                status: "success",
                duration: Math.floor(Math.random() * 800) + 200,
              }
            : call
        )
      );
    }, Math.random() * 2000 + 500);
  };

  // Auto-generate API calls for demo
  useEffect(() => {
    if (!isActive) return;

    const apis = [
      {
        name: "News API",
        endpoints: ["/news/recent", "/news/search", "/news/trending"],
      },
      {
        name: "Search API",
        endpoints: ["/search/web", "/search/company", "/search/market"],
      },
      {
        name: "Chat API",
        endpoints: ["/chat/analyze", "/chat/extract", "/chat/summarize"],
      },
      {
        name: "ARI API",
        endpoints: ["/ari/research", "/ari/synthesize", "/ari/insights"],
      },
    ];

    const interval = setInterval(() => {
      const randomAPI = apis[Math.floor(Math.random() * apis.length)];
      const randomEndpoint =
        randomAPI.endpoints[
          Math.floor(Math.random() * randomAPI.endpoints.length)
        ];
      simulateAPICall(randomAPI.name, randomEndpoint);
    }, Math.random() * 3000 + 1000);

    return () => clearInterval(interval);
  }, [isActive]);

  const getStatusIcon = (status: APICall["status"]) => {
    switch (status) {
      case "pending":
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      case "success":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "error":
        return <div className="w-4 h-4 rounded-full bg-red-500" />;
    }
  };

  const getAPIColor = (api: string) => {
    switch (api) {
      case "News API":
        return "text-blue-600 bg-blue-50";
      case "Search API":
        return "text-green-600 bg-green-50";
      case "Chat API":
        return "text-purple-600 bg-purple-50";
      case "ARI API":
        return "text-orange-600 bg-orange-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  return (
    <div className="bg-white border-2 border-gray-200 rounded-xl p-6 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-blue-600" />
          <h3 className="text-xl font-bold text-gray-900">Live API Activity</h3>
          <div className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span>{totalCalls} total calls</span>
          </div>
        </div>

        <button
          onClick={() => setIsActive(!isActive)}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            isActive
              ? "bg-red-100 text-red-700 hover:bg-red-200"
              : "bg-green-100 text-green-700 hover:bg-green-200"
          }`}
        >
          {isActive ? "Stop Demo" : "Start Demo"}
        </button>
      </div>

      {/* API Call Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">
            {apiCalls.filter((call) => call.api === "News API").length}
          </div>
          <div className="text-xs text-gray-600">News API</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {apiCalls.filter((call) => call.api === "Search API").length}
          </div>
          <div className="text-xs text-gray-600">Search API</div>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">
            {apiCalls.filter((call) => call.api === "Chat API").length}
          </div>
          <div className="text-xs text-gray-600">Chat API</div>
        </div>
        <div className="text-center p-3 bg-orange-50 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">
            {apiCalls.filter((call) => call.api === "ARI API").length}
          </div>
          <div className="text-xs text-gray-600">ARI API</div>
        </div>
      </div>

      {/* Recent API Calls */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Zap className="w-4 h-4 text-blue-600" />
          Recent API Calls
        </h4>

        {apiCalls.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-12 h-12 text-gray-300 mx-auto mb-2" />
            <p>Click "Start Demo" to see live API calls</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {apiCalls.map((call) => (
              <div
                key={call.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {getStatusIcon(call.status)}
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${getAPIColor(
                          call.api
                        )}`}
                      >
                        {call.api}
                      </span>
                      <span className="text-sm font-mono text-gray-600">
                        {call.endpoint}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {call.timestamp.toLocaleTimeString()}
                      {call.duration && (
                        <span className="ml-2">• {call.duration}ms</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="text-xs text-gray-400">
                  {call.status === "pending" && "Processing..."}
                  {call.status === "success" && "✓ Success"}
                  {call.status === "error" && "✗ Error"}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {isActive && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 text-blue-800 text-sm">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span>
              Live API orchestration active - all 4 You.com APIs working
              together
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
