import {
  TribeUser,
  InterfaceMode,
  TribePreferences,
} from "./types/tribe-interface";

/**
 * Persistence layer for Tribe Interface System
 * Handles localStorage, sessionStorage, and API persistence
 */
export class TribePersistence {
  private readonly STORAGE_KEYS = {
    USER_PREFERENCES: "tribe_user_preferences",
    CURRENT_MODE: "tribe_current_mode",
    MODE_HISTORY: "tribe_mode_history",
    USER_PROFILE: "tribe_user_profile",
    ADAPTATION_METRICS: "tribe_adaptation_metrics",
    ROLE_DETECTION: "tribe_role_detection",
    SATISFACTION_SCORES: "tribe_satisfaction_scores",
  };

  private readonly MAX_HISTORY_LENGTH = 20;
  private readonly STORAGE_VERSION = "1.0";

  /**
   * Save user preferences to localStorage
   */
  saveUserPreferences(preferences: TribePreferences): void {
    try {
      const data = {
        version: this.STORAGE_VERSION,
        timestamp: new Date().toISOString(),
        preferences,
      };
      localStorage.setItem(
        this.STORAGE_KEYS.USER_PREFERENCES,
        JSON.stringify(data)
      );
    } catch (error) {
      console.warn("Failed to save user preferences:", error);
    }
  }

  /**
   * Load user preferences from localStorage
   */
  loadUserPreferences(): TribePreferences | null {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEYS.USER_PREFERENCES);
      if (!stored) return null;

      const data = JSON.parse(stored);

      // Check version compatibility
      if (data.version !== this.STORAGE_VERSION) {
        console.warn("Preferences version mismatch, using defaults");
        return null;
      }

