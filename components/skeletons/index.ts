/**
 * Skeleton Components Export
 * Centralized exports for all skeleton components
 */

export { LoadingSkeleton } from "../LoadingSkeleton";
export {
  ImpactCardSkeleton,
  ImpactCardSkeletonCompact,
} from "./ImpactCardSkeleton";
export {
  DashboardSkeleton,
  DashboardSkeletonSimple,
} from "./DashboardSkeleton";

// Re-export skeleton variants for convenience
export const SkeletonVariants = {
  Card: "card",
  Dashboard: "dashboard",
  Widget: "widget",
  List: "list",
  ImpactCard: "impact-card",
  Chart: "chart",
  Table: "table",
} as const;

export type SkeletonVariant =
  (typeof SkeletonVariants)[keyof typeof SkeletonVariants];
