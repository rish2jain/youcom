/**
 * Interactive Element Fallbacks
 * Provides graceful degradation for interactive components
 */

import React from "react";

export interface InteractiveFallbackProps {
  children: React.ReactNode;
  fallbackType?: "basic" | "enhanced" | "full";
  className?: string;
}

/**
 * Modal fallback that works without JavaScript
 */
export function ModalFallback({
  isOpen,
  onClose,
  title,
  children,
  fallbackType = "basic",
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  fallbackType?: "basic" | "enhanced" | "full";
}) {
  if (fallbackType === "basic") {
    // Basic fallback: render content inline
    return isOpen ? (
      <div className="modal-fallback border border-gray-300 rounded-lg p-4 mb-4 bg-gray-50">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div>{children}</div>
      </div>
    ) : null;
  }

  if (fallbackType === "enhanced") {
    // Enhanced fallback: simple overlay without animations
    return isOpen ? (
      <div className="fixed inset-0 z-50 bg-black bg-opacity-50">
        <div className="flex items-center justify-center min-h-screen p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">{title}</h3>
              <button
                onClick={onClose}
                className="text-gray-500 hover:text-gray-700 text-xl"
                aria-label="Close"
              >
                ×
              </button>
            </div>
            <div>{children}</div>
          </div>
        </div>
      </div>
    ) : null;
  }

  // Full fallback: complete modal with animations
  return isOpen ? (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 transition-opacity duration-300">
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="bg-white rounded-lg max-w-md w-full p-6 transform transition-transform duration-300 scale-100">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">{title}</h3>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl transition-colors duration-200"
              aria-label="Close"
            >
              ×
            </button>
          </div>
          <div>{children}</div>
        </div>
      </div>
    </div>
  ) : null;
}

/**
 * Dropdown fallback
 */
export function DropdownFallback({
  trigger,
  children,
  isOpen,
  onToggle,
  fallbackType = "basic",
}: {
  trigger: React.ReactNode;
  children: React.ReactNode;
  isOpen: boolean;
  onToggle: () => void;
  fallbackType?: "basic" | "enhanced" | "full";
}) {
  // All hooks must be called at the top level
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (fallbackType !== "enhanced") return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        onToggle();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onToggle();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEscape);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [fallbackType, isOpen, onToggle]);

  if (fallbackType === "basic") {
    // Basic fallback: controlled when props provided, uncontrolled otherwise
    const detailsProps: any = {};
    if (isOpen !== undefined) {
      detailsProps.open = isOpen;
    }

    return (
      <details
        className="dropdown-fallback"
        {...detailsProps}
        onToggle={onToggle ? () => onToggle() : undefined}
      >
        <summary className="cursor-pointer list-none">{trigger}</summary>
        <div className="mt-2 p-2 border border-gray-200 rounded bg-white">
          {children}
        </div>
      </details>
    );
  }

  if (fallbackType === "enhanced") {
    return (
      <div className="relative dropdown-fallback" ref={dropdownRef}>
        <button
          onClick={onToggle}
          className="cursor-pointer"
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onToggle();
            }
          }}
        >
          {trigger}
        </button>
        {isOpen && (
          <div className="absolute top-full left-0 mt-1 p-2 border border-gray-200 rounded bg-white shadow-lg z-10">
            {children}
          </div>
        )}
      </div>
    );
  }

  // Full fallback: complete dropdown with animations
  return (
    <div className="relative dropdown-fallback">
      <div onClick={onToggle} className="cursor-pointer">
        {trigger}
      </div>
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 p-2 border border-gray-200 rounded bg-white shadow-lg z-10 transform transition-all duration-200 opacity-100 scale-100">
          {children}
        </div>
      )}
    </div>
  );
}

/**
 * Tooltip fallback
 */
export function TooltipFallback({
  children,
  content,
  fallbackType = "basic",
}: {
  children: React.ReactNode;
  content: string;
  fallbackType?: "basic" | "enhanced" | "full";
}) {
  const [isVisible, setIsVisible] = React.useState(false);

  if (fallbackType === "basic") {
    // Basic fallback: use title attribute
    return (
      <span title={content} className="tooltip-fallback">
        {children}
      </span>
    );
  }

  if (fallbackType === "enhanced") {
    // Enhanced fallback: accessible tooltip with keyboard support
    return (
      <div
        className="relative tooltip-fallback inline-block"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        tabIndex={0}
      >
        {children}
        {isVisible && (
          <div
            className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-sm bg-gray-800 text-white rounded whitespace-nowrap z-10"
            role="tooltip"
            aria-hidden={!isVisible}
          >
            {content}
          </div>
        )}
      </div>
    );
  }

  // Full fallback: animated tooltip
  return (
    <div
      className="relative tooltip-fallback inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      <div
        className={`absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-sm bg-gray-800 text-white rounded whitespace-nowrap z-10 transition-all duration-200 ${
          isVisible
            ? "opacity-100 translate-y-0"
            : "opacity-0 translate-y-1 pointer-events-none"
        }`}
      >
        {content}
      </div>
    </div>
  );
}

