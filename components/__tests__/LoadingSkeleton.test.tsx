import { render, screen } from "@testing-library/react";
import {
  ImpactCardSkeleton,
  WatchListSkeleton,
  MetricCardSkeleton,
} from "../LoadingSkeleton";

describe("ImpactCardSkeleton Component", () => {
  it("renders impact card skeleton", () => {
    const { container } = render(<ImpactCardSkeleton />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("has pulse animation class", () => {
    const { container } = render(<ImpactCardSkeleton />);
    const skeleton = container.querySelector(".animate-pulse");
    expect(skeleton).toBeInTheDocument();
  });

  it("renders with white background", () => {
    const { container } = render(<ImpactCardSkeleton />);
    const skeleton = container.querySelector(".bg-white");
    expect(skeleton).toBeInTheDocument();
  });

  it("renders header elements", () => {
    const { container } = render(<ImpactCardSkeleton />);

    // Avatar/icon placeholder
    const avatar = container.querySelector(".w-12.h-12.bg-gray-200");
    expect(avatar).toBeInTheDocument();

    // Title and subtitle placeholders
    const placeholders = container.querySelectorAll(".bg-gray-200");
    expect(placeholders.length).toBeGreaterThan(0);
  });

  it("renders content lines", () => {
    const { container } = render(<ImpactCardSkeleton />);

    // Should have multiple content line placeholders
    const contentLines = container.querySelectorAll(".h-4.bg-gray-200");
    expect(contentLines.length).toBeGreaterThan(2);
  });

  it("renders action button placeholders", () => {
    const { container } = render(<ImpactCardSkeleton />);

    // Button placeholders
    const buttons = container.querySelectorAll(".h-8.bg-gray-200");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("has proper shadow and rounded corners", () => {
    const { container } = render(<ImpactCardSkeleton />);
    const skeleton = container.querySelector(".shadow-sm.rounded-lg");
    expect(skeleton).toBeInTheDocument();
  });
});

describe("WatchListSkeleton Component", () => {
  it("renders watchlist skeleton", () => {
    const { container } = render(<WatchListSkeleton />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("renders three skeleton items", () => {
    const { container } = render(<WatchListSkeleton />);

    const items = container.querySelectorAll(".bg-white.p-4.rounded-lg");
    expect(items).toHaveLength(3);
  });

  it("each item has pulse animation", () => {
    const { container } = render(<WatchListSkeleton />);

    const animatedItems = container.querySelectorAll(".animate-pulse");
    expect(animatedItems.length).toBeGreaterThan(0);
  });

  it("renders title and description placeholders for each item", () => {
    const { container } = render(<WatchListSkeleton />);

    // Each item should have title (h-5) and description (h-3) placeholders
    const titles = container.querySelectorAll(".h-5.bg-gray-200");
    const descriptions = container.querySelectorAll(".h-3.bg-gray-200");

    expect(titles.length).toBeGreaterThan(0);
    expect(descriptions.length).toBeGreaterThan(0);
  });

  it("renders action button placeholders", () => {
    const { container } = render(<WatchListSkeleton />);

    // Action buttons (10x10)
    const buttons = container.querySelectorAll(".w-10.h-10.bg-gray-200");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("has proper layout structure", () => {
    const { container } = render(<WatchListSkeleton />);

    // Should have flex layout
    const flexContainers = container.querySelectorAll(".flex.items-center");
    expect(flexContainers.length).toBeGreaterThan(0);
  });
});

describe("MetricCardSkeleton Component", () => {
  it("renders metric card skeleton", () => {
    const { container } = render(<MetricCardSkeleton />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("has pulse animation class", () => {
    const { container } = render(<MetricCardSkeleton />);
    const skeleton = container.querySelector(".animate-pulse");
    expect(skeleton).toBeInTheDocument();
  });

  it("renders with white background", () => {
    const { container } = render(<MetricCardSkeleton />);
    const skeleton = container.querySelector(".bg-white");
    expect(skeleton).toBeInTheDocument();
  });

  it("renders value placeholder", () => {
    const { container } = render(<MetricCardSkeleton />);

    // Large value placeholder (h-8)
    const value = container.querySelector(".h-8.bg-gray-200");
    expect(value).toBeInTheDocument();
  });

  it("renders title and subtitle placeholders", () => {
    const { container } = render(<MetricCardSkeleton />);

    // Title (h-4) and subtitle (h-3) placeholders
    const title = container.querySelector(".h-4.bg-gray-200");
    const subtitle = container.querySelector(".h-3.bg-gray-200");

    expect(title).toBeInTheDocument();
    expect(subtitle).toBeInTheDocument();
  });

  it("has proper padding and shadow", () => {
    const { container } = render(<MetricCardSkeleton />);
    const skeleton = container.querySelector(".p-6.shadow-sm");
    expect(skeleton).toBeInTheDocument();
  });

  it("has rounded corners", () => {
    const { container } = render(<MetricCardSkeleton />);
    const skeleton = container.querySelector(".rounded-lg");
    expect(skeleton).toBeInTheDocument();
  });
});

describe("Loading Skeleton Accessibility", () => {
  it("impact card skeleton has appropriate structure", () => {
    const { container } = render(<ImpactCardSkeleton />);

    // Should not have role="progressbar" as it's a static skeleton
    const progressbar = container.querySelector('[role="progressbar"]');
    expect(progressbar).not.toBeInTheDocument();
  });

  it("watchlist skeleton is not focusable", () => {
    const { container } = render(<WatchListSkeleton />);

    const focusableElements = container.querySelectorAll('[tabindex]');
    expect(focusableElements).toHaveLength(0);
  });

  it("metric card skeleton has no interactive elements", () => {
    const { container } = render(<MetricCardSkeleton />);

    const buttons = container.querySelectorAll("button");
    const links = container.querySelectorAll("a");

    expect(buttons).toHaveLength(0);
    expect(links).toHaveLength(0);
  });
});

describe("Loading Skeleton Visual Consistency", () => {
  it("all skeletons use gray-200 for placeholders", () => {
    const { container: impactContainer } = render(<ImpactCardSkeleton />);
    const { container: watchContainer } = render(<WatchListSkeleton />);
    const { container: metricContainer } = render(<MetricCardSkeleton />);

    const impactPlaceholders = impactContainer.querySelectorAll(".bg-gray-200");
    const watchPlaceholders = watchContainer.querySelectorAll(".bg-gray-200");
    const metricPlaceholders = metricContainer.querySelectorAll(".bg-gray-200");

    expect(impactPlaceholders.length).toBeGreaterThan(0);
    expect(watchPlaceholders.length).toBeGreaterThan(0);
    expect(metricPlaceholders.length).toBeGreaterThan(0);
  });

  it("all skeletons have animate-pulse class", () => {
    const { container: impactContainer } = render(<ImpactCardSkeleton />);
    const { container: watchContainer } = render(<WatchListSkeleton />);
    const { container: metricContainer } = render(<MetricCardSkeleton />);

    expect(impactContainer.querySelector(".animate-pulse")).toBeInTheDocument();
    expect(watchContainer.querySelector(".animate-pulse")).toBeInTheDocument();
    expect(metricContainer.querySelector(".animate-pulse")).toBeInTheDocument();
  });
});
