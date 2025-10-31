import React from "react";
import { useState } from "react";
import Link from "next/link";
import {
  HomeIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  BoltIcon,
  ChartPieIcon,
  Cog6ToothIcon,
  AdjustmentsHorizontalIcon,
  Bars3Icon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  badge?: string;
  description: string;
}

interface SidebarProps {
  activeItem: string;
  onItemClick: (itemId: string) => void;
  collapsed?: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  activeItem,
  onItemClick,
  collapsed = false,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(collapsed);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const sidebarItems: SidebarItem[] = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: ChartPieIcon,
      href: "/",
      description: "Intelligence hub & alerts",
    },
    {
      id: "demo",
      label: "Demo",
      icon: HomeIcon,
      href: "/demo",
      description: "4-API orchestration showcase",
    },
    {
      id: "research",
      label: "Research",
      icon: MagnifyingGlassIcon,
      href: "/research",
      description: "Individual company analysis",
    },
    {
      id: "monitoring",
      label: "Monitoring",
      icon: BoltIcon,
      href: "/monitoring",
      badge: "3",
      description: "Real-time competitive tracking",
    },
    {
      id: "analytics",
      label: "Analytics",
      icon: ChartPieIcon,
      href: "/analytics",
      description: "Trends and predictions",
    },
    {
      id: "integrations",
      label: "Integrations",
      icon: Cog6ToothIcon,
      href: "/integrations",
      description: "Connect your tools",
    },
    {
      id: "settings",
      label: "Settings",
      icon: AdjustmentsHorizontalIcon,
      href: "/settings",
      description: "Preferences and playbooks",
    },
  ];

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <h2 className="text-lg font-semibold text-gray-900">Navigation</h2>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors hidden lg:block"
          >
            <Bars3Icon className="w-5 h-5 text-gray-500" />
          </button>
          <button
            onClick={() => setIsMobileOpen(false)}
            className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors lg:hidden"
          >
            <XMarkIcon className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 p-4 space-y-2">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeItem === item.id;

          return (
            <Link
              key={item.id}
              href={item.href}
              onClick={() => setIsMobileOpen(false)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-left ${
                isActive
                  ? "bg-blue-600 text-white shadow-lg transform scale-105 border border-blue-700"
                  : "text-gray-700 hover:bg-gray-50 hover:text-gray-900 hover:shadow-sm"
              }`}
              title={isCollapsed ? item.label : undefined}
            >
              <div className="relative">
                <Icon
                  className={`w-5 h-5 ${
                    isActive ? "text-white" : "text-gray-500"
                  }`}
                />
                {item.badge && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center animate-pulse shadow-lg">
                    {item.badge}
                  </span>
                )}
              </div>

              {!isCollapsed && (
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-medium truncate">{item.label}</span>
                  </div>
                  <p className="text-xs text-gray-500 truncate">
                    {item.description}
                  </p>
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Sidebar Footer */}
      {!isCollapsed && (
        <div className="p-4 border-t border-gray-200">
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm font-medium text-gray-900">
                APIs Connected
              </span>
            </div>
            <p className="text-xs text-gray-600">
              All You.com APIs operational
            </p>
            <button className="text-xs text-blue-600 hover:text-blue-700 mt-1">
              View status →
            </button>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <div
        className={`hidden lg:flex flex-col bg-white border-r border-gray-200 transition-all duration-300 ${
          isCollapsed ? "w-16" : "w-64"
        }`}
      >
        <SidebarContent />
      </div>

      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-40 p-2 bg-white rounded-lg shadow-md border border-gray-200"
      >
        <Bars3Icon className="w-6 h-6 text-gray-600" />
      </button>

      {/* Mobile Sidebar Overlay */}
      {isMobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black bg-opacity-50"
            onClick={() => setIsMobileOpen(false)}
          />

          {/* Sidebar */}
          <div className="relative w-64 bg-white shadow-xl">
            <SidebarContent />
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar;
