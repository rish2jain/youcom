/**
 * Loading State Management System
 * Coordinates component loading states and progress tracking
 */

import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";

export interface LoadingState {
  component: string;
  status: "idle" | "loading" | "loaded" | "error";
  progress?: number;
  startTime?: number;
  endTime?: number;
  error?: string;
}

export interface LoadingMetrics {
  totalComponents: number;
  loadedComponents: number;
  failedComponents: number;
  overallProgress: number;
  averageLoadTime: number;
  isLoading: boolean;
}

interface LoadingStateStore {
  states: Map<string, LoadingState>;
  metrics: LoadingMetrics;

  // Actions
  setLoading: (component: string, progress?: number) => void;
  setLoaded: (component: string) => void;
  setError: (component: string, error: string) => void;
  setProgress: (component: string, progress: number) => void;
  reset: (component?: string) => void;

  // Getters
  getState: (component: string) => LoadingState | undefined;
  getMetrics: () => LoadingMetrics;
  isComponentLoading: (component: string) => boolean;
  isAnyLoading: () => boolean;
}

/**
 * Calculate loading metrics from current states
 */
function calculateMetrics(states: Map<string, LoadingState>): LoadingMetrics {
  const stateArray = Array.from(states.values());
  const totalComponents = stateArray.length;
  const loadedComponents = stateArray.filter(
    (s) => s.status === "loaded"
  ).length;
  const failedComponents = stateArray.filter(
    (s) => s.status === "error"
  ).length;
  const loadingComponents = stateArray.filter(
    (s) => s.status === "loading"
  ).length;

  // Calculate overall progress
  const totalProgress = stateArray.reduce((sum, state) => {
    if (state.status === "loaded") return sum + 100;
    if (state.status === "loading") return sum + (state.progress || 0);
    if (state.status === "error") return sum + 0;
    return sum;
  }, 0);

  const overallProgress =
    totalComponents > 0 ? totalProgress / totalComponents : 0;

  // Calculate average load time for completed components
  const completedStates = stateArray.filter(
    (s) => s.status === "loaded" && s.startTime && s.endTime
  );

  const averageLoadTime =
    completedStates.length > 0
      ? completedStates.reduce(
          (sum, state) => sum + (state.endTime! - state.startTime!),
          0
        ) / completedStates.length
      : 0;

  return {
    totalComponents,
    loadedComponents,
    failedComponents,
    overallProgress,
    averageLoadTime,
    isLoading: loadingComponents > 0,
  };
}

/**
 * Zustand store for loading state management
 */
export const useLoadingStateStore = create<LoadingStateStore>()(
  subscribeWithSelector((set, get) => ({
    states: new Map<string, LoadingState>(),
    metrics: {
      totalComponents: 0,
      loadedComponents: 0,
      failedComponents: 0,
      overallProgress: 0,
      averageLoadTime: 0,
      isLoading: false,
    },

    setLoading: (component: string, progress = 0) => {
      set((state) => {
        const newStates = new Map(state.states);
        newStates.set(component, {
          component,
          status: "loading",
          progress,
          startTime: Date.now(),
        });

        return {
          states: newStates,
          metrics: calculateMetrics(newStates),
        };
      });
    },

    setLoaded: (component: string) => {
      set((state) => {
        const newStates = new Map(state.states);
        const currentState = newStates.get(component);

        newStates.set(component, {
          component,
          status: "loaded",
          progress: 100,
          startTime: currentState?.startTime,
          endTime: Date.now(),
        });

        return {
          states: newStates,
          metrics: calculateMetrics(newStates),
        };
      });
    },

    setError: (component: string, error: string) => {
      set((state) => {
        const newStates = new Map(state.states);
        const currentState = newStates.get(component);

        newStates.set(component, {
          component,
          status: "error",
          progress: 0,
          startTime: currentState?.startTime,
          endTime: Date.now(),
          error,
        });

        return {
          states: newStates,
          metrics: calculateMetrics(newStates),
        };
      });
    },

    setProgress: (component: string, progress: number) => {
      set((state) => {
        const newStates = new Map(state.states);
        const currentState = newStates.get(component);

        if (currentState && currentState.status === "loading") {
          newStates.set(component, {
            ...currentState,
            progress: Math.min(100, Math.max(0, progress)),
          });

          return {
            states: newStates,
            metrics: calculateMetrics(newStates),
          };
        }

        return state;
      });
    },

    reset: (component?: string) => {
      set((state) => {
        if (component) {
          const newStates = new Map(state.states);
          newStates.delete(component);

          return {
            states: newStates,
            metrics: calculateMetrics(newStates),
          };
        } else {
          return {
            states: new Map(),
            metrics: {
              totalComponents: 0,
              loadedComponents: 0,
              failedComponents: 0,
              overallProgress: 0,
              averageLoadTime: 0,
              isLoading: false,
            },
          };
        }
      });
    },

    getState: (component: string) => {
      return get().states.get(component);
    },

    getMetrics: () => {
      return get().metrics;
    },

    isComponentLoading: (component: string) => {
      const state = get().states.get(component);
      return state?.status === "loading";
    },

    isAnyLoading: () => {
      return get().metrics.isLoading;
    },
  }))
);

