"use client";

import { IntegrationManager } from "@/components/IntegrationManager";

export default function IntegrationsPage() {
  return (
    <div className="space-y-8">
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Integration Management
        </h1>
        <p className="text-gray-600 mb-4">
          Connect your favorite tools to sync competitive intelligence data
          automatically.
        </p>
      </div>
      <IntegrationManager />
    </div>
  );
}
