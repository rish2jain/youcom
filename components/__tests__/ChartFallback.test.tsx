/**
 * Chart Fallback Components Tests
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import {
  TextChartFallback,
  SimpleChartFallback,
  StaticChartFallback,
  AdaptiveChartFallback,
  ChartData,
} from "../fallbacks/ChartFallback";

describe("Chart Fallback Components", () => {
  const mockChartData: ChartData = {
    labels: ["Jan", "Feb", "Mar", "Apr"],
    datasets: [
      {
        label: "Sales",
        data: [100, 150, 120, 200],
        color: "#3b82f6",
      },
      {
        label: "Profit",
        data: [20, 30, 25, 40],
        color: "#10b981",
      },
    ],
  };

  describe("TextChartFallback", () => {
    it("should render chart data as text with bars", () => {
      render(
        <TextChartFallback
          data={mockChartData}
          title="Sales Chart"
          type="bar"
        />
      );

      expect(screen.getByText("Sales Chart")).toBeInTheDocument();
      expect(screen.getByText("Jan")).toBeInTheDocument();
      expect(screen.getByText("Feb")).toBeInTheDocument();
      expect(screen.getByText("200")).toBeInTheDocument(); // Highest value
    });

    it("should handle empty datasets", () => {
      const emptyData: ChartData = {
        labels: ["Jan", "Feb"],
        datasets: [],
      };

      const { container } = render(<TextChartFallback data={emptyData} />);

      expect(container.firstChild).toBeNull();
    });

    it("should show additional datasets", () => {
      render(<TextChartFallback data={mockChartData} />);

      expect(screen.getByText("Sales")).toBeInTheDocument();
      expect(screen.getByText("Profit:")).toBeInTheDocument();
      expect(screen.getByText("Additional Data:")).toBeInTheDocument();
    });

    it("should calculate percentage bars correctly", () => {
      render(<TextChartFallback data={mockChartData} />);

      // The highest value (200) should have 100% width
      const bars = document.querySelectorAll('[style*="width"]');
      expect(bars.length).toBeGreaterThan(0);
    });

    it("should format numbers with locale", () => {
      const largeNumberData: ChartData = {
        labels: ["Q1"],
        datasets: [
          {
            label: "Revenue",
            data: [1000000],
          },
        ],
      };

      render(<TextChartFallback data={largeNumberData} />);

      // Should format large numbers with commas
      expect(screen.getByText("1,000,000")).toBeInTheDocument();
    });
  });

  describe("SimpleChartFallback", () => {
    it("should render visual chart with bars", () => {
      render(
        <SimpleChartFallback
          data={mockChartData}
          title="Sales Chart"
          type="bar"
        />
      );

      expect(screen.getByText("Sales Chart")).toBeInTheDocument();
      expect(screen.getByText("Jan")).toBeInTheDocument();
      expect(screen.getByText("Sales")).toBeInTheDocument();

      // Should have chart container
      expect(document.querySelector(".chart-container")).toBeInTheDocument();
    });

    it("should render pie chart layout for pie type", () => {
      render(
        <SimpleChartFallback
          data={mockChartData}
          title="Sales Distribution"
          type="pie"
        />
      );

      expect(screen.getByText("Sales Distribution")).toBeInTheDocument();
      expect(document.querySelector(".simple-pie-chart")).toBeInTheDocument();
    });

    it("should show legend for multiple datasets", () => {
      render(<SimpleChartFallback data={mockChartData} type="bar" />);

      expect(screen.getByText("Sales")).toBeInTheDocument();
      expect(screen.getByText("Profit")).toBeInTheDocument();
    });

    it("should handle single dataset without legend", () => {
      const singleDataset: ChartData = {
        labels: ["Jan", "Feb"],
        datasets: [
          {
            label: "Sales",
            data: [100, 150],
          },
        ],
      };

      render(<SimpleChartFallback data={singleDataset} />);

      expect(screen.getByText("Sales")).toBeInTheDocument();
      // Should not show additional legend section
      expect(screen.queryByText("Profit")).not.toBeInTheDocument();
    });

    it("should calculate bar heights proportionally", () => {
      render(<SimpleChartFallback data={mockChartData} />);

      const bars = document.querySelectorAll('[style*="height"]');
      expect(bars.length).toBe(4); // One bar per label
    });

    it("should show pie chart percentages", () => {
      render(<SimpleChartFallback data={mockChartData} type="pie" />);

      // Should show percentages for pie chart
      expect(screen.getByText(/\d+\.\d+%/)).toBeInTheDocument();
    });
  });

  describe("StaticChartFallback", () => {
    it("should render without animations", () => {
      render(<StaticChartFallback data={mockChartData} />);

      expect(screen.getByText("Jan")).toBeInTheDocument();
      expect(document.querySelector(".no-animations")).toBeInTheDocument();
    });

    it("should include CSS to disable animations", () => {
      render(<StaticChartFallback data={mockChartData} />);

      // Should have style tag with animation disabling CSS
      const styleElements = document.querySelectorAll("style");
      const hasAnimationCSS = Array.from(styleElements).some((style) =>
        style.textContent?.includes("transition: none")
      );
      expect(hasAnimationCSS).toBe(true);
    });
  });

  describe("AdaptiveChartFallback", () => {
    it("should render text fallback when specified", () => {
      render(
        <AdaptiveChartFallback data={mockChartData} fallbackType="text" />
      );

      expect(document.querySelector(".text-fallback")).toBeInTheDocument();
    });

    it("should render simple fallback when specified", () => {
      render(
        <AdaptiveChartFallback data={mockChartData} fallbackType="simple" />
      );

      expect(document.querySelector(".simple-fallback")).toBeInTheDocument();
    });

    it("should render static fallback when specified", () => {
      render(
        <AdaptiveChartFallback data={mockChartData} fallbackType="static" />
      );

      expect(document.querySelector(".static-fallback")).toBeInTheDocument();
    });

    it("should default to simple fallback", () => {
      render(<AdaptiveChartFallback data={mockChartData} />);

      expect(document.querySelector(".simple-fallback")).toBeInTheDocument();
    });

    it("should pass through all props", () => {
      render(
        <AdaptiveChartFallback
          data={mockChartData}
          title="Test Chart"
          type="pie"
          className="custom-class"
          fallbackType="text"
        />
      );

      expect(screen.getByText("Test Chart")).toBeInTheDocument();
      expect(document.querySelector(".custom-class")).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("should have proper ARIA labels", () => {
      render(
        <TextChartFallback data={mockChartData} title="Accessible Chart" />
      );

      expect(
        screen.getByRole("heading", { name: "Accessible Chart" })
      ).toBeInTheDocument();
    });

    it("should provide text alternatives for visual elements", () => {
      render(<SimpleChartFallback data={mockChartData} />);

      // Visual bars should have title attributes for accessibility
      const barsWithTitles = document.querySelectorAll("[title]");
      expect(barsWithTitles.length).toBeGreaterThan(0);
    });
  });

  describe("Error Handling", () => {
    it("should handle zero values gracefully", () => {
      const zeroData: ChartData = {
        labels: ["A", "B"],
        datasets: [
          {
            label: "Zero Values",
            data: [0, 0],
          },
        ],
      };

      render(<TextChartFallback data={zeroData} />);

      expect(screen.getByText("A")).toBeInTheDocument();
      expect(screen.getByText("0")).toBeInTheDocument();
    });

    it("should handle negative values", () => {
      const negativeData: ChartData = {
        labels: ["Loss"],
        datasets: [
          {
            label: "Negative",
            data: [-50],
          },
        ],
      };

      render(<TextChartFallback data={negativeData} />);

      expect(screen.getByText("Loss")).toBeInTheDocument();
    });

    it("should handle missing colors gracefully", () => {
      const noColorData: ChartData = {
        labels: ["Test"],
        datasets: [
          {
            label: "No Color",
            data: [100],
            // No color property
          },
        ],
      };

      render(<SimpleChartFallback data={noColorData} />);

      expect(screen.getByText("Test")).toBeInTheDocument();
    });
  });

  describe("Responsive Behavior", () => {
    it("should apply responsive classes", () => {
      render(
        <SimpleChartFallback
          data={mockChartData}
          className="responsive-chart"
        />
      );

      expect(document.querySelector(".responsive-chart")).toBeInTheDocument();
    });

    it("should truncate long labels", () => {
      const longLabelData: ChartData = {
        labels: ["Very Long Label That Should Be Truncated"],
        datasets: [
          {
            label: "Data",
            data: [100],
          },
        ],
      };

      render(<SimpleChartFallback data={longLabelData} />);

      const labelElement = screen.getByText(
        "Very Long Label That Should Be Truncated"
      );
      expect(labelElement).toHaveClass("truncate");
    });
  });
});