/**
 * Loading State Manager Class
 * Provides a class-based interface for managing loading states
 */
export class LoadingStateManager {
  private store = useLoadingStateStore;
  private subscribers = new Set<(metrics: LoadingMetrics) => void>();

  constructor() {
    // Subscribe to store changes and notify subscribers
    this.store.subscribe(
      (state) => state.metrics,
      (metrics) => {
        this.subscribers.forEach((callback) => callback(metrics));
      }
    );
  }

  setLoading(component: string, progress?: number): void {
    this.store.getState().setLoading(component, progress);
  }

  setLoaded(component: string): void {
    this.store.getState().setLoaded(component);
  }

  setError(component: string, error: string): void {
    this.store.getState().setError(component, error);
  }

  setProgress(component: string, progress: number): void {
    this.store.getState().setProgress(component, progress);
  }

  reset(component?: string): void {
    this.store.getState().reset(component);
  }

  getState(component: string): LoadingState | undefined {
    return this.store.getState().getState(component);
  }

  getMetrics(): LoadingMetrics {
    return this.store.getState().getMetrics();
  }

  isComponentLoading(component: string): boolean {
    return this.store.getState().isComponentLoading(component);
  }

  isAnyLoading(): boolean {
    return this.store.getState().isAnyLoading();
  }

  subscribe(callback: (metrics: LoadingMetrics) => void): () => void {
    this.subscribers.add(callback);

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(callback);
    };
  }

  /**
   * Persist loading state to localStorage for recovery
   */
  persistState(): void {
    try {
      const states = Array.from(this.store.getState().states.entries());
      localStorage.setItem("loadingStates", JSON.stringify(states));
    } catch (error) {
      console.warn("Failed to persist loading state:", error);
    }
  }

  /**
   * Recover loading state from localStorage
   */
  recoverState(): void {
    try {
      const stored = localStorage.getItem("loadingStates");
      if (stored) {
        const states = JSON.parse(stored);
        const stateMap = new Map(states);

        // Only recover non-loading states to avoid stale loading indicators
        const filteredStates = new Map();
        stateMap.forEach((state: any, key) => {
          if (state.status !== "loading") {
            filteredStates.set(key, state);
          }
        });

        this.store.setState({
          states: filteredStates,
          metrics: calculateMetrics(filteredStates),
        });
      }
    } catch (error) {
      console.warn("Failed to recover loading state:", error);
    }
  }
}

// Global instance
export const loadingStateManager = new LoadingStateManager();

// Auto-persist state changes
if (typeof window !== "undefined") {
  useLoadingStateStore.subscribe(
    (state) => state.states,
    () => {
      loadingStateManager.persistState();
    }
  );

  // Recover state on page load
  loadingStateManager.recoverState();
}
