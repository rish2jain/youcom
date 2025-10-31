import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link";
  size?: "default" | "sm" | "lg" | "icon";
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "default",
      size = "default",
      className = "",
      children,
      ...props
    },
    ref
  ) => {
    const getVariantClasses = () => {
      switch (variant) {
        case "destructive":
          return "bg-red-600 text-white hover:bg-red-700";
        case "outline":
          return "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50";
        case "secondary":
          return "bg-gray-100 text-gray-900 hover:bg-gray-200";
        case "ghost":
          return "text-gray-700 hover:bg-gray-100";
        case "link":
          return "text-blue-600 underline-offset-4 hover:underline";
        default:
          return "bg-blue-600 text-white hover:bg-blue-700";
      }
    };

    const getSizeClasses = () => {
      switch (size) {
        case "sm":
          return "h-8 px-3 text-sm";
        case "lg":
          return "h-12 px-8 text-lg";
        case "icon":
          return "h-10 w-10";
        default:
          return "h-10 px-4 py-2";
      }
    };

    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50 ${getVariantClasses()} ${getSizeClasses()} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
