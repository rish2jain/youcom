"use client";

import { useState } from "react";
import { Zap, Database, Wifi, WifiOff } from "lucide-react";

interface DemoModeToggleProps {
  onToggle?: (demoMode: boolean) => void;
}

export function DemoModeToggle({ onToggle }: DemoModeToggleProps) {
  const [demoMode, setDemoMode] = useState(false);

  const handleToggle = () => {
    const newMode = !demoMode;
    setDemoMode(newMode);
    onToggle?.(newMode);
  };

  return (
    <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border">
      <div className="flex items-center space-x-2">
        {demoMode ? (
          <Database className="w-4 h-4 text-purple-600" />
        ) : (
          <Wifi className="w-4 h-4 text-blue-600" />
        )}
        <span className="text-sm font-medium text-gray-700">
          {demoMode ? "Demo Mode" : "Live APIs"}
        </span>
      </div>

      <button
        onClick={handleToggle}
        role="switch"
        aria-checked={demoMode ? "true" : "false"}
        aria-label={`${demoMode ? "Disable" : "Enable"} demo mode`}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
          demoMode ? "bg-purple-600" : "bg-gray-200"
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            demoMode ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>

      <div className="text-xs text-gray-500">
        {demoMode ? (
          <span className="flex items-center space-x-1">
            <WifiOff className="w-3 h-3" />
            <span>Using demo data</span>
          </span>
        ) : (
          <span className="flex items-center space-x-1">
            <Zap className="w-3 h-3" />
            <span>Live You.com APIs</span>
          </span>
        )}
      </div>
    </div>
  );
}
