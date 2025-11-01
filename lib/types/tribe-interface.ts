// Tribe Interface System Types
export type UserRole = "executive" | "analyst" | "team";
export type InterfaceMode = "executive" | "analyst" | "team";

export interface TribeUser {
  id: string;
  role: UserRole;
  preferences: TribePreferences;
  permissions: string[];
  department?: string;
  seniority?: "junior" | "senior" | "lead" | "director" | "vp" | "c-level";
}

export interface TribePreferences {
  defaultMode: InterfaceMode;
  maxInsights: number;
  showTechnicalDetails: boolean;
  enableCollaboration: boolean;
  summaryLevel: "high" | "medium" | "detailed";
  thresholds: {
    riskScore: number;
    confidenceScore: number;
    sourceCount: number;
  };
  notifications: {
    email: boolean;
    inApp: boolean;
    slack: boolean;
    frequency: "immediate" | "hourly" | "daily";
  };
}

export interface InterfaceModeConfig {
  name: InterfaceMode;
  maxInsights: number;
  showTechnicalDetails: boolean;
  enableCollaboration: boolean;
  summaryLevel: "high" | "medium" | "detailed";
  cognitiveLoadLimit: number;
  features: {
    apiMetrics: boolean;
    sourceBreakdown: boolean;
    explainability: boolean;
    annotations: boolean;
    sharing: boolean;
    advancedFilters: boolean;
  };
}

export interface ContentFilter {
  filterTechnicalJargon: boolean;
  maxComplexity: number;
  prioritizeActions: boolean;
  hideImplementationDetails: boolean;
  summarizeEvidence: boolean;
}

export interface AdaptedContent {
  title: string;
  summary: string;
  insights: string[];
  actions: string[];
  technicalDetails?: any;
  metadata: {
    originalComplexity: number;
    adaptedComplexity: number;
    filteringApplied: string[];
  };
}

export interface TribeInterfaceState {
  currentMode: InterfaceMode;
  detectedRole: UserRole | null;
  user: TribeUser | null;
  modeHistory: InterfaceMode[];
  lastModeSwitch: Date | null;
  adaptationMetrics: {
    contentFiltered: number;
    complexityReduced: number;
    userSatisfaction: number;
  };
}
