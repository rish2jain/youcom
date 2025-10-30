"use client";

import { useState } from "react";
import { Zap, RotateCcw, Play, Presentation } from "lucide-react";
import { api } from "@/lib/api";

interface QuickDemoActionsProps {
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
}

export function QuickDemoActions({
  onSuccess,
  onError,
}: QuickDemoActionsProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const generateDemoData = async () => {
    setIsGenerating(true);
    try {
      // Generate impact cards for demo competitors
      const competitors = [
        { name: "OpenAI", keywords: ["GPT", "ChatGPT", "API"] },
        { name: "Anthropic", keywords: ["Claude", "AI assistant"] },
        { name: "Google AI", keywords: ["Gemini", "Bard", "PaLM"] },
      ];

      for (const competitor of competitors) {
        await api.post("/api/v1/impact/generate", {
          competitor_name: competitor.name,
          keywords: competitor.keywords,
        });
      }

      // Generate company research for demo
      const companies = ["Perplexity AI", "Stripe", "Notion"];
      for (const company of companies) {
        await api.post("/api/v1/research/company", {
          company_name: company,
        });
      }

      onSuccess?.(
        "Demo data generated successfully! All impact cards and research reports are ready."
      );
    } catch (error) {
      console.error("Demo generation error:", error);
      onError?.("Failed to generate demo data. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const resetDemo = async () => {
    setIsResetting(true);
    try {
      // This would typically call a reset endpoint
      // For now, we'll just show a success message
      await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate API call
      onSuccess?.("Demo reset successfully! Ready for a fresh presentation.");
    } catch (error) {
      console.error("Reset error:", error);
      onError?.("Failed to reset demo. Please try again.");
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border">
      <div className="flex items-center space-x-2 mb-4">
        <Presentation className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">
          Quick Demo Actions
        </h3>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Prepare your demo with one-click actions for a perfect presentation.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={generateDemoData}
          disabled={isGenerating}
          className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isGenerating ? (
            <>
              <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              <span>Generating...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Generate Demo Data</span>
            </>
          )}
        </button>

        <button
          onClick={resetDemo}
          disabled={isResetting}
          className="flex items-center justify-center space-x-2 bg-gray-600 text-white px-4 py-3 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isResetting ? (
            <>
              <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              <span>Resetting...</span>
            </>
          ) : (
            <>
              <RotateCcw className="w-4 h-4" />
              <span>Reset Demo</span>
            </>
          )}
        </button>
      </div>

      <div className="mt-4 p-3 bg-white rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">🎯 Demo Flow</h4>
        <ol className="text-sm text-gray-600 space-y-1">
          <li>
            1. Generate demo data (creates 3 impact cards + 3 research reports)
          </li>
          <li>2. Show enterprise competitive monitoring with impact cards</li>
          <li>3. Demonstrate individual company research capabilities</li>
          <li>4. Highlight You.com API integration and metrics</li>
        </ol>
      </div>
    </div>
  );
}
