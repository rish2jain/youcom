"use client";

import React, { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Loader2, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useUserContext } from "@/contexts/UserContext";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatCommand {
  intent: "research" | "alert" | "monitor" | "general";
  company?: string;
  topic?: string;
}

export const FloatingChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "👋 Hi! I'm your competitive intelligence assistant. Try asking me:\n\n• **Research [company]** - Get detailed competitor analysis\n• **Alert me about [topic]** - Set up monitoring\n• **Show competitors in [industry]** - Industry insights",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { userContext } = useUserContext();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const parseCommand = (text: string): ChatCommand => {
    const lowerText = text.toLowerCase();

    // Research intent
    if (
      lowerText.includes("research") ||
      lowerText.includes("analyze") ||
      lowerText.includes("tell me about")
    ) {
      const company = extractCompanyName(text);
      return { intent: "research", company };
    }

    // Alert intent
    if (
      lowerText.includes("alert") ||
      lowerText.includes("notify") ||
      lowerText.includes("watch")
    ) {
      const topic = extractTopic(text);
      return { intent: "alert", topic };
    }

    // Monitor intent
    if (
      lowerText.includes("monitor") ||
      lowerText.includes("track") ||
      lowerText.includes("competitors in")
    ) {
      const topic = extractTopic(text) || userContext.industry;
      return { intent: "monitor", topic };
    }

    return { intent: "general" };
  };

  const extractCompanyName = (text: string): string | undefined => {
    // Simple extraction - in production, use NLP
    const patterns = [
      /research\s+([a-z0-9\s]+?)(?:\s|$)/i,
      /analyze\s+([a-z0-9\s]+?)(?:\s|$)/i,
      /about\s+([a-z0-9\s]+?)(?:\s|$)/i,
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        return match[1].trim();
      }
    }
    return undefined;
  };

  const extractTopic = (text: string): string | undefined => {
    // Simple extraction - in production, use NLP
    const patterns = [/about\s+([a-z0-9\s]+?)(?:\s|$)/i, /in\s+([a-z0-9\s]+?)(?:\s|$)/i];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        return match[1].trim();
      }
    }
    return undefined;
  };

  const handleCommand = async (command: ChatCommand, userMessage: string) => {
    let assistantResponse = "";

    switch (command.intent) {
      case "research":
        if (command.company) {
          assistantResponse = `🔍 Great! I'll research **${command.company}** for you. Analyzing 400+ sources using You.com ARI API...\n\nNavigating to the research page now.`;
          setTimeout(() => {
            router.push(`/research?company=${encodeURIComponent(command.company!)}`);
          }, 1500);
        } else {
          assistantResponse =
            "I'd love to help you research a company! Please specify which company you'd like to analyze. For example: **Research OpenAI**";
        }
        break;

      case "alert":
        assistantResponse = `🚨 Setting up alert for **${command.topic || "updates"}**. I'll notify you when there are significant developments.\n\nYou can manage your alerts in the Monitoring section.`;
        setTimeout(() => {
          router.push("/monitoring");
        }, 1500);
        break;

      case "monitor":
        assistantResponse = `👀 I'll show you competitors in **${command.topic || userContext.industry}**. Taking you to the monitoring dashboard where you can add them to your watchlist.`;
        setTimeout(() => {
          router.push("/monitoring");
        }, 1500);
        break;

      default:
        // Use You.com Chat API for general questions
        assistantResponse = await callChatAPI(userMessage);
        break;
    }

    return assistantResponse;
  };

  const callChatAPI = async (query: string): Promise<string> => {
    try {
      // Backend handles You.com Chat API calls with proper context
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          context: userContext,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend API error: ${response.statusText}`);
      }

      const data = await response.json();
      return data.answer || data.message || "I received your question but couldn't generate a response.";
    } catch (error) {
      console.error("Chat API error:", error);

      // Provide helpful error message
      const errorMessage = error instanceof Error ? error.message : "Unknown error";

      if (errorMessage.includes("Failed to fetch") || errorMessage.includes("Backend API error")) {
        return `⚠️ **Backend server unavailable**\n\nPlease ensure the FastAPI backend is running at \`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765"}\`\n\nYou can still use specific commands:\n• **Research [company]** - Deep analysis\n• **Alert me about [topic]** - Set up monitoring\n• **Show competitors in [industry]** - Industry insights`;
      }

      return "I encountered an error. Please try again or use specific commands like **Research [company]**.";
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const command = parseCommand(input);
      const response = await handleCommand(command, input);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I encountered an error. Please try again or rephrase your question.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full p-4 shadow-2xl hover:shadow-blue-500/50 transition-all hover:scale-110 group"
          aria-label="Open chat"
        >
          <MessageCircle className="w-6 h-6" />
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            Ask me anything! 💬
          </div>
        </button>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-96 h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-200">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 text-white flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold">CIA Assistant</h3>
                <p className="text-xs text-blue-100">Powered by You.com Chat API</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-white/20 rounded-lg p-1 transition-colors"
              aria-label="Close chat"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-white border border-gray-200 text-gray-900"
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                  <div
                    className={`text-xs mt-1 ${
                      message.role === "user" ? "text-blue-100" : "text-gray-400"
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 bg-white border-t border-gray-200">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything..."
                className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none transition-all text-gray-900"
                disabled={isLoading}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="bg-blue-600 text-white px-4 py-3 rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all"
                aria-label="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Try: "Research OpenAI" or "Alert me about AI models"
            </p>
          </div>
        </div>
      )}
    </>
  );
};
