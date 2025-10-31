import React from "react";
import { useState } from "react";
import {
  BoltIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  QuestionMarkCircleIcon,
} from "@heroicons/react/24/outline";

interface DemoActionsProps {
  onGenerateDemo: () => Promise<void>;
  onResetDemo: () => Promise<void>;
  isLiveMode: boolean;
}

const DemoActions: React.FC<DemoActionsProps> = ({
  onGenerateDemo,
  onResetDemo,
  isLiveMode,
}) => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  const handleGenerateDemo = async () => {
    setLoading(true);
    setSuccess(false);

    try {
      await onGenerateDemo();
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error("Demo generation failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleResetDemo = async () => {
    setLoading(true);

    try {
      await onResetDemo();
    } catch (error) {
      console.error("Demo reset failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Try Sample Analysis
        </h3>
        <button
          onClick={() => setShowHelp(!showHelp)}
          className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
          title="Learn about demo mode"
        >
          <QuestionMarkCircleIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Help Text */}
      {showHelp && (
        <div className="mb-4 p-3 bg-white rounded-lg border border-blue-200">
          <p className="text-sm text-gray-700">
            Demo mode lets you explore all features with sample data. Switch to
            "Live Data" mode to connect to real You.com APIs for actual
            analysis.
          </p>
        </div>
      )}

      {/* Instructions */}
      <div className="mb-4 space-y-2">
        <div className="flex items-start space-x-3">
          <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white text-sm font-semibold rounded-full flex items-center justify-center">
            1
          </span>
          <p className="text-sm text-gray-700">
            Load sample competitive intelligence data to see all features in
            action
          </p>
        </div>
        <div className="flex items-start space-x-3">
          <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white text-sm font-semibold rounded-full flex items-center justify-center">
            2
          </span>
          <p className="text-sm text-gray-700">
            Explore Impact Cards, research reports, and analytics dashboards
          </p>
        </div>
        <div className="flex items-start space-x-3">
          <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white text-sm font-semibold rounded-full flex items-center justify-center">
            3
          </span>
          <p className="text-sm text-gray-700">
            Switch to Live Data mode when ready to analyze real companies
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-3">
        <button
          onClick={handleGenerateDemo}
          disabled={loading || isLiveMode}
          className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-semibold transition-colors ${
            loading || isLiveMode
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700"
          }`}
        >
          {loading ? (
            <>
              <ArrowPathIcon className="w-5 h-5 animate-spin" />
              <span>Generating sample data...</span>
            </>
          ) : success ? (
            <>
              <CheckCircleIcon className="w-5 h-5 text-green-500" />
              <span>Sample data loaded!</span>
            </>
          ) : (
            <>
              <BoltIcon className="w-5 h-5" />
              <span>Load Sample Analysis</span>
            </>
          )}
        </button>

        <button
          onClick={handleResetDemo}
          disabled={loading || isLiveMode}
          className={`w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg font-medium transition-colors ${
            loading || isLiveMode
              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          <ArrowPathIcon className="w-4 h-4" />
          <span>Reset to Clean State</span>
        </button>
      </div>

      {/* Status Messages */}
      {success && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-green-800">
              ✅ Demo data ready! Explore the features below.
            </span>
          </div>
        </div>
      )}

      {isLiveMode && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <BoltIcon className="w-5 h-5 text-yellow-600" />
            <span className="text-sm font-medium text-yellow-800">
              Live mode active - Using real You.com API data
            </span>
          </div>
        </div>
      )}

      {/* Progress Indicator */}
      {loading && (
        <div className="mt-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Generating sample data...</span>
            <span>Step 2 of 3</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full transition-all duration-1000 w-2/3"></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DemoActions;
