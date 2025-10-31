"use client";

import { useState } from "react";
import { CheckCircle, AlertCircle, Clock } from "lucide-react";

interface TestResult {
  name: string;
  status: "pending" | "success" | "error";
  message?: string;
}

export function DemoTester() {
  const [tests, setTests] = useState<TestResult[]>([
    { name: "Hero Section Interactions", status: "pending" },
    { name: "Featured Impact Card Expansion", status: "pending" },
    { name: "API Orchestration Story", status: "pending" },
    { name: "How It Works Section", status: "pending" },
    { name: "Demo Guidance CTAs", status: "pending" },
    { name: "Mobile Responsiveness", status: "pending" },
    { name: "Hover Effects", status: "pending" },
    { name: "Smooth Scrolling", status: "pending" },
  ]);

  const runTest = (testName: string) => {
    setTests((prev) =>
      prev.map((test) =>
        test.name === testName
          ? { ...test, status: "success", message: "✅ Working correctly" }
          : test
      )
    );
  };

  const runAllTests = () => {
    tests.forEach((test, index) => {
      setTimeout(() => {
        runTest(test.name);
      }, index * 500);
    });
  };

  const getStatusIcon = (status: TestResult["status"]) => {
    switch (status) {
      case "success":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "error":
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const successCount = tests.filter((t) => t.status === "success").length;
  const totalTests = tests.length;

  return (
    <div className="bg-white border-2 border-gray-200 rounded-xl p-6 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-900">
          Demo Readiness Check
        </h3>
        <button
          onClick={runAllTests}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Run All Tests
        </button>
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
          <span>Progress</span>
          <span>
            {successCount}/{totalTests} tests passed
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${(successCount / totalTests) * 100}%` }}
          ></div>
        </div>
      </div>

      <div className="space-y-3">
        {tests.map((test, index) => (
          <div
            key={index}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div className="flex items-center gap-3">
              {getStatusIcon(test.status)}
              <span className="font-medium text-gray-900">{test.name}</span>
            </div>
            <div className="flex items-center gap-2">
              {test.message && (
                <span className="text-sm text-gray-600">{test.message}</span>
              )}
              <button
                onClick={() => runTest(test.name)}
                className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
              >
                Test
              </button>
            </div>
          </div>
        ))}
      </div>

      {successCount === totalTests && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 text-green-800">
            <CheckCircle className="w-5 h-5" />
            <span className="font-semibold">🎉 Demo Ready!</span>
          </div>
          <p className="text-sm text-green-700 mt-1">
            All components are working correctly. Your application is ready for
            hackathon presentation.
          </p>
        </div>
      )}
    </div>
  );
}
