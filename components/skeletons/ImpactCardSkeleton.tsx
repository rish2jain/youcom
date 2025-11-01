"use client";

import React from "react";

interface ImpactCardSkeletonProps {
  className?: string;
  animated?: boolean;
  showDetails?: boolean;
}

/**
 * Specialized skeleton for ImpactCard components
 * Matches the exact layout and dimensions of the actual component
 */
export function ImpactCardSkeleton({
  className = "",
  animated = true,
  showDetails = true,
}: ImpactCardSkeletonProps) {
  const baseClasses = animated ? "animate-pulse" : "";

  return (
    <div
      className={`${baseClasses} bg-white p-6 rounded-lg shadow-sm border border-gray-200 ${className}`}
      data-testid="impact-card-skeleton"
    >
      {/* Header Section */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex-1">
          <div className="h-6 bg-gray-200 rounded w-48 mb-3"></div>
          <div className="flex items-center space-x-2">
            <div className="h-6 bg-red-100 rounded-full w-24 px-2 py-1"></div>
            <div className="h-4 bg-gray-200 rounded w-20"></div>
          </div>
        </div>
        <button className="text-gray-500 hover:text-gray-700">
          <div className="h-6 w-6 bg-gray-200 rounded"></div>
        </button>
      </div>

      {/* Risk Score Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Risk Gauge */}
        <div className="text-center">
          <div className="relative w-32 h-32 mx-auto mb-2">
            <div className="w-full h-full bg-gray-200 rounded-full"></div>
          </div>
          <div className="h-6 bg-gray-200 rounded w-20 mx-auto"></div>
        </div>

        {/* Confidence Score */}
        <div className="text-center">
          <div className="h-8 bg-gray-200 rounded w-16 mx-auto mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-24 mx-auto mb-1"></div>
          <div className="h-3 bg-gray-200 rounded w-20 mx-auto"></div>
        </div>

        {/* Total Sources */}
        <div className="text-center">
          <div className="h-8 bg-gray-200 rounded w-12 mx-auto mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-20 mx-auto mb-1"></div>
          <div className="h-3 bg-gray-200 rounded w-32 mx-auto"></div>
        </div>
      </div>

      {showDetails && (
        <>
          {/* Source Quality Section */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border border-gray-200 rounded-lg">
              <div className="h-5 bg-gray-200 rounded w-32 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
              <div className="space-y-1">
                <div className="h-3 bg-gray-200 rounded w-28"></div>
                <div className="h-3 bg-gray-200 rounded w-28"></div>
                <div className="h-3 bg-gray-200 rounded w-28"></div>
              </div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg">
              <div className="h-5 bg-gray-200 rounded w-24 mb-2"></div>
              <div className="space-y-1">
                <div className="h-3 bg-blue-200 rounded w-full"></div>
                <div className="h-3 bg-blue-200 rounded w-3/4"></div>
                <div className="h-3 bg-blue-200 rounded w-1/2"></div>
              </div>
            </div>
          </div>

          {/* Impact Areas */}
          <div className="mb-6">
            <div className="h-5 bg-gray-200 rounded w-24 mb-3"></div>
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <div className="h-4 bg-gray-200 rounded w-20"></div>
                    <div className="h-4 bg-gray-200 rounded w-12"></div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-full"></div>
                </div>
              ))}
            </div>
          </div>

          {/* Next Steps */}
          <div className="mb-6">
            <div className="h-5 bg-gray-200 rounded w-20 mb-3"></div>
            <div className="space-y-3">
              {Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                    <div className="text-right text-sm">
                      <div className="h-3 bg-gray-200 rounded w-16 mb-1"></div>
                      <div className="h-3 bg-gray-200 rounded w-16 mb-1"></div>
                      <div className="h-3 bg-blue-200 rounded w-20"></div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 mt-2">
                    <div className="h-6 bg-green-200 rounded w-16"></div>
                    <div className="h-6 bg-red-200 rounded w-20"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Key Insights */}
          <div className="mb-6">
            <div className="h-5 bg-gray-200 rounded w-24 mb-3"></div>
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex items-start space-x-2">
                  <div className="w-4 h-4 bg-blue-200 rounded mt-0.5"></div>
                  <div className="h-4 bg-gray-200 rounded flex-1"></div>
                </div>
              ))}
            </div>
          </div>

          {/* API Usage */}
          <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
            <div className="flex items-center mb-3">
              <div className="w-4 h-4 bg-gray-200 rounded mr-2"></div>
              <div className="h-5 bg-gray-200 rounded w-32"></div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i}>
                  <div className="h-6 bg-gray-200 rounded w-8 mx-auto mb-1"></div>
                  <div className="h-3 bg-gray-200 rounded w-16 mx-auto"></div>
                </div>
              ))}
            </div>
            <div className="text-center mt-3">
              <div className="h-4 bg-gray-200 rounded w-32 mx-auto"></div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Compact version for card lists
 */
export function ImpactCardSkeletonCompact({
  className = "",
  animated = true,
}: {
  className?: string;
  animated?: boolean;
}) {
  const baseClasses = animated ? "animate-pulse" : "";

  return (
    <div
      className={`${baseClasses} p-4 border rounded-lg cursor-pointer hover:shadow-md transition-shadow bg-white ${className}`}
      data-testid="impact-card-skeleton-compact"
    >
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
          <div className="flex items-center space-x-2">
            <div className="h-4 bg-red-100 rounded-full w-20"></div>
            <div className="h-3 bg-gray-200 rounded w-16"></div>
          </div>
        </div>
        <div className="text-right">
          <div className="h-6 bg-gray-200 rounded w-8 mb-1 ml-auto"></div>
          <div className="h-3 bg-gray-200 rounded w-12"></div>
        </div>
      </div>

      <div className="h-3 bg-gray-200 rounded w-3/4 mb-2"></div>

      <div className="inline-flex items-center space-x-2 rounded-full bg-red-50 px-3 py-1">
        <div className="w-3 h-3 bg-red-200 rounded"></div>
        <div className="h-3 bg-red-200 rounded w-24"></div>
      </div>
    </div>
  );
}
