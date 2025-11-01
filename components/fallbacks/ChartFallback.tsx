/**
 * Chart Fallback Components
 * Provides graceful degradation for chart components
 */

import React from "react";

export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    color?: string;
  }>;
}

export interface ChartFallbackProps {
  data: ChartData;
  title?: string;
  type?: "line" | "bar" | "pie" | "area";
  className?: string;
}

/**
 * Text-based chart fallback for minimal devices
 */
export function TextChartFallback({
  data,
  title,
  type = "bar",
  className = "",
}: ChartFallbackProps) {
  const renderTextChart = () => {
    if (!data.datasets.length) return null;

    const primaryDataset = data.datasets[0];
    if (
      !primaryDataset ||
      !primaryDataset.data ||
      primaryDataset.data.length === 0
    ) {
      return null;
    }
    const maxValue = Math.max(...primaryDataset.data);

    return (
      <div className="text-chart-fallback">
        {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}

        <div className="space-y-2">
          {data.labels.map((label, index) => {
            const value = primaryDataset.data[index];
            const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;

            return (
              <div key={label} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 w-1/3">
                  {label}
                </span>
                <div className="flex-1 mx-3">
                  <div className="bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
                <span className="text-sm text-gray-600 w-16 text-right">
                  {typeof value === "number" ? value.toLocaleString() : value}
                </span>
              </div>
            );
          })}
        </div>

        {data.datasets.length > 1 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-2">
              Additional Data:
            </h4>
            {data.datasets.slice(1).map((dataset, datasetIndex) => (
              <div key={datasetIndex} className="mb-3">
                <span className="text-sm font-medium text-gray-600">
                  {dataset.label}:
                </span>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  {dataset.data.map((value, index) => (
                    <div key={index} className="text-xs text-gray-500">
                      {data.labels[index]}:{" "}
                      {typeof value === "number"
                        ? value.toLocaleString()
                        : value}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`chart-fallback text-fallback ${className}`}>
      {renderTextChart()}
    </div>
  );
}

/**
 * Simple visual chart fallback for standard devices
 */
export function SimpleChartFallback({
  data,
  title,
  type = "bar",
  className = "",
}: ChartFallbackProps) {
  const renderSimpleChart = () => {
    if (!data.datasets.length) return null;

    const primaryDataset = data.datasets[0];
    if (
      !primaryDataset ||
      !primaryDataset.data ||
      primaryDataset.data.length === 0
    ) {
      return null;
    }
    const maxValue = Math.max(...primaryDataset.data);

    if (type === "pie") {
      return renderSimplePieChart(primaryDataset, data.labels);
    }

    return (
      <div className="simple-chart">
        {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}

        <div className="chart-container bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-end justify-between h-32 space-x-1">
            {data.labels.map((label, index) => {
              const value = primaryDataset.data[index];
              const height = maxValue > 0 ? (value / maxValue) * 100 : 0;

              return (
                <div key={label} className="flex flex-col items-center flex-1">
                  <div
                    className="bg-blue-500 rounded-t transition-all duration-500 w-full min-h-[4px]"
                    style={{ height: `${height}%` }}
                    title={`${label}: ${value}`}
                  />
                  <span className="text-xs text-gray-600 mt-2 text-center truncate w-full">
                    {label}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-4 text-center">
            <span className="text-sm text-gray-500">
              {primaryDataset.label || "Data"}
            </span>
          </div>
        </div>

        {/* Legend for multiple datasets */}
        {data.datasets.length > 1 && (
          <div className="mt-4 flex flex-wrap gap-4 justify-center">
            {data.datasets.map((dataset, index) => (
              <div key={index} className="flex items-center">
                <div
                  className="w-3 h-3 rounded mr-2"
                  style={{
                    backgroundColor:
                      dataset.color || `hsl(${index * 60}, 70%, 50%)`,
                  }}
                />
                <span className="text-sm text-gray-600">{dataset.label}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderSimplePieChart = (
    dataset: ChartData["datasets"][0],
    labels: string[]
  ) => {
    const total = dataset.data.reduce((sum, value) => sum + value, 0);

    return (
      <div className="simple-pie-chart">
        {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}

        <div className="flex flex-col md:flex-row items-center gap-6">
          {/* Simple pie representation using CSS */}
          <div className="relative w-32 h-32">
            <div className="w-full h-full rounded-full bg-gray-200 overflow-hidden">
              {dataset.data.map((value, index) => {
                const percentage = total > 0 ? (value / total) * 100 : 0;
                const color = `hsl(${index * 60}, 70%, 50%)`;

                return (
                  <div
                    key={index}
                    className="absolute inset-0 rounded-full"
                    style={{
                      background: `conic-gradient(${color} 0% ${percentage}%, transparent ${percentage}% 100%)`,
                      transform: `rotate(${
                        index * (360 / dataset.data.length)
                      }deg)`,
                    }}
                  />
                );
              })}
            </div>
          </div>

          {/* Legend */}
          <div className="space-y-2">
            {labels.map((label, index) => {
              const value = dataset.data[index];
              const percentage =
                total > 0 ? ((value / total) * 100).toFixed(1) : "0";
              const color = `hsl(${index * 60}, 70%, 50%)`;

              return (
                <div key={label} className="flex items-center">
                  <div
                    className="w-3 h-3 rounded mr-3"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-sm text-gray-700">
                    {label}: {value} ({percentage}%)
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`chart-fallback simple-fallback ${className}`}>
      {renderSimpleChart()}
    </div>
  );
}

/**
 * Static chart fallback (no animations)
 */
export function StaticChartFallback({
  data,
  title,
  type = "bar",
  className = "",
}: ChartFallbackProps) {
  return (
    <div className={`chart-fallback static-fallback ${className}`}>
      <SimpleChartFallback
        data={data}
        title={title}
        type={type}
        className="no-animations"
      />
      <style jsx>{`
        .no-animations * {
          transition: none !important;
          animation: none !important;
        }
      `}</style>
    </div>
  );
}

/**
 * Chart fallback selector based on degradation level
 */
export function AdaptiveChartFallback({
  data,
  title,
  type = "bar",
  className = "",
  fallbackType = "simple",
}: ChartFallbackProps & { fallbackType?: "text" | "simple" | "static" }) {
  switch (fallbackType) {
    case "text":
      return (
        <TextChartFallback
          data={data}
          title={title}
          type={type}
          className={className}
        />
      );
    case "static":
      return (
        <StaticChartFallback
          data={data}
          title={title}
          type={type}
          className={className}
        />
      );
    case "simple":
    default:
      return (
        <SimpleChartFallback
          data={data}
          title={title}
          type={type}
          className={className}
        />
      );
  }
}
