"use client";

interface PulseAnimationProps {
  children: React.ReactNode;
  isActive: boolean;
  color?: "blue" | "green" | "purple" | "orange";
}

export function PulseAnimation({ children, isActive, color = "blue" }: PulseAnimationProps) {
  const colorClasses = {
    blue: "ring-blue-400",
    green: "ring-green-400",
    purple: "ring-purple-400",
    orange: "ring-orange-400",
  };

  return (
    <div className={`relative ${isActive ? "animate-pulse-ring" : ""}`}>
      {isActive && (
        <>
          <div className={`absolute inset-0 rounded-lg ${colorClasses[color]} ring-4 opacity-75 animate-ping`}></div>
          <div className={`absolute inset-0 rounded-lg ${colorClasses[color]} ring-4 opacity-50`}></div>
        </>
      )}
      <div className="relative">{children}</div>
    </div>
  );
}

// Add to tailwind.config.js:
/*
theme: {
  extend: {
    keyframes: {
      'pulse-ring': {
        '0%': { transform: 'scale(1)', opacity: '1' },
        '50%': { transform: 'scale(1.05)', opacity: '0.7' },
        '100%': { transform: 'scale(1)', opacity: '1' },
      }
    },
    animation: {
      'pulse-ring': 'pulse-ring 2s ease-in-out infinite',
    }
  }
}
*/
