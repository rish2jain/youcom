"use client";

import React from "react";
import { ImpactCardSkeletonCompact } from "./ImpactCardSkeleton";

interface DashboardSkeletonProps {
  className?: string;
  animated?: boolean;
  cardCount?: number;
}

/**
 * Specialized skeleton for dashboard layout
 * Includes header, filters, and card grid
 */
export function DashboardSkeleton({
  className = "",
  animated = true,
  cardCount = 6,
}: DashboardSkeletonProps) {
  const baseClasses = animated ? "animate-pulse" : "";

  return (
    <div
      className={`${baseClasses} space-y-6 ${className}`}
      data-testid="dashboard-skeleton"
    >
      {/* Header Section */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex justify-between items-center mb-6">
          <div className="h-6 bg-gray-200 rounded w-32"></div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-24"></div>
          </div>
        </div>

        {/* Generate Form */}
        <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg mb-6">
          <div className="h-5 bg-gray-200 rounded w-40 mb-3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
            <div className="h-10 bg-white rounded-md border border-gray-300"></div>
            <div className="h-10 bg-white rounded-md border border-gray-300"></div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-10 bg-blue-200 rounded-md w-48"></div>
          </div>
        </div>

        {/* Filter Section */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
          <div>
            <div className="h-4 bg-gray-200 rounded w-40 mb-1"></div>
            <div className="h-3 bg-gray-200 rounded w-56"></div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="h-6 bg-gray-200 rounded-full w-32"></div>
            <div className="h-4 bg-gray-200 rounded w-8"></div>
            <div className="h-3 bg-blue-200 rounded w-12"></div>
          </div>
        </div>
      </div>

      {/* Progressive Disclosure Section */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="h-5 bg-gray-200 rounded w-48 mb-1"></div>
            <div className="h-3 bg-gray-200 rounded w-64"></div>
          </div>
          <div className="h-6 bg-gray-200 rounded w-16"></div>
        </div>

        {/* Critical Alerts Section */}
        <div className="border border-gray-200 rounded-lg mb-4">
          <div className="p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-40"></div>
              </div>
              <div className="h-5 bg-red-100 rounded-full w-16"></div>
            </div>
          </div>
          <div className="p-4 space-y-4">
            {Array.from({ length: 2 }).map((_, i) => (
              <ImpactCardSkeletonCompact key={i} animated={animated} />
            ))}
          </div>
        </div>

        {/* Supporting Details Section */}
        <div className="border border-gray-200 rounded-lg mb-4">
          <div className="p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-48"></div>
              </div>
              <div className="h-5 bg-blue-100 rounded-full w-20"></div>
            </div>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="p-4 bg-gray-50 rounded-lg">
                  <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <div className="h-3 bg-gray-200 rounded w-16"></div>
                      <div className="h-3 bg-blue-200 rounded w-8"></div>
                    </div>
                    <div className="flex justify-between">
                      <div className="h-3 bg-gray-200 rounded w-20"></div>
                      <div className="h-3 bg-green-200 rounded w-8"></div>
                    </div>
                    <div className="flex justify-between">
                      <div className="h-3 bg-gray-200 rounded w-12"></div>
                      <div className="h-3 bg-purple-200 rounded w-6"></div>
                    </div>
                  </div>
                  <div className="flex items-center mt-2">
                    <div className="w-3 h-3 bg-gray-200 rounded mr-1"></div>
                    <div className="h-3 bg-gray-200 rounded w-32"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Technical Details Section */}
        <div className="border border-gray-200 rounded-lg">
          <div className="p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-56"></div>
              </div>
              <div className="h-5 bg-purple-100 rounded-full w-20"></div>
            </div>
          </div>
          <div className="p-4 space-y-4">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="p-4 border border-gray-200 rounded-lg">
                <div className="h-4 bg-gray-200 rounded w-48 mb-3"></div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Array.from({ length: 4 }).map((_, j) => (
                    <div key={j} className="text-center p-2 bg-blue-50 rounded">
                      <div className="h-6 bg-blue-200 rounded w-8 mx-auto mb-1"></div>
                      <div className="h-3 bg-gray-200 rounded w-12 mx-auto"></div>
                    </div>
                  ))}
                </div>
                <div className="h-3 bg-gray-200 rounded w-40 mt-2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Notifications Section */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="p-3 border border-gray-200 rounded-lg">
              <div className="flex justify-between mb-1">
                <div className="h-4 bg-gray-200 rounded w-24"></div>
                <div className="h-3 bg-gray-200 rounded w-20"></div>
              </div>
              <div className="h-3 bg-gray-200 rounded w-16 mb-1"></div>
              <div className="h-3 bg-gray-200 rounded w-full"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Simplified dashboard skeleton for faster loading
 */
export function DashboardSkeletonSimple({
  className = "",
  animated = true,
  cardCount = 6,
}: DashboardSkeletonProps) {
  const baseClasses = animated ? "animate-pulse" : "";

  return (
    <div
      className={`${baseClasses} space-y-6 ${className}`}
      data-testid="dashboard-skeleton-simple"
    >
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
        <div className="h-10 bg-gray-100 rounded-lg"></div>
      </div>

      {/* Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: cardCount }).map((_, i) => (
          <ImpactCardSkeletonCompact key={i} animated={animated} />
        ))}
      </div>
    </div>
  );
}
