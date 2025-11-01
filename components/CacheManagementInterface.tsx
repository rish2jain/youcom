"use client";

import React, { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cachedApi, warmAPICache, getCriticalEndpoints } from "@/lib/api-cache";
import { useServiceWorkerContext } from "./ServiceWorkerProvider";

interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  hitRate: number;
}

interface CacheManagementInterfaceProps {
  className?: string;
}

export const CacheManagementInterface: React.FC<
  CacheManagementInterfaceProps
> = ({ className = "" }) => {
  const [apiCacheStats, setApiCacheStats] = useState<CacheStats>({
    hits: 0,
    misses: 0,
    size: 0,
    hitRate: 0,
  });
  const [isWarming, setIsWarming] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const { cacheStatus, clearCache, refreshCacheStatus } =
    useServiceWorkerContext();

  // Refresh stats periodically
  useEffect(() => {
    const refreshStats = () => {
      const stats = cachedApi.getCacheStats();
      setApiCacheStats(stats);
      setLastUpdated(new Date());
    };

    refreshStats();
    const interval = setInterval(refreshStats, 10000); // Every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const handleClearAPICache = async () => {
    try {
      cachedApi.clearCache();
      setApiCacheStats({ hits: 0, misses: 0, size: 0, hitRate: 0 });
    } catch (error) {
      console.error("Failed to clear API cache:", error);
    }
  };

  const handleClearServiceWorkerCache = async () => {
    try {
      await clearCache();
      await refreshCacheStatus();
    } catch (error) {
      console.error("Failed to clear service worker cache:", error);
    }
  };

  const handleWarmCache = async () => {
    setIsWarming(true);
    try {
      const endpoints = getCriticalEndpoints();
      await warmAPICache(endpoints);

      // Refresh stats immediately after warming
      const stats = cachedApi.getCacheStats();
      setApiCacheStats(stats);
    } catch (error) {
      console.error("Failed to warm cache:", error);
    } finally {
      setIsWarming(false);
    }
  };

  const handleInvalidateByTag = async (tag: string) => {
    try {
      const invalidated = cachedApi.invalidateCache([tag]);
      console.log(`Invalidated ${invalidated} entries with tag: ${tag}`);

      // Refresh stats
      const stats = cachedApi.getCacheStats();
      setApiCacheStats(stats);
    } catch (error) {
      console.error("Failed to invalidate cache:", error);
    }
  };

  const formatHitRate = (rate: number): string => {
    return `${(rate * 100).toFixed(1)}%`;
  };

  const getHitRateColor = (rate: number): string => {
    if (rate >= 0.8) return "bg-green-100 text-green-800";
    if (rate >= 0.6) return "bg-yellow-100 text-yellow-800";
    return "bg-red-100 text-red-800";
  };

  const getTotalServiceWorkerEntries = (): number => {
    return Object.values(cacheStatus).reduce(
      (total: number, cache: any) => total + (cache.entryCount || 0),
      0
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* API Cache Stats */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">API Response Cache</h3>
          <Badge className={getHitRateColor(apiCacheStats.hitRate)}>
            Hit Rate: {formatHitRate(apiCacheStats.hitRate)}
          </Badge>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {apiCacheStats.hits}
            </div>
            <div className="text-sm text-gray-600">Cache Hits</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {apiCacheStats.misses}
            </div>
            <div className="text-sm text-gray-600">Cache Misses</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {apiCacheStats.size}
            </div>
            <div className="text-sm text-gray-600">Cached Entries</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {apiCacheStats.hits + apiCacheStats.misses}
            </div>
            <div className="text-sm text-gray-600">Total Requests</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          <Button
            onClick={handleWarmCache}
            disabled={isWarming}
            variant="outline"
            size="sm"
          >
            {isWarming ? "Warming..." : "Warm Cache"}
          </Button>
          <Button onClick={handleClearAPICache} variant="outline" size="sm">
            Clear API Cache
          </Button>
        </div>

        <div className="flex flex-wrap gap-2">
          {["watchlist", "news", "research", "analytics", "impact"].map(
            (tag) => (
              <Button
                key={tag}
                onClick={() => handleInvalidateByTag(tag)}
                variant="ghost"
                size="sm"
                className="text-xs"
              >
                Clear {tag}
              </Button>
            )
          )}
        </div>
      </Card>

      {/* Service Worker Cache Stats */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Service Worker Cache</h3>
          <Badge variant="outline">
            {getTotalServiceWorkerEntries()} Total Entries
          </Badge>
        </div>

        <div className="space-y-3 mb-4">
          {Object.entries(cacheStatus).map(([cacheName, cache]) => (
            <div
              key={cacheName}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div>
                <div className="font-medium">{cacheName}</div>
                <div className="text-sm text-gray-600">
                  {(cache as any).entryCount || 0} entries
                </div>
              </div>
              <Button
                onClick={() => clearCache(cacheName)}
                variant="ghost"
                size="sm"
              >
                Clear
              </Button>
            </div>
          ))}
        </div>

        <Button
          onClick={handleClearServiceWorkerCache}
          variant="outline"
          size="sm"
        >
          Clear All Service Worker Cache
        </Button>
      </Card>

      {/* Cache Performance Insights */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Performance Insights</h3>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
            <div>
              <div className="font-medium">Cache Efficiency</div>
              <div className="text-sm text-gray-600">
                {apiCacheStats.hitRate >= 0.8
                  ? "Excellent"
                  : apiCacheStats.hitRate >= 0.6
                  ? "Good"
                  : "Needs Improvement"}
              </div>
            </div>
            <div className="text-right">
              <div className="font-bold">
                {formatHitRate(apiCacheStats.hitRate)}
              </div>
              <div className="text-sm text-gray-600">Hit Rate</div>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
            <div>
              <div className="font-medium">Memory Usage</div>
              <div className="text-sm text-gray-600">Estimated cache size</div>
            </div>
            <div className="text-right">
              <div className="font-bold">
                {Math.round(
                  (apiCacheStats.size * 2 +
                    getTotalServiceWorkerEntries() * 5) /
                    1024
                )}
                KB
              </div>
              <div className="text-sm text-gray-600">Approx Size</div>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
            <div>
              <div className="font-medium">Last Updated</div>
              <div className="text-sm text-gray-600">
                Cache statistics refresh
              </div>
            </div>
            <div className="text-right">
              <div className="font-bold">
                {lastUpdated.toLocaleTimeString()}
              </div>
              <div className="text-sm text-gray-600">
                {Math.round((Date.now() - lastUpdated.getTime()) / 1000)}s ago
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Cache Strategy Information */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Cache Strategy</h3>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span>News Data:</span>
            <span className="text-gray-600">2 minutes TTL</span>
          </div>
          <div className="flex justify-between">
            <span>Watchlist:</span>
            <span className="text-gray-600">5 minutes TTL</span>
          </div>
          <div className="flex justify-between">
            <span>Impact Cards:</span>
            <span className="text-gray-600">10 minutes TTL</span>
          </div>
          <div className="flex justify-between">
            <span>Company Research:</span>
            <span className="text-gray-600">15 minutes TTL</span>
          </div>
          <div className="flex justify-between">
            <span>Analytics:</span>
            <span className="text-gray-600">30 minutes TTL</span>
          </div>
          <div className="flex justify-between">
            <span>Static Assets:</span>
            <span className="text-gray-600">1 year TTL</span>
          </div>
        </div>
      </Card>
    </div>
  );
};
