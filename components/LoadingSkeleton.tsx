"use client";

export function ImpactCardSkeleton() {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
          <div>
            <div className="h-5 w-32 bg-gray-200 rounded mb-2"></div>
            <div className="h-3 w-24 bg-gray-200 rounded"></div>
          </div>
        </div>
        <div className="w-20 h-8 bg-gray-200 rounded-full"></div>
      </div>

      <div className="space-y-3">
        <div className="h-4 bg-gray-200 rounded w-full"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        <div className="h-4 bg-gray-200 rounded w-4/6"></div>
      </div>

      <div className="mt-4 flex space-x-2">
        <div className="h-8 w-24 bg-gray-200 rounded"></div>
        <div className="h-8 w-24 bg-gray-200 rounded"></div>
        <div className="h-8 w-24 bg-gray-200 rounded"></div>
      </div>
    </div>
  );
}

export function WatchListSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white p-4 rounded-lg shadow-sm animate-pulse">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="h-5 w-40 bg-gray-200 rounded mb-2"></div>
              <div className="h-3 w-64 bg-gray-200 rounded"></div>
            </div>
            <div className="flex space-x-2">
              <div className="w-10 h-10 bg-gray-200 rounded"></div>
              <div className="w-10 h-10 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function MetricCardSkeleton() {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm animate-pulse">
      <div className="h-8 w-20 bg-gray-200 rounded mb-2"></div>
      <div className="h-4 w-32 bg-gray-200 rounded mb-1"></div>
      <div className="h-3 w-40 bg-gray-200 rounded"></div>
    </div>
  );
}
