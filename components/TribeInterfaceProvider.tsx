"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { tribeInterfaceSystem } from "@/lib/tribe-interface-system";
import {
  TribeUser,
  UserRole,
  InterfaceMode,
  InterfaceModeConfig,
  TribeInterfaceState,
} from "@/lib/types/tribe-interface";

interface TribeInterfaceContextType {
  currentMode: InterfaceMode;
  modeConfig: InterfaceModeConfig;
  user: TribeUser | null;
  detectedRole: UserRole | null;
  state: TribeInterfaceState;
  switchMode: (mode: InterfaceMode) => void;
  isFeatureEnabled: (feature: keyof InterfaceModeConfig["features"]) => boolean;
  adaptContent: (content: any) => any;
  recordSatisfaction: (rating: number) => void;
  suggestMode: (role: UserRole) => InterfaceMode;
}

const TribeInterfaceContext = createContext<
  TribeInterfaceContextType | undefined
>(undefined);

interface TribeInterfaceProviderProps {
  children: ReactNode;
  user?: TribeUser;
}

export function TribeInterfaceProvider({
  children,
  user,
}: TribeInterfaceProviderProps) {
  const [state, setState] = useState<TribeInterfaceState>(
    tribeInterfaceSystem().getState()
  );
  const [modeConfig, setModeConfig] = useState<InterfaceModeConfig>(
    tribeInterfaceSystem().getCurrentModeConfig()
  );

  // Initialize the system
  useEffect(() => {
    tribeInterfaceSystem().initialize(user);
    setState(tribeInterfaceSystem().getState());
    setModeConfig(tribeInterfaceSystem().getCurrentModeConfig());
  }, [user]);

  // Update state when mode changes
  useEffect(() => {
    const updateState = () => {
      setState(tribeInterfaceSystem().getState());
      setModeConfig(tribeInterfaceSystem().getCurrentModeConfig());
    };

    // Listen for mode changes (if we had events)
    updateState();
  }, [state.currentMode]);

  const switchMode = (mode: InterfaceMode) => {
    tribeInterfaceSystem().switchMode(mode, user);
    setState(tribeInterfaceSystem().getState());
    setModeConfig(tribeInterfaceSystem().getCurrentModeConfig());
  };

  const isFeatureEnabled = (
    feature: keyof InterfaceModeConfig["features"]
  ): boolean => {
    return tribeInterfaceSystem().isFeatureEnabled(feature);
  };

  const adaptContent = (content: any) => {
    return tribeInterfaceSystem().adaptContent(content);
  };

  const recordSatisfaction = (rating: number) => {
    tribeInterfaceSystem().recordSatisfaction(rating);
    setState(tribeInterfaceSystem().getState());
  };

  const suggestMode = (role: UserRole): InterfaceMode => {
    return tribeInterfaceSystem().suggestMode(role);
  };

  const contextValue: TribeInterfaceContextType = {
    currentMode: state.currentMode,
    modeConfig,
    user: state.user,
    detectedRole: state.detectedRole,
    state,
    switchMode,
    isFeatureEnabled,
    adaptContent,
    recordSatisfaction,
    suggestMode,
  };

  return (
    <TribeInterfaceContext.Provider value={contextValue}>
      {children}
    </TribeInterfaceContext.Provider>
  );
}

export function useTribeInterface(): TribeInterfaceContextType {
  const context = useContext(TribeInterfaceContext);
  if (context === undefined) {
    throw new Error(
      "useTribeInterface must be used within a TribeInterfaceProvider"
    );
  }
  return context;
}
