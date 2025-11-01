/**
 * Notification System Component
 * Displays performance alerts and notifications in the UI
 */

"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  Bell,
  BellOff,
  Check,
  CheckCircle,
  Clock,
  Settings,
  X,
  Zap,
} from "lucide-react";
import { usePerformanceAlerting } from "@/lib/performance-alerting";
import type { Alert } from "@/lib/performance-alerting";

interface NotificationItemProps {
  alert: Alert;
  onAcknowledge: (alertId: string) => void;
  onResolve: (alertId: string) => void;
  onDismiss: (alertId: string) => void;
}

const NotificationItem: React.FC<NotificationItemProps> = ({
  alert,
  onAcknowledge,
  onResolve,
  onDismiss,
}) => {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case "high":
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case "medium":
        return <Zap className="w-4 h-4 text-yellow-500" />;
      case "low":
        return <Bell className="w-4 h-4 text-blue-500" />;
      default:
        return <Bell className="w-4 h-4 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "border-red-500 bg-red-50";
      case "high":
        return "border-orange-500 bg-orange-50";
      case "medium":
        return "border-yellow-500 bg-yellow-50";
      case "low":
        return "border-blue-500 bg-blue-50";
      default:
        return "border-gray-300 bg-gray-50";
    }
  };

  return (
    <Card
      className={`${getSeverityColor(alert.severity)} ${
        alert.acknowledged ? "opacity-60" : ""
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            <div className="mt-0.5">{getSeverityIcon(alert.severity)}</div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <h4 className="text-sm font-medium truncate">{alert.title}</h4>
                <Badge
                  variant={
                    alert.severity === "critical"
                      ? "destructive"
                      : alert.severity === "high"
                      ? "secondary"
                      : "default"
                  }
                >
                  {alert.severity}
                </Badge>
              </div>

              <p className="text-sm text-muted-foreground mb-2">
                {alert.message}
              </p>

              <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>{alert.timestamp.toLocaleString()}</span>
                </div>

                {alert.acknowledged && (
                  <div className="flex items-center space-x-1 text-green-600">
                    <Check className="w-3 h-3" />
                    <span>Acknowledged</span>
                  </div>
                )}

                {alert.resolved && (
                  <div className="flex items-center space-x-1 text-green-600">
                    <CheckCircle className="w-3 h-3" />
                    <span>Resolved</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-1 ml-2">
            {!alert.acknowledged && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onAcknowledge(alert.id)}
                title="Acknowledge"
              >
                <Check className="w-4 h-4" />
              </Button>
            )}

            {!alert.resolved && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onResolve(alert.id)}
                title="Resolve"
              >
                <CheckCircle className="w-4 h-4" />
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDismiss(alert.id)}
              title="Dismiss"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

interface NotificationCenterProps {
  maxVisible?: number;
  showResolved?: boolean;
  autoHide?: boolean;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left";
  notifications?: Array<{
    id: string;
    type: "success" | "error" | "info" | "warning";
    message: string;
    autoClose?: boolean;
    duration?: number;
  }>;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  maxVisible = 5,
  showResolved = false,
  autoHide = true,
  position = "top-right",
  notifications: contextNotifications = [],
}) => {
  const alerting = usePerformanceAlerting();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isVisible, setIsVisible] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Load alerts function - memoize to prevent infinite re-renders
  const loadAlerts = useCallback(() => {
    if (!alerting) return;

    const performanceAlerts = alerting.getAlerts({
      resolved: showResolved ? undefined : false,
    });

    // Convert context notifications to alert format for display
    const contextAlerts: Alert[] = contextNotifications.map((notification) => ({
      id: notification.id,
      ruleId: "context-notification",
      timestamp: new Date(),
      severity:
        notification.type === "error"
          ? "critical"
          : notification.type === "warning"
          ? "medium"
          : "low",
      title:
        notification.type.charAt(0).toUpperCase() + notification.type.slice(1),
      message: notification.message,
      data: {},
      acknowledged: false,
      resolved: false,
    }));

    const allAlerts = [...performanceAlerts, ...contextAlerts];
    setAlerts(allAlerts);

    const unread = allAlerts.filter(
      (alert) => !alert.acknowledged && !alert.resolved
    ).length;
    setUnreadCount(unread);
  }, [alerting, showResolved, contextNotifications]);

  // Load alerts on mount and when showResolved or contextNotifications change
  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  // Listen for new alerts
  useEffect(() => {
    const handleNewAlert = () => {
      loadAlerts();
      setIsVisible(true); // Show notification center when new alert arrives
    };

    window.addEventListener(
      "performance-alert-triggered",
      handleNewAlert as EventListener
    );

    return () => {
      window.removeEventListener(
        "performance-alert-triggered",
        handleNewAlert as EventListener
      );
    };
  }, [loadAlerts]);

  // Auto-hide functionality
  useEffect(() => {
    if (autoHide && isVisible && unreadCount === 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
      }, 5000); // Hide after 5 seconds if no unread alerts

      return () => clearTimeout(timer);
    }
  }, [autoHide, isVisible, unreadCount]);

  const handleAcknowledge = (alertId: string) => {
    if (alerting) {
      alerting.acknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId
            ? { ...alert, acknowledged: true, acknowledgedAt: new Date() }
            : alert
        )
      );
    }
  };

  const handleResolve = (alertId: string) => {
    if (alerting) {
      alerting.resolveAlert(alertId);
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId
            ? { ...alert, resolved: true, resolvedAt: new Date() }
            : alert
        )
      );
    }
  };

  const handleDismiss = async (alertId: string) => {
    try {
      // TODO: Add alerting service dismiss method when available
      // await alertService.dismiss(alertId);

      // For now, just update local state
      setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
    } catch (error) {
      console.error("Failed to dismiss alert:", error);
      // Rollback on failure - could implement optimistic updates here
    }
  };

  // Stable position class mapping
  const positionClasses = {
    "top-left": "top-4 left-4",
    "top-right": "top-4 right-4",
    "bottom-left": "bottom-4 left-4",
    "bottom-right": "bottom-4 right-4",
  };

  const getPositionClasses = () => {
    return positionClasses[position] || positionClasses["top-right"];
  };

  if (!alerting) return null;

  const visibleAlerts = alerts.slice(0, maxVisible);

  return (
    <>
      {/* Notification Bell */}
      <div className="relative">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsVisible(!isVisible)}
          className="relative"
        >
          {unreadCount > 0 ? (
            <Bell className="w-5 h-5" />
          ) : (
            <BellOff className="w-5 h-5" />
          )}
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
            >
              {unreadCount > 99 ? "99+" : unreadCount}
            </Badge>
          )}
        </Button>
      </div>

      {/* Notification Panel */}
      {isVisible && (
        <div
          className={`fixed ${getPositionClasses()} z-50 w-96 max-h-screen overflow-hidden`}
        >
          <Card className="shadow-lg border-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Performance Alerts</CardTitle>
                  <CardDescription>
                    {unreadCount > 0
                      ? `${unreadCount} unread alert${
                          unreadCount > 1 ? "s" : ""
                        }`
                      : "All alerts acknowledged"}
                  </CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" size="sm" title="Settings">
                    <Settings className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsVisible(false)}
                    title="Close"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-0">
              <div className="max-h-96 overflow-y-auto">
                {visibleAlerts.length === 0 ? (
                  <div className="p-6 text-center text-muted-foreground">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
                    <p>No performance alerts</p>
                    <p className="text-sm">System is running smoothly</p>
                  </div>
                ) : (
                  <div className="space-y-2 p-3">
                    {visibleAlerts.map((alert) => (
                      <NotificationItem
                        key={alert.id}
                        alert={alert}
                        onAcknowledge={handleAcknowledge}
                        onResolve={handleResolve}
                        onDismiss={handleDismiss}
                      />
                    ))}

                    {alerts.length > maxVisible && (
                      <div className="text-center py-2">
                        <Button variant="ghost" size="sm">
                          View {alerts.length - maxVisible} more alerts
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
};

// Toast notification component for immediate alerts
interface ToastNotificationProps {
  alert: Alert;
  onDismiss: () => void;
  duration?: number;
  index?: number;
}

export const ToastNotification: React.FC<ToastNotificationProps> = ({
  alert,
  onDismiss,
  duration = 5000,
  index = 0,
}) => {
  const onDismissRef = React.useRef(onDismiss);
  onDismissRef.current = onDismiss;

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => onDismissRef.current(), duration);
      return () => clearTimeout(timer);
    }
  }, [duration]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "border-red-500 bg-red-50 text-red-900";
      case "high":
        return "border-orange-500 bg-orange-50 text-orange-900";
      case "medium":
        return "border-yellow-500 bg-yellow-50 text-yellow-900";
      case "low":
        return "border-blue-500 bg-blue-50 text-blue-900";
      default:
        return "border-gray-300 bg-gray-50 text-gray-900";
    }
  };

  const baseTop = 16; // 1rem = 16px (top-4)
  const spacing = 96; // 6rem = 96px spacing between toasts
  const top = baseTop + index * spacing;

  return (
    <div
      className={`fixed right-4 z-50 w-80 p-4 rounded-lg border-2 shadow-lg ${getSeverityColor(
        alert.severity
      )} animate-in slide-in-from-right`}
      style={{ top: `${top}px` }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-medium text-sm mb-1">{alert.title}</h4>
          <p className="text-sm opacity-90">{alert.message}</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onDismiss}
          className="ml-2 h-6 w-6 p-0"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};

// Hook for managing toast notifications
export function useToastNotifications() {
  const [toasts, setToasts] = useState<Alert[]>([]);

  useEffect(() => {
    // Only run on client
    if (typeof window === "undefined") return;

    const handleNewAlert = (event: CustomEvent) => {
      const alert: Alert = event.detail;

      // Only show critical and high severity alerts as toasts
      if (alert.severity === "critical" || alert.severity === "high") {
        setToasts((prev) => [...prev, alert]);
      }
    };

    window.addEventListener(
      "performance-alert-triggered",
      handleNewAlert as EventListener
    );

    return () => {
      window.removeEventListener(
        "performance-alert-triggered",
        handleNewAlert as EventListener
      );
    };
  }, []);

  const dismissToast = (alertId: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== alertId));
  };

  return {
    toasts,
    dismissToast,
    // Render toasts with proper positioning
    renderToasts: () =>
      toasts.map((toast, index) => (
        <ToastNotification
          key={toast.id}
          alert={toast}
          index={index}
          onDismiss={() => dismissToast(toast.id)}
        />
      )),
  };
}
