"use client";

import "./globals.css";
import { Providers } from "./providers";
import { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
import NotificationSystem from "@/components/NotificationSystem";
import { UserContextProvider, useUserContext } from "@/contexts/UserContext";
import { OnboardingModal } from "@/components/OnboardingModal";
import { FloatingChatWidget } from "@/components/FloatingChatWidget";

interface Notification {
  id: string;
  type: "success" | "error" | "info" | "warning";
  message: string;
  autoClose?: boolean;
  duration?: number;
}

function LayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const { isOnboarded, setUserContext, isLoaded } = useUserContext();

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
  }, [isLoaded, isOnboarded, pathname]); // Removed setUserContext from dependencies

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
    addNotification({
      type: "info",
      message: "Starting new competitive analysis...",
    });
  };

  const addNotification = (notification: Omit<Notification, "id">) => {
    const id = Date.now().toString();
    setNotifications((prev) => [...prev, { ...notification, id }]);
  };

  const removeNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
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
          <main className="flex-1 overflow-auto p-6">{children}</main>
        </div>
      </div>
      <NotificationSystem
        notifications={notifications}
        onRemove={removeNotification}
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
  return (
    <html lang="en">
      <body className="font-sans">
        <Providers>
          <UserContextProvider>
            <LayoutContent>{children}</LayoutContent>
          </UserContextProvider>
        </Providers>
      </body>
    </html>
  );
}
