"use client";

import "./globals.css";
import { Providers } from "./providers";
import { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
import dynamic from "next/dynamic";

// Import NotificationCenter dynamically to prevent SSR hydration issues
const DynamicNotificationCenter = dynamic(
  () => import("@/components/ClientOnlyNotificationCenter"),
  {
    ssr: false,
  }
);
import { UserContextProvider, useUserContext } from "@/contexts/UserContext";
import {
  NotificationProvider,
  useNotificationContext,
} from "@/app/notifications/NotificationProvider";
import { OnboardingModal } from "@/components/OnboardingModal";
import { FloatingChatWidget } from "@/components/FloatingChatWidget";

import { RouteLoadingBoundary } from "@/components/RouteLoadingBoundary";
import { ServiceWorkerProvider } from "@/components/ServiceWorkerProvider";
import { useRoutePrefetching } from "@/lib/hooks/useRoutePrefetching";

function LayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [showOnboarding, setShowOnboarding] = useState(false);
  const { isOnboarded, setUserContext, isLoaded } = useUserContext();
  const { handleLinkHover, currentRoute } = useRoutePrefetching();

  // Check onboarding status on mount
  useEffect(() => {
    // Check for skip parameter in URL
    const urlParams = new URLSearchParams(window.location.search);
    const skipOnboarding = urlParams.get("skip-onboarding") === "true";

    if (skipOnboarding && !isOnboarded) {
      // Auto-complete onboarding for demo purposes (only if not already onboarded)
      setUserContext({
        companyName: "You.com",
        industry: "Artificial Intelligence & ML",
      });
      return;
    }

    if (isLoaded && !isOnboarded && pathname !== "/demo") {
      setShowOnboarding(true);
    }
  }, [isLoaded, isOnboarded, pathname, setUserContext]); // Fixed: Added setUserContext to dependencies

  const { addNotification } = useNotificationContext();

  const handleOnboardingComplete = (data: {
    companyName: string;
    industry: string;
  }) => {
    setUserContext(data);
    setShowOnboarding(false);
    addNotification({
      type: "success",
      message: `Welcome ${data.companyName}! Your dashboard is now personalized for ${data.industry}.`,
    });
  };

  // Get active item from pathname
  const getActiveItem = (path: string) => {
    if (path === "/" || path === "/dashboard") return "dashboard";
    if (path === "/demo") return "demo";
    return path.split("/")[1] || "dashboard";
  };

  const activeItem = getActiveItem(pathname);

  const handleNavigation = (itemId: string) => {
    const route =
      itemId === "dashboard" ? "/" : itemId === "demo" ? "/demo" : `/${itemId}`;
    router.push(route);
  };

  const handleStartAnalysis = () => {
    // Navigate to monitoring page where users can start analyses
    router.push("/monitoring");
    addNotification({
      type: "info",
      message: "Navigate to monitoring to start competitive analysis",
    });
  };

  return (
    <>
      <div className="flex h-screen bg-gray-50">
        <Sidebar activeItem={activeItem} onItemClick={handleNavigation} />
        <div className="flex-1 flex flex-col">
          <Header
            onStartAnalysis={handleStartAnalysis}
            currentPath={activeItem}
          />

          {/* Active Page Indicator */}
          <div className="px-6 py-2 bg-blue-50 border-b border-blue-100">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-sm font-medium text-blue-900 capitalize">
                {activeItem} {activeItem === "demo" ? "- API Showcase" : ""}
                {activeItem === "dashboard" ? "- Intelligence Hub" : ""}
              </span>
            </div>
          </div>
          <main className="flex-1 overflow-auto p-6">
            <RouteLoadingBoundary routeKey={currentRoute}>
              {children}
            </RouteLoadingBoundary>
          </main>
        </div>
      </div>
      <DynamicNotificationCenter
        maxVisible={5}
        showResolved={false}
        autoHide={true}
        position="top-right"
      />
      <OnboardingModal
        isOpen={showOnboarding}
        onComplete={handleOnboardingComplete}
      />
      <FloatingChatWidget />
    </>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Add favicon links dynamically for client component
  useEffect(() => {
    if (typeof window === "undefined") return;

    // Remove existing favicon links if any
    const existingLinks = document.querySelectorAll(
      'link[rel="icon"], link[rel="apple-touch-icon"]'
    );
    existingLinks.forEach((link) => link.remove());

    // Add favicon link
    const favicon = document.createElement("link");
    favicon.rel = "icon";
    favicon.href = "/icon.svg";
    favicon.type = "image/svg+xml";
    document.head.appendChild(favicon);

    // Add apple touch icon
    const appleIcon = document.createElement("link");
    appleIcon.rel = "apple-touch-icon";
    appleIcon.href = "/apple-icon.svg";
    appleIcon.type = "image/svg+xml";
    document.head.appendChild(appleIcon);

    // Also add for /favicon.ico to prevent 404
    const faviconIco = document.createElement("link");
    faviconIco.rel = "icon";
    faviconIco.href = "/icon.svg";
    faviconIco.type = "image/svg+xml";
    document.head.appendChild(faviconIco);
  }, []);

  return (
    <html lang="en">
      <body className="font-sans">
        <Providers>
          <UserContextProvider>
            <NotificationProvider>
              <ServiceWorkerProvider>
                <LayoutContent>{children}</LayoutContent>
              </ServiceWorkerProvider>
            </NotificationProvider>
          </UserContextProvider>
        </Providers>
      </body>
    </html>
  );
}
