"use client";

import { useQuery } from "@tanstack/react-query";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { TrendingUp, Brain, Target, Clock, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";

interface MLPerformanceMetrics {
  model_version: string;
  f1_score: number;
  precision: number;
  recall: number;
  accuracy: number;
  confidence_avg: number;
  training_date: string;
  dataset_size: number;
}

interface TrainingJob {
  id: string;
  status: string;
  trigger_type: string;
  model_version: string;
  performance_improvement: number;
  started_at: string;
  completed_at: string;
  training_data_size: number;
}

interface FeedbackStats {
  total_feedback: number;
  accuracy_feedback: number;
  relevance_feedback: number;
  severity_feedback: number;
  avg_confidence: number;
  improvement_rate: number;
}

export function MLPerformanceDashboard() {
  const { data: performanceMetrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["mlPerformance"],
    queryFn: () =>
      api.get("/api/v1/ml_training/performance").then((res) => res.data),
    staleTime: 30000, // 30 seconds
  });

  const { data: trainingJobs, isLoading: jobsLoading } = useQuery({
    queryKey: ["mlTrainingJobs"],
    queryFn: () =>
      api.get("/api/v1/ml_training/jobs").then((res) => res.data.items),
    staleTime: 30000,
  });

  const { data: feedbackStats, isLoading: feedbackLoading } = useQuery({
    queryKey: ["mlFeedbackStats"],
    queryFn: () => api.get("/api/v1/ml_feedback/stats").then((res) => res.data),
    staleTime: 30000,
  });

  if (metricsLoading || jobsLoading || feedbackLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const currentMetrics = performanceMetrics?.current || {};
  const historicalMetrics = performanceMetrics?.historical || [];
  const recentJobs = trainingJobs?.slice(0, 5) || [];
  const stats = feedbackStats || {};

  // Prepare data for charts
  const performanceData = historicalMetrics.map(
    (metric: MLPerformanceMetrics) => ({
      date: new Date(metric.training_date).toLocaleDateString(),
      f1_score: Math.round(metric.f1_score * 100),
      precision: Math.round(metric.precision * 100),
      recall: Math.round(metric.recall * 100),
      accuracy: Math.round(metric.accuracy * 100),
    })
  );

  const feedbackBreakdown = [
    { name: "Accuracy", value: stats.accuracy_feedback || 0, color: "#3b82f6" },
    {
      name: "Relevance",
      value: stats.relevance_feedback || 0,
      color: "#10b981",
    },
    { name: "Severity", value: stats.severity_feedback || 0, color: "#f59e0b" },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-green-600 bg-green-100";
      case "running":
        return "text-blue-600 bg-blue-100";
      case "failed":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getTriggerIcon = (trigger: string) => {
    switch (trigger) {
      case "performance_drop":
        return <AlertTriangle className="w-4 h-4" />;
      case "feedback_threshold":
        return <Target className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Brain className="w-5 h-5 mr-2 text-blue-600" />
            ML Model Performance
          </h3>
          <div className="text-sm text-gray-600">
            Current Model: v{currentMetrics.model_version || "1.0"}
          </div>
        </div>

        {/* Current Performance Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {Math.round((currentMetrics.f1_score || 0) * 100)}%
            </div>
            <div className="text-sm text-gray-600">F1 Score</div>
            <div className="text-xs text-gray-500 mt-1">Target: ≥90%</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {Math.round((currentMetrics.precision || 0) * 100)}%
            </div>
            <div className="text-sm text-gray-600">Precision</div>
            <div className="text-xs text-gray-500 mt-1">True Positives</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {Math.round((currentMetrics.recall || 0) * 100)}%
            </div>
            <div className="text-sm text-gray-600">Recall</div>
            <div className="text-xs text-gray-500 mt-1">Coverage</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {Math.round((currentMetrics.confidence_avg || 0) * 100)}%
            </div>
            <div className="text-sm text-gray-600">Avg Confidence</div>
            <div className="text-xs text-gray-500 mt-1">Model Certainty</div>
          </div>
        </div>
      </div>

      {/* Performance Trends */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="w-4 h-4 mr-2" />
          Performance Trends
        </h4>
        {performanceData.length > 0 ? (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value) => [`${value}%`, ""]} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="f1_score"
                  stroke="#3b82f6"
                  name="F1 Score"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="precision"
                  stroke="#10b981"
                  name="Precision"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="recall"
                  stroke="#8b5cf6"
                  name="Recall"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#f59e0b"
                  name="Accuracy"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Brain className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>No historical performance data available yet.</p>
            <p className="text-sm">
              Performance metrics will appear after model training.
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Training Jobs Status */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4">
            Recent Training Jobs
          </h4>
          {recentJobs.length > 0 ? (
            <div className="space-y-3">
              {recentJobs.map((job: TrainingJob) => (
                <div
                  key={job.id}
                  className="p-3 border border-gray-200 rounded-lg"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      {getTriggerIcon(job.trigger_type)}
                      <span className="font-medium text-sm">
                        Model v{job.model_version}
                      </span>
                    </div>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${getStatusColor(
                        job.status
                      )}`}
                    >
                      {job.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="text-xs text-gray-600 space-y-1">
                    <div>Trigger: {job.trigger_type.replace("_", " ")}</div>
                    <div>Training data: {job.training_data_size} samples</div>
                    {job.performance_improvement && (
                      <div className="text-green-600">
                        Improvement: +
                        {(job.performance_improvement * 100).toFixed(1)}%
                      </div>
                    )}
                    <div>
                      {job.completed_at
                        ? `Completed: ${new Date(
                            job.completed_at
                          ).toLocaleString()}`
                        : `Started: ${new Date(
                            job.started_at
                          ).toLocaleString()}`}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Clock className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">No training jobs yet.</p>
            </div>
          )}
        </div>

        {/* Feedback Statistics */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4">User Feedback</h4>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-xl font-bold text-blue-600">
                  {stats.total_feedback || 0}
                </div>
                <div className="text-sm text-gray-600">Total Feedback</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-xl font-bold text-green-600">
                  {Math.round((stats.avg_confidence || 0) * 100)}%
                </div>
                <div className="text-sm text-gray-600">Avg Confidence</div>
              </div>
            </div>

            {feedbackBreakdown.some((item) => item.value > 0) ? (
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={feedbackBreakdown}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      dataKey="value"
                    >
                      {feedbackBreakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Target className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No feedback collected yet.</p>
              </div>
            )}

            {stats.improvement_rate && (
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="text-sm text-green-700">
                  <strong>Model Improvement Rate:</strong> +
                  {(stats.improvement_rate * 100).toFixed(1)}% from feedback
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
