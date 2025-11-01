"use client";

import React from "react";

interface LoadingSkeletonProps {
  variant?:
    | "card"
    | "dashboard"
    | "widget"
    | "list"
    | "impact-card"
    | "chart"
    | "table";
  count?: number;
  className?: string;
  animated?: boolean;
}

export function LoadingSkeleton({
  variant = "card",
  count = 1,
  className = "",
  animated = true,
}: LoadingSkeletonProps) {
  const baseClasses = animated ? "animate-pulse" : "";

  const renderCardSkeleton = () => (
    <div
      className={`${baseClasses} bg-white p-6 rounded-lg shadow-sm border border-gray-200 ${className}`}
      data-testid="loading-skeleton"
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="h-5 bg-gray-200 rounded w-1/3 mb-2"></div>
          <div className="flex space-x-2 mb-2">
            <div className="h-4 bg-gray-200 rounded w-16"></div>
            <div className="h-4 bg-gray-200 rounded w-20"></div>
          </div>
        </div>
        <div className="h-8 w-8 bg-gray-200 rounded"></div>
      </div>
      <div className="h-4 bg-gray-200 rounded mb-2 w-3/4"></div>
      <div className="h-4 bg-gray-200 rounded mb-4 w-1/2"></div>
      <div className="flex justify-between items-center">
        <div className="h-3 bg-gray-200 rounded w-24"></div>
        <div className="h-3 bg-gray-200 rounded w-16"></div>
      </div>
    </div>
  );

  const renderImpactCardSkeleton = () => (
    <div
      className={`${baseClasses} bg-white p-6 rounded-lg shadow-sm border border-gray-200 ${className}`}
      data-testid="impact-card-skeleton"
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div className="flex-1">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-3"></div>
          <div className="flex space-x-3 mb-2">
            <div className="h-5 bg-red-100 rounded-full w-20"></div>
            <div className="h-5 bg-gray-200 rounded w-16"></div>
          </div>
        </div>
        <div className="text-center">
          <div className="h-12 w-12 bg-gray-200 rounded-full mb-2 mx-auto"></div>
          <div className="h-3 bg-gray-200 rounded w-12"></div>
        </div>
      </div>

      {/* Risk Score Gauge */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="text-center">
          <div className="h-32 w-32 bg-gray-200 rounded-full mx-auto mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-20 mx-auto"></div>
        </div>
        <div className="text-center">
          <div className="h-8 bg-gray-200 rounded w-16 mx-auto mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-24 mx-auto mb-1"></div>
          <div className="h-3 bg-gray-200 rounded w-20 mx-auto"></div>
        </div>
        <div className="text-center">
          <div className="h-8 bg-gray-200 rounded w-12 mx-auto mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-20 mx-auto mb-1"></div>
          <div className="h-3 bg-gray-200 rounded w-32 mx-auto"></div>
        </div>
      </div>

      {/* Impact Areas */}
      <div className="space-y-3 mb-6">
        <div className="h-5 bg-gray-200 rounded w-32 mb-3"></div>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="p-3 bg-gray-50 rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <div className="h-4 bg-gray-200 rounded w-24"></div>
              <div className="h-4 bg-gray-200 rounded w-12"></div>
            </div>
            <div className="h-2 bg-gray-200 rounded mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-full"></div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="space-y-3">
        <div className="h-5 bg-gray-200 rounded w-24 mb-3"></div>
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="p-4 border border-gray-200 rounded-lg">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>
            <div className="flex space-x-2">
              <div className="h-6 bg-gray-200 rounded w-16"></div>
              <div className="h-6 bg-gray-200 rounded w-20"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderDashboardSkeleton = () => (
    <div className={`${baseClasses} space-y-6 ${className}`}>
      <div className="h-6 bg-gray-200 rounded w-1/4"></div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="bg-white p-4 rounded-lg border border-gray-200"
          >
            <div className="h-4 bg-gray-200 rounded mb-3 w-2/3"></div>
            <div className="h-20 bg-gray-200 rounded mb-3"></div>
            <div className="flex space-x-2">
              <div className="h-6 bg-gray-200 rounded w-16"></div>
              <div className="h-6 bg-gray-200 rounded w-20"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderWidgetSkeleton = () => (
    <div
      className={`${baseClasses} bg-white p-4 rounded-lg border border-gray-200 ${className}`}
    >
      <div className="h-5 bg-gray-200 rounded w-1/2 mb-4"></div>
      <div className="space-y-3">
        <div className="h-4 bg-gray-200 rounded w-full"></div>
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    </div>
  );

  const renderChartSkeleton = () => (
    <div
      className={`${baseClasses} bg-white p-4 rounded-lg border border-gray-200 ${className}`}
    >
      <div className="h-5 bg-gray-200 rounded w-1/3 mb-4"></div>
      <div className="h-64 bg-gray-100 rounded-lg flex items-end justify-around p-4">
        {Array.from({ length: 8 }).map((_, i) => {
          // Deterministic height calculation based on index
          const height = 20 + ((i * 37) % 80);
          return (
            <div
              key={i}
              className="bg-gray-200 rounded-t"
              style={{
                height: `${height}%`,
                width: "8%",
              }}
            ></div>
          );
        })}
      </div>
      <div className="flex justify-between mt-3">
        <div className="h-3 bg-gray-200 rounded w-16"></div>
        <div className="h-3 bg-gray-200 rounded w-20"></div>
      </div>
    </div>
  );

  const renderTableSkeleton = () => (
    <div
      className={`${baseClasses} bg-white rounded-lg border border-gray-200 overflow-hidden ${className}`}
    >
      {/* Table Header */}
      <div className="bg-gray-50 p-4 border-b border-gray-200">
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-4 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>

      {/* Table Rows */}
      <div className="divide-y divide-gray-200">
        {Array.from({ length: count || 5 }).map((_, i) => (
          <div key={i} className="p-4">
            <div className="grid grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, j) => (
                <div key={j} className="h-4 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderListSkeleton = () => (
    <div className={`${baseClasses} space-y-3 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200"
        >
          <div className="h-10 w-10 bg-gray-200 rounded-full"></div>
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
          <div className="h-6 w-16 bg-gray-200 rounded"></div>
        </div>
      ))}
    </div>
  );

  switch (variant) {
    case "impact-card":
      return renderImpactCardSkeleton();
    case "dashboard":
      return renderDashboardSkeleton();
    case "widget":
      return renderWidgetSkeleton();
    case "chart":
      return renderChartSkeleton();
    case "table":
      return renderTableSkeleton();
    case "list":
      return renderListSkeleton();
    case "card":
    default:
      return count > 1 ? (
        <div className="space-y-4">
          {Array.from({ length: count }).map((_, i) => (
            <div key={i}>{renderCardSkeleton()}</div>
          ))}
        </div>
      ) : (
        renderCardSkeleton()
      );
  }
}