/**
 * Accordion fallback
 */
export function AccordionFallback({
  items,
  fallbackType = "basic",
}: {
  items: Array<{
    title: string;
    content: React.ReactNode;
    defaultOpen?: boolean;
  }>;
  fallbackType?: "basic" | "enhanced" | "full";
}) {
  const [openItems, setOpenItems] = React.useState<Set<number>>(
    new Set(
      items
        .map((item, index) => (item.defaultOpen ? index : -1))
        .filter((i) => i >= 0)
    )
  );

  const toggleItem = (index: number) => {
    const newOpenItems = new Set(openItems);
    if (newOpenItems.has(index)) {
      newOpenItems.delete(index);
    } else {
      newOpenItems.add(index);
    }
    setOpenItems(newOpenItems);
  };

  if (fallbackType === "basic") {
    // Basic fallback: use details/summary elements
    return (
      <div className="accordion-fallback space-y-2">
        {items.map((item, index) => (
          <details
            key={index}
            open={item.defaultOpen}
            className="border border-gray-200 rounded"
          >
            <summary className="p-3 cursor-pointer bg-gray-50 hover:bg-gray-100 list-none">
              <span className="font-medium">{item.title}</span>
            </summary>
            <div className="p-3 border-t border-gray-200">{item.content}</div>
          </details>
        ))}
      </div>
    );
  }

  if (fallbackType === "enhanced") {
    // Enhanced fallback: accessible expand/collapse
    return (
      <div className="accordion-fallback space-y-2">
        {items.map((item, index) => (
          <div key={index} className="border border-gray-200 rounded">
            <button
              id={`accordion-btn-${index}`}
              onClick={() => toggleItem(index)}
              aria-expanded={openItems.has(index)}
              aria-controls={`accordion-panel-${index}`}
              className="w-full p-3 text-left bg-gray-50 hover:bg-gray-100 font-medium"
            >
              <span className="flex justify-between items-center">
                {item.title}
                <span className="text-gray-500">
                  {openItems.has(index) ? "−" : "+"}
                </span>
              </span>
            </button>
            {openItems.has(index) && (
              <div
                id={`accordion-panel-${index}`}
                role="region"
                aria-labelledby={`accordion-btn-${index}`}
                className="p-3 border-t border-gray-200"
              >
                {item.content}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  }

  // Full fallback: animated accordion
  return (
    <div className="accordion-fallback space-y-2">
      {items.map((item, index) => (
        <div
          key={index}
          className="border border-gray-200 rounded overflow-hidden"
        >
          <button
            onClick={() => toggleItem(index)}
            className="w-full p-3 text-left bg-gray-50 hover:bg-gray-100 font-medium transition-colors duration-200"
          >
            <span className="flex justify-between items-center">
              {item.title}
              <span
                className={`text-gray-500 transition-transform duration-200 ${
                  openItems.has(index) ? "rotate-180" : ""
                }`}
              >
                ▼
              </span>
            </span>
          </button>
          <div
            className={`overflow-hidden transition-all duration-300 ${
              openItems.has(index)
                ? "max-h-96 opacity-100"
                : "max-h-0 opacity-0"
            }`}
          >
            <div className="p-3 border-t border-gray-200">{item.content}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Tab fallback
 */
export function TabsFallback({
  tabs,
  defaultTab = 0,
  fallbackType = "basic",
}: {
  tabs: Array<{
    label: string;
    content: React.ReactNode;
  }>;
  defaultTab?: number;
  fallbackType?: "basic" | "enhanced" | "full";
}) {
  const [activeTab, setActiveTab] = React.useState(defaultTab);

  if (fallbackType === "basic") {
    // Basic fallback: show all content with headings
    return (
      <div className="tabs-fallback space-y-4">
        {tabs.map((tab, index) => (
          <div key={index} className="border border-gray-200 rounded p-4">
            <h3 className="font-semibold mb-3">{tab.label}</h3>
            {tab.content}
          </div>
        ))}
      </div>
    );
  }

  // Enhanced and full fallbacks: functional tabs
  return (
    <div className="tabs-fallback">
      <div className="flex border-b border-gray-200">
        {tabs.map((tab, index) => (
          <button
            key={index}
            onClick={() => setActiveTab(index)}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors duration-200 ${
              activeTab === index
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="mt-4">{tabs[activeTab]?.content}</div>
    </div>
  );
}

/**
 * Generic interactive fallback wrapper
 */
export function InteractiveFallback({
  children,
  fallbackType = "basic",
  className = "",
}: InteractiveFallbackProps) {
  const baseClasses = "interactive-fallback";
  const typeClasses = {
    basic: "basic-interaction",
    enhanced: "enhanced-interaction",
    full: "full-interaction",
  };

  return (
    <div className={`${baseClasses} ${typeClasses[fallbackType]} ${className}`}>
      {children}
    </div>
  );
}
