"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export interface UserContextData {
  companyName: string;
  industry: string;
  competitors: string[];
  setupComplete: boolean;
}

interface UserContextType {
  userContext: UserContextData;
  setUserContext: (data: Partial<UserContextData>) => void;
  clearUserContext: () => void;
  isOnboarded: boolean;
  isLoaded: boolean;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

const DEFAULT_CONTEXT: UserContextData = {
  companyName: "",
  industry: "",
  competitors: [],
  setupComplete: false,
};

export const UserContextProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [userContext, setUserContextState] =
    useState<UserContextData>(DEFAULT_CONTEXT);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("enterpriseCIA_userContext");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setUserContextState(parsed);
      } catch (error) {
        console.error("Failed to parse user context:", error);
      }
    }
    setIsLoaded(true);
  }, []);

  // Save to localStorage whenever context changes
  useEffect(() => {
    if (isLoaded) {
      localStorage.setItem(
        "enterpriseCIA_userContext",
        JSON.stringify(userContext)
      );
    }
  }, [userContext, isLoaded]);

  const setUserContext = (data: Partial<UserContextData>) => {
    setUserContextState((prev) => ({
      ...prev,
      ...data,
      setupComplete: true,
    }));
  };

  const clearUserContext = () => {
    setUserContextState(DEFAULT_CONTEXT);
    localStorage.removeItem("enterpriseCIA_userContext");
  };

  const isOnboarded =
    userContext.setupComplete && Boolean(userContext.companyName);

  return (
    <UserContext.Provider
      value={{
        userContext,
        setUserContext,
        clearUserContext,
        isOnboarded,
        isLoaded,
      }}
    >
      {children}
    </UserContext.Provider>
  );
};

export const useUserContext = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUserContext must be used within UserContextProvider");
  }
  return context;
};

// Helper to get industry-specific competitors
export const getIndustryCompetitors = (industry: string): string[] => {
  const competitorMap: Record<string, string[]> = {
    "SaaS & Cloud Services": [
      "Salesforce",
      "Microsoft Azure",
      "AWS",
      "Google Cloud",
      "ServiceNow",
      "Workday",
    ],
    "Artificial Intelligence & ML": [
      "OpenAI",
      "Anthropic",
      "Google DeepMind",
      "Cohere",
      "Mistral AI",
      "Stability AI",
    ],
    "E-commerce & Retail": [
      "Amazon",
      "Shopify",
      "BigCommerce",
      "WooCommerce",
      "Magento",
      "Square",
    ],
    "Financial Services & Fintech": [
      "Stripe",
      "PayPal",
      "Square",
      "Plaid",
      "Braintree",
      "Adyen",
    ],
    "Healthcare & Life Sciences": [
      "Epic Systems",
      "Cerner",
      "Veeva",
      "Athenahealth",
      "Teladoc",
      "Oscar Health",
    ],
    "Enterprise Software": [
      "SAP",
      "Oracle",
      "Microsoft",
      "IBM",
      "Adobe",
      "Atlassian",
    ],
    "Consumer Technology": [
      "Apple",
      "Samsung",
      "Google",
      "Meta",
      "Snap",
      "Twitter/X",
    ],
    "Media & Entertainment": [
      "Netflix",
      "Disney+",
      "HBO Max",
      "Spotify",
      "YouTube",
      "TikTok",
    ],
    Cybersecurity: [
      "CrowdStrike",
      "Palo Alto Networks",
      "Okta",
      "Cloudflare",
      "Zscaler",
      "Fortinet",
    ],
    "Developer Tools & Infrastructure": [
      "GitHub",
      "GitLab",
      "Vercel",
      "Netlify",
      "HashiCorp",
      "Docker",
    ],
    "Marketing & Advertising Technology": [
      "HubSpot",
      "Marketo",
      "Mailchimp",
      "Hootsuite",
      "Sprinklr",
      "Adobe Marketing Cloud",
    ],
    Other: [
      "Competitor A",
      "Competitor B",
      "Competitor C",
      "Competitor D",
      "Competitor E",
    ],
  };

  return competitorMap[industry] || competitorMap["Other"];
};
