"use client";

import { Check, X, TrendingUp, Clock, DollarSign, Zap } from "lucide-react";

export function ComparisonTable() {
  const comparisons = [
    {
      metric: "Research Time",
      icon: Clock,
      manual: "2-4 hours",
      automated: "<2 minutes",
      improvement: "120x faster",
      color: "blue"
    },
    {
      metric: "Sources Analyzed",
      icon: TrendingUp,
      manual: "10-20",
      automated: "400+",
      improvement: "20x more",
      color: "green"
    },
    {
      metric: "Cost per Report",
      icon: DollarSign,
      manual: "$500",
      automated: "$5",
      improvement: "100x cheaper",
      color: "purple"
    },
    {
      metric: "Update Frequency",
      icon: Zap,
      manual: "Weekly",
      automated: "Real-time",
      improvement: "Continuous",
      color: "orange"
    },
  ];

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Manual vs. Automated Intelligence
        </h2>
        <p className="text-gray-600">
          See how Enterprise CIA transforms competitive research
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b-2 border-gray-200">
              <th className="text-left py-4 px-6 text-gray-600 font-semibold">Metric</th>
              <th className="text-center py-4 px-6">
                <div className="flex flex-col items-center">
                  <X className="w-6 h-6 text-red-500 mb-1" />
                  <span className="text-gray-900 font-semibold">Manual Process</span>
                  <span className="text-xs text-gray-500">Traditional approach</span>
                </div>
              </th>
              <th className="text-center py-4 px-6">
                <div className="flex flex-col items-center">
                  <Check className="w-6 h-6 text-green-500 mb-1" />
                  <span className="text-gray-900 font-semibold">Enterprise CIA</span>
                  <span className="text-xs text-gray-500">Powered by You.com APIs</span>
                </div>
              </th>
              <th className="text-center py-4 px-6 text-gray-600 font-semibold">Improvement</th>
            </tr>
          </thead>
          <tbody>
            {comparisons.map((item, index) => {
              const Icon = item.icon;
              return (
                <tr
                  key={index}
                  className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  <td className="py-6 px-6">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg bg-${item.color}-100`}>
                        <Icon className={`w-5 h-5 text-${item.color}-600`} />
                      </div>
                      <span className="font-medium text-gray-900">{item.metric}</span>
                    </div>
                  </td>
                  <td className="py-6 px-6 text-center">
                    <span className="text-red-600 font-semibold">{item.manual}</span>
                  </td>
                  <td className="py-6 px-6 text-center">
                    <span className="text-green-600 font-semibold">{item.automated}</span>
                  </td>
                  <td className="py-6 px-6 text-center">
                    <div className={`inline-block px-4 py-2 bg-${item.color}-100 rounded-full`}>
                      <span className={`text-${item.color}-700 font-bold`}>
                        {item.improvement}
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              ROI Calculator
            </h3>
            <p className="text-gray-600 text-sm">
              For a company monitoring 20 competitors monthly
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-green-600">$119,000</div>
            <div className="text-sm text-gray-600">Annual savings</div>
          </div>
        </div>
      </div>
    </div>
  );
}
