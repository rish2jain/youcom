import React from "react";
import { useState, useEffect } from "react";
import {
  BoltIcon,
  DocumentTextIcon,
  QuestionMarkCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

interface APIToggleProps {
  useLiveData: boolean;
  onToggle: (useLive: boolean) => void;
  hasApiKey: boolean;
}

const APIToggle: React.FC<APIToggleProps> = ({
  useLiveData,
  onToggle,
  hasApiKey,
}) => {
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleToggle = () => {
    if (useLiveData) {
      // Switching to demo mode - show confirmation
      setShowConfirmation(true);
    } else {
      // Switching to live mode - check API key
      if (!hasApiKey) {
        alert("Please add your You.com API key in settings to use live data.");
        return;
      }
      onToggle(true);
    }
  };

  const confirmToggle = (confirm: boolean) => {
    setShowConfirmation(false);
    if (confirm) {
      onToggle(false);
    }
  };

  if (!mounted) {
    return (
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-3"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <label className="font-medium text-gray-900">Data Source</label>
          <button
            onClick={() => setShowHelp(!showHelp)}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <QuestionMarkCircleIcon className="w-4 h-4" />
          </button>
        </div>

        {/* Toggle Switch */}
        <button
          onClick={handleToggle}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
            useLiveData ? "bg-blue-600" : "bg-gray-300"
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              useLiveData ? "translate-x-6" : "translate-x-1"
            }`}
          />
        </button>
      </div>

      {/* Status Display */}
      <div className="mb-3">
        {useLiveData ? (
          <div className="flex items-center space-x-2">
            <BoltIcon className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-green-700">
              Live: Real You.com API data
            </span>
            {hasApiKey && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                Connected
              </span>
            )}
          </div>
        ) : (
          <div className="flex items-center space-x-2">
            <DocumentTextIcon className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-blue-700">
              Demo: Sample showcase data
            </span>
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
              Sample Data
            </span>
          </div>
        )}
      </div>

      {/* Description */}
      <div className="text-sm text-gray-600 mb-3">
        {useLiveData ? (
          <p>
            Using real-time data from You.com APIs for actual competitive
            intelligence analysis.
          </p>
        ) : (
          <p>
            Using curated sample data to demonstrate all platform features and
            capabilities.
          </p>
        )}
      </div>

      {/* API Key Warning */}
      {!hasApiKey && (
        <div className="flex items-start space-x-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg mb-3">
          <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-yellow-800">
              API Key Required
            </p>
            <p className="text-xs text-yellow-700 mt-1">
              Add your You.com API key in settings to enable live data mode.
            </p>
          </div>
        </div>
      )}

      {/* Help Section */}
      {showHelp && (
        <div className="p-3 bg-white border border-gray-200 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">
            Data Source Options
          </h4>
          <div className="space-y-2 text-sm text-gray-600">
            <div>
              <span className="font-medium text-blue-600">Demo Mode:</span>
              <p>
                Perfect for exploring features, demos, and training. Uses
                pre-loaded sample data.
              </p>
            </div>
            <div>
              <span className="font-medium text-green-600">Live Mode:</span>
              <p>
                Real competitive intelligence using You.com APIs. Requires valid
                API key.
              </p>
            </div>
          </div>
          <a
            href="/docs/api-setup"
            className="inline-block mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium"
          >
            Learn more about API setup →
          </a>
        </div>
      )}

      {/* Confirmation Dialog */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-md mx-4">
            <div className="flex items-start space-x-3 mb-4">
              <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-gray-900">
                  Switch to Demo Mode?
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  This will stop using live API data and switch to sample data.
                  Any current analysis will be replaced with demo content.
                </p>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => confirmToggle(true)}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Switch to Demo
              </button>
              <button
                onClick={() => confirmToggle(false)}
                className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg font-medium hover:bg-gray-200 transition-colors"
              >
                Keep Live Data
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default APIToggle;
