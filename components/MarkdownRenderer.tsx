"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import { ExternalLink, Copy, Check } from "lucide-react";
import "highlight.js/styles/github.css";

interface MarkdownRendererProps {
  content: string | any;
  className?: string;
  maxHeight?: string;
  showCopyButton?: boolean;
}

export function MarkdownRenderer({
  content,
  className = "",
  maxHeight = "max-h-96",
  showCopyButton = true,
}: MarkdownRendererProps) {
  const [copied, setCopied] = useState(false);

  // Process content to ensure it's a string
  const processContent = (content: any): string => {
    if (typeof content === "string") {
      return content;
    } else if (Array.isArray(content) && content.length > 0) {
      // Handle array format from Express Agent
      return content
        .map((item) => item.text || item.content || JSON.stringify(item))
        .join("\n\n");
    } else if (typeof content === "object" && content !== null) {
      // Handle object format
      if (content.report) {
        return processContent(content.report);
      }
      return JSON.stringify(content, null, 2);
    }
    return String(content || "No content available");
  };

  const markdownContent = processContent(content);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(markdownContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  return (
    <div className={`relative ${className}`}>
      {showCopyButton && (
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 z-10 p-2 bg-white/90 hover:bg-white border border-gray-200 rounded-lg shadow-sm transition-all duration-200 flex items-center space-x-1 text-sm"
          title="Copy content"
        >
          {copied ? (
            <>
              <Check className="w-4 h-4 text-green-600" />
              <span className="text-green-600">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-4 h-4 text-gray-600" />
              <span className="text-gray-600">Copy</span>
            </>
          )}
        </button>
      )}

      <div
        className={`${maxHeight} overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 pr-2`}
      >
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight, rehypeRaw]}
            components={{
              // Custom link component with external link icon
              a: ({ href, children, ...props }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700 underline inline-flex items-center gap-1"
                  {...props}
                >
                  {children}
                  <ExternalLink className="w-3 h-3" />
                </a>
              ),
              // Custom heading components with better spacing
              h1: ({ children, ...props }) => (
                <h1
                  className="text-xl font-bold text-gray-900 mt-6 mb-4 first:mt-0"
                  {...props}
                >
                  {children}
                </h1>
              ),
              h2: ({ children, ...props }) => (
                <h2
                  className="text-lg font-semibold text-gray-900 mt-5 mb-3 first:mt-0"
                  {...props}
                >
                  {children}
                </h2>
              ),
              h3: ({ children, ...props }) => (
                <h3
                  className="text-base font-semibold text-gray-900 mt-4 mb-2 first:mt-0"
                  {...props}
                >
                  {children}
                </h3>
              ),
              // Custom list components
              ul: ({ children, ...props }) => (
                <ul className="list-disc list-inside space-y-1 my-3" {...props}>
                  {children}
                </ul>
              ),
              ol: ({ children, ...props }) => (
                <ol
                  className="list-decimal list-inside space-y-1 my-3"
                  {...props}
                >
                  {children}
                </ol>
              ),
              // Custom paragraph with better spacing
              p: ({ children, ...props }) => (
                <p
                  className="text-gray-700 leading-relaxed my-3 first:mt-0 last:mb-0"
                  {...props}
                >
                  {children}
                </p>
              ),
              // Custom blockquote
              blockquote: ({ children, ...props }) => (
                <blockquote
                  className="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-50 text-gray-700 italic"
                  {...props}
                >
                  {children}
                </blockquote>
              ),
              // Custom code block
              pre: ({ children, ...props }) => (
                <pre
                  className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4 text-sm"
                  {...props}
                >
                  {children}
                </pre>
              ),
              // Custom table styling
              table: ({ children, ...props }) => (
                <div className="overflow-x-auto my-4">
                  <table
                    className="min-w-full border border-gray-200 rounded-lg"
                    {...props}
                  >
                    {children}
                  </table>
                </div>
              ),
              th: ({ children, ...props }) => (
                <th
                  className="bg-gray-50 border-b border-gray-200 px-4 py-2 text-left font-semibold text-gray-900"
                  {...props}
                >
                  {children}
                </th>
              ),
              td: ({ children, ...props }) => (
                <td
                  className="border-b border-gray-200 px-4 py-2 text-gray-700"
                  {...props}
                >
                  {children}
                </td>
              ),
            }}
          >
            {markdownContent}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export default MarkdownRenderer;
