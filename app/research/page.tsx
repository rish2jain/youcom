"use client";

import { CompanyResearch } from "@/components/CompanyResearch";
import { useSearchParams } from "next/navigation";
import { useUserContext, getIndustryCompetitors } from "@/contexts/UserContext";
import { Suspense } from "react";

function ResearchContent() {
  const searchParams = useSearchParams();
  const { userContext } = useUserContext();
  const companyFromUrl = searchParams.get("company");
  const suggestedCompanies = getIndustryCompetitors(userContext.industry);

  return (
    <div className="space-y-8">
      {/* Value Proposition Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-blue-600 py-4 px-6 rounded-lg text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold mb-1">🔍 Deep Company Research</h2>
            <p className="text-indigo-50 text-sm">
              <strong>So what?</strong> Get comprehensive competitive intelligence from 400+ sources in under 2 minutes.
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">400+</div>
            <div className="text-indigo-100 text-xs">Sources per Report</div>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Company Research
        </h1>
        <p className="text-gray-600 mb-4">
          Generate comprehensive research reports using You.com ARI API with
          400+ sources in under 2 minutes.
        </p>

        {userContext.industry && !companyFromUrl && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-gray-700 mb-2">
              <strong>💡 Suggested competitors in {userContext.industry}:</strong>
            </p>
            <div className="flex flex-wrap gap-2">
              {suggestedCompanies.slice(0, 6).map((company) => (
                <button
                  key={company}
                  onClick={() => {
                    const url = new URL(window.location.href);
                    url.searchParams.set("company", company);
                    window.location.href = url.toString();
                  }}
                  className="px-3 py-1 bg-white border border-blue-300 rounded-full text-sm text-blue-700 hover:bg-blue-100 transition-colors"
                >
                  {company}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
      <CompanyResearch initialCompany={companyFromUrl || undefined} />
    </div>
  );
}

export default function ResearchPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResearchContent />
    </Suspense>
  );
}
