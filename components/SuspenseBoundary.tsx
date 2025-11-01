"use client";

import React, { Suspense, ReactNode } from "react";
import { LoadingSkeleton } from "./LoadingSkeleton";

interface SuspenseBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  variant?: "card" | "dashboard" | "widget" | "list";
  count?: number;
  className?: string;
}

/**
 * Enhanced Suspense boundary with customizable loading states
 */
export function SuspenseBoundary({
  children,
  fallback,
  variant = "card",
  count = 1,
  className = "",
}: SuspenseBoundaryProps) {
  const defaultFallback = (
    <div className={className}>
      <LoadingSkeleton variant={variant} count={count} />
    </div>
  );

  return <Suspense fallback={fallback || defaultFallback}>{children}</Suspense>;
}

/**
 * Specialized Suspense boundaries for different use cases
 */
export function CardSuspenseBoundary({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <SuspenseBoundary variant="card" className={className}>
      {children}
    </SuspenseBoundary>
  );
}

export function DashboardSuspenseBoundary({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <SuspenseBoundary variant="dashboard" className={className}>
      {children}
    </SuspenseBoundary>
  );
}

export function WidgetSuspenseBoundary({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <SuspenseBoundary variant="widget" className={className}>
      {children}
    </SuspenseBoundary>
  );
}

export function ListSuspenseBoundary({
  children,
  count = 3,
  className,
}: {
  children: ReactNode;
  count?: number;
  className?: string;
}) {
  return (
    <SuspenseBoundary variant="list" count={count} className={className}>
      {children}
    </SuspenseBoundary>
  );
}
