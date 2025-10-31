"use client";

import React, { useState } from "react";
import { X, Building2, Briefcase } from "lucide-react";

interface OnboardingModalProps {
  isOpen: boolean;
  onComplete: (data: { companyName: string; industry: string }) => void;
}

const INDUSTRIES = [
  "SaaS & Cloud Services",
  "Artificial Intelligence & ML",
  "E-commerce & Retail",
  "Financial Services & Fintech",
  "Healthcare & Life Sciences",
  "Enterprise Software",
  "Consumer Technology",
  "Media & Entertainment",
  "Cybersecurity",
  "Developer Tools & Infrastructure",
  "Marketing & Advertising Technology",
  "Other",
];

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  isOpen,
  onComplete,
}) => {
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [step, setStep] = useState(1);

  if (!isOpen) return null;

  const handleNext = () => {
    if (step === 1 && companyName.trim()) {
      setStep(2);
    }
  };

  const handleComplete = () => {
    if (companyName.trim() && industry) {
      onComplete({ companyName: companyName.trim(), industry });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-2xl font-bold">Welcome to Enterprise CIA</h2>
            <div className="text-blue-100 text-sm">
              Step {step} of 2
            </div>
          </div>
          <p className="text-blue-100">
            Let's personalize your competitive intelligence experience
          </p>
        </div>

        {/* Content */}
        <div className="p-8">
          {step === 1 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">
                    What company are you from?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    We'll use this to personalize your competitor suggestions
                  </p>
                </div>
              </div>

              <div>
                <label
                  htmlFor="companyName"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Company Name
                </label>
                <input
                  id="companyName"
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleNext()}
                  placeholder="e.g., Acme Corporation"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none transition-all text-gray-900"
                  autoFocus
                />
              </div>

              <button
                onClick={handleNext}
                disabled={!companyName.trim()}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all"
              >
                Continue
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <Briefcase className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">
                    What industry are you in?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    This helps us show you relevant competitors and insights
                  </p>
                </div>
              </div>

              <div>
                <label
                  htmlFor="industry"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Industry
                </label>
                <select
                  id="industry"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-600 focus:ring-2 focus:ring-purple-100 outline-none transition-all text-gray-900"
                  autoFocus
                >
                  <option value="">Select your industry...</option>
                  {INDUSTRIES.map((ind) => (
                    <option key={ind} value={ind}>
                      {ind}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 bg-gray-100 text-gray-700 py-3 px-6 rounded-lg font-semibold hover:bg-gray-200 transition-all"
                >
                  Back
                </button>
                <button
                  onClick={handleComplete}
                  disabled={!industry}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all"
                >
                  Get Started
                </button>
              </div>
            </div>
          )}

          {/* Info Footer */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
            <p className="text-sm text-gray-700">
              <strong className="text-blue-600">💡 Why we ask:</strong> Your
              context helps us filter through thousands of companies to show
              only the competitors and insights that matter to YOU.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
