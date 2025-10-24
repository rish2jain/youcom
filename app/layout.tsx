import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Enterprise CIA - Competitive Intelligence Agent",
  description: "AI-powered competitive intelligence using You.com APIs",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <Providers>
          <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
            <header className="bg-white shadow-sm border-b">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center py-4">
                  <div className="flex items-center space-x-4">
                    <h1 className="text-2xl font-bold text-gray-900">
                      Enterprise CIA
                    </h1>
                    <div className="you-api-badge">Powered by You.com APIs</div>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <span>News</span>
                    <span>•</span>
                    <span>Search</span>
                    <span>•</span>
                    <span>Chat</span>
                    <span>•</span>
                    <span>ARI</span>
                  </div>
                </div>
              </div>
            </header>
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