      return data.preferences;
    } catch (error) {
      console.warn("Failed to load user preferences:", error);
      return null;
    }
  }

  /**
   * Save current interface mode
   */
  saveCurrentMode(mode: InterfaceMode): void {
    try {
      const data = {
        mode,
        timestamp: new Date().toISOString(),
        sessionId: this.getSessionId(),
      };
      localStorage.setItem(
        this.STORAGE_KEYS.CURRENT_MODE,
        JSON.stringify(data)
      );

      // Also save to sessionStorage for session-specific tracking
      sessionStorage.setItem("tribe_session_mode", mode);
    } catch (error) {
      console.warn("Failed to save current mode:", error);
    }
  }

  /**
   * Load current interface mode
   */
  loadCurrentMode(): InterfaceMode | null {
    try {
      // First check sessionStorage for session-specific mode
      const sessionMode = sessionStorage.getItem(
        "tribe_session_mode"
      ) as InterfaceMode;
      if (
        sessionMode &&
        ["executive", "analyst", "team"].includes(sessionMode)
      ) {
        return sessionMode;
      }

      // Fall back to localStorage
      const stored = localStorage.getItem(this.STORAGE_KEYS.CURRENT_MODE);
      if (!stored) return null;

      const data = JSON.parse(stored);
      return data.mode;
    } catch (error) {
      console.warn("Failed to load current mode:", error);
      return null;
    }
  }

  /**
   * Save mode switching history
   */
  saveModeHistory(history: InterfaceMode[]): void {
    try {
      const trimmedHistory = history.slice(-this.MAX_HISTORY_LENGTH);
      const data = {
        history: trimmedHistory,
        timestamp: new Date().toISOString(),
      };
      localStorage.setItem(
        this.STORAGE_KEYS.MODE_HISTORY,
        JSON.stringify(data)
      );
    } catch (error) {
      console.warn("Failed to save mode history:", error);
    }
  }

  /**
   * Load mode switching history
   */
  loadModeHistory(): InterfaceMode[] {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEYS.MODE_HISTORY);
      if (!stored) return [];

      const data = JSON.parse(stored);
      return data.history || [];
    } catch (error) {
      console.warn("Failed to load mode history:", error);
      return [];
    }
  }

  /**
   * Add mode switch to history
   */
  addModeSwitch(fromMode: InterfaceMode, toMode: InterfaceMode): void {
    const history = this.loadModeHistory();
    const switchRecord = {
      from: fromMode,
      to: toMode,
      timestamp: new Date().toISOString(),
      sessionId: this.getSessionId(),
    };

    // Add to history (we'll store the 'to' mode for simplicity)
    history.push(toMode);
    this.saveModeHistory(history);

    // Also track detailed switch data
    this.saveSwitchAnalytics(switchRecord);
  }

  /**
   * Save user profile data
   */
  saveUserProfile(user: TribeUser): void {
    try {
      const data = {
        version: this.STORAGE_VERSION,
        timestamp: new Date().toISOString(),
        user: {
          id: user.id,
          role: user.role,
          department: user.department,
          seniority: user.seniority,
          preferences: user.preferences,
        },
      };
      localStorage.setItem(
        this.STORAGE_KEYS.USER_PROFILE,
        JSON.stringify(data)
      );
    } catch (error) {
      console.warn("Failed to save user profile:", error);
    }
  }

  /**
   * Load user profile data
   */
  loadUserProfile(): TribeUser | null {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEYS.USER_PROFILE);
      if (!stored) return null;

      const data = JSON.parse(stored);

      if (data.version !== this.STORAGE_VERSION) {
        return null;
      }

      return data.user;
    } catch (error) {
      console.warn("Failed to load user profile:", error);
      return null;
    }
  }

  /**
   * Save adaptation metrics
   */
  saveAdaptationMetrics(metrics: {
    contentFiltered: number;
    complexityReduced: number;
    userSatisfaction: number;
  }): void {
    try {
      const data = {
        metrics,
        timestamp: new Date().toISOString(),
        sessionId: this.getSessionId(),
      };
      localStorage.setItem(
        this.STORAGE_KEYS.ADAPTATION_METRICS,
        JSON.stringify(data)
      );
    } catch (error) {
      console.warn("Failed to save adaptation metrics:", error);
    }
  }

  /**
   * Load adaptation metrics
   */
  loadAdaptationMetrics(): {
    contentFiltered: number;
    complexityReduced: number;
    userSatisfaction: number;
  } | null {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEYS.ADAPTATION_METRICS);
      if (!stored) return null;

      const data = JSON.parse(stored);
      return data.metrics;
    } catch (error) {
      console.warn("Failed to load adaptation metrics:", error);
      return null;
    }
  }

  /**
   * Save role detection data for learning
   */
  saveRoleDetection(
    detectedRole: string,
    actualRole: string,
    confidence: number
  ): void {
    try {
      const existing = this.loadRoleDetectionHistory();
      const newEntry = {
        detectedRole,
        actualRole,
        confidence,
        timestamp: new Date().toISOString(),
        sessionId: this.getSessionId(),
      };

      existing.push(newEntry);

      // Keep only recent entries
      const trimmed = existing.slice(-50);

      localStorage.setItem(
        this.STORAGE_KEYS.ROLE_DETECTION,
        JSON.stringify(trimmed)
      );
    } catch (error) {
      console.warn("Failed to save role detection data:", error);
    }
  }

  /**
   * Load role detection history
   */
  loadRoleDetectionHistory(): Array<{
    detectedRole: string;
    actualRole: string;
    confidence: number;
    timestamp: string;
    sessionId: string;
  }> {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEYS.ROLE_DETECTION);
      if (!stored) return [];

      return JSON.parse(stored);
    } catch (error) {
      console.warn("Failed to load role detection history:", error);
      return [];
    }
  }

  /**
   * Save satisfaction scores
   */
  saveSatisfactionScore(
    mode: InterfaceMode,
    score: number,
    feedback?: string
  ): void {
    try {
      const existing = this.loadSatisfactionScores();
      const newEntry = {
        mode,
        score,
        feedback,
        timestamp: new Date().toISOString(),
        sessionId: this.getSessionId(),
      };

      existing.push(newEntry);

      // Keep only recent entries
      const trimmed = existing.slice(-100);

      localStorage.setItem(
        this.STORAGE_KEYS.SATISFACTION_SCORES,
        JSON.stringify(trimmed)
      );
    } catch (error) {
      console.warn("Failed to save satisfaction score:", error);
    }
  }

  /**
   * Load satisfaction scores
   */
  loadSatisfactionScores(): Array<{
    mode: InterfaceMode;
    score: number;
    feedback?: string;
    timestamp: string;
    sessionId: string;
  }> {
    try {
      const stored = localStorage.getItem(
        this.STORAGE_KEYS.SATISFACTION_SCORES
      );
      if (!stored) return [];

      return JSON.parse(stored);
    } catch (error) {
      console.warn("Failed to load satisfaction scores:", error);
      return [];
    }
  }

  /**
   * Get average satisfaction score for a mode
   */
  getAverageSatisfaction(mode: InterfaceMode): number {
    const scores = this.loadSatisfactionScores()
      .filter((entry) => entry.mode === mode)
      .map((entry) => entry.score);

    if (scores.length === 0) return 0;

    return scores.reduce((sum, score) => sum + score, 0) / scores.length;
  }

  /**
   * Clear all stored data
   */
  clearAllData(): void {
    try {
      Object.values(this.STORAGE_KEYS).forEach((key) => {
        localStorage.removeItem(key);
      });
      sessionStorage.removeItem("tribe_session_mode");
    } catch (error) {
      console.warn("Failed to clear stored data:", error);
    }
  }

  /**
   * Export all data for backup or analysis
   */
  exportData(): any {
    const data: any = {};

    try {
      Object.entries(this.STORAGE_KEYS).forEach(([key, storageKey]) => {
        const stored = localStorage.getItem(storageKey);
        if (stored) {
          try {
            data[key] = JSON.parse(stored);
          } catch {
            data[key] = stored;
          }
        }
      });

      data.exportTimestamp = new Date().toISOString();
      data.version = this.STORAGE_VERSION;

      return data;
    } catch (error) {
      console.warn("Failed to export data:", error);
      return null;
    }
  }

  /**
   * Import data from backup
   */
  importData(data: any): boolean {
    try {
      if (data.version !== this.STORAGE_VERSION) {
        console.warn("Data version mismatch during import");
        return false;
      }

      Object.entries(this.STORAGE_KEYS).forEach(([key, storageKey]) => {
        if (data[key]) {
          const value =
            typeof data[key] === "string"
              ? data[key]
              : JSON.stringify(data[key]);
          localStorage.setItem(storageKey, value);
        }
      });

      return true;
    } catch (error) {
      console.warn("Failed to import data:", error);
      return false;
    }
  }

  /**
   * Get usage analytics
   */
  getUsageAnalytics(): {
    totalSessions: number;
    modeSwitches: number;
    averageSatisfaction: number;
    mostUsedMode: InterfaceMode | null;
    sessionDuration: number;
  } {
    try {
      const history = this.loadModeHistory();
      const satisfactionScores = this.loadSatisfactionScores();
      const switchAnalytics = this.loadSwitchAnalytics();

      // Count mode usage
      const modeUsage: Record<InterfaceMode, number> = {
        executive: 0,
        analyst: 0,
        team: 0,
      };

      history.forEach((mode) => {
        if (modeUsage[mode] !== undefined) {
          modeUsage[mode]++;
        }
      });

      const mostUsedMode =
        (Object.entries(modeUsage).sort(
          ([, a], [, b]) => b - a
        )[0]?.[0] as InterfaceMode) || null;

      const averageSatisfaction =
        satisfactionScores.length > 0
          ? satisfactionScores.reduce((sum, entry) => sum + entry.score, 0) /
            satisfactionScores.length
          : 0;

      return {
        totalSessions: new Set(switchAnalytics.map((s) => s.sessionId)).size,
        modeSwitches: switchAnalytics.length,
        averageSatisfaction,
        mostUsedMode,
        sessionDuration: this.calculateAverageSessionDuration(),
      };
    } catch (error) {
      console.warn("Failed to get usage analytics:", error);
      return {
        totalSessions: 0,
        modeSwitches: 0,
        averageSatisfaction: 0,
        mostUsedMode: null,
        sessionDuration: 0,
      };
    }
  }

  /**
   * Get or create session ID
   */
  private getSessionId(): string {
    let sessionId = sessionStorage.getItem("tribe_session_id");
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random()
        .toString(36)
        .substr(2, 9)}`;
      sessionStorage.setItem("tribe_session_id", sessionId);
    }
    return sessionId;
  }

  /**
   * Save detailed switch analytics
   */
  private saveSwitchAnalytics(switchRecord: any): void {
    try {
      const existing = this.loadSwitchAnalytics();
      existing.push(switchRecord);

      // Keep only recent switches
      const trimmed = existing.slice(-200);

      localStorage.setItem("tribe_switch_analytics", JSON.stringify(trimmed));
    } catch (error) {
      console.warn("Failed to save switch analytics:", error);
    }
  }

  /**
   * Load switch analytics
   */
  private loadSwitchAnalytics(): Array<{
    from: InterfaceMode;
    to: InterfaceMode;
    timestamp: string;
    sessionId: string;
  }> {
    try {
      const stored = localStorage.getItem("tribe_switch_analytics");
      if (!stored) return [];

      return JSON.parse(stored);
    } catch (error) {
      console.warn("Failed to load switch analytics:", error);
      return [];
    }
  }

  /**
   * Calculate average session duration
   */
  private calculateAverageSessionDuration(): number {
    try {
      const switches = this.loadSwitchAnalytics();
      const sessions: Record<string, { start: number; end: number }> = {};

      switches.forEach((switchRecord) => {
        const timestamp = new Date(switchRecord.timestamp).getTime();
        const sessionId = switchRecord.sessionId;

        if (!sessions[sessionId]) {
          sessions[sessionId] = { start: timestamp, end: timestamp };
        } else {
          sessions[sessionId].end = Math.max(
            sessions[sessionId].end,
            timestamp
          );
        }
      });

      const durations = Object.values(sessions)
        .map((session) => session.end - session.start)
        .filter((duration) => duration > 0);

      if (durations.length === 0) return 0;

      return (
        durations.reduce((sum, duration) => sum + duration, 0) /
        durations.length
      );
    } catch (error) {
      console.warn("Failed to calculate session duration:", error);
      return 0;
    }
  }
}

// Singleton instance - lazy initialization to avoid circular dependencies
let _tribePersistence: TribePersistence | null = null;
export const tribePersistence = () => {
  if (!_tribePersistence) {
    _tribePersistence = new TribePersistence();
  }
  return _tribePersistence;
};
