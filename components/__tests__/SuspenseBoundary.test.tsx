/**
 * Tests for SuspenseBoundary components
 */

import React, { Suspense } from "react";
import { render, screen } from "@testing-library/react";
import {
  SuspenseBoundary,
  CardSuspenseBoundary,
  DashboardSuspenseBoundary,
  WidgetSuspenseBoundary,
  ListSuspenseBoundary,
} from "../SuspenseBoundary";

// Mock LoadingSkeleton component
jest.mock("../LoadingSkeleton", () => ({
  LoadingSkeleton: ({ variant, count }: { variant: string; count: number }) => (
    <div data-testid={`loading-skeleton-${variant}`} data-count={count}>
      Loading {variant} skeleton...
    </div>
  ),
}));

// Mock component that suspends
const SuspendingComponent = () => {
  throw Promise.resolve(); // Simulate suspense
};

// Mock component that renders normally
const NormalComponent = () => <div>Normal component content</div>;

describe("SuspenseBoundary", () => {
  it("renders children when not suspended", () => {
    render(
      <SuspenseBoundary>
        <NormalComponent />
      </SuspenseBoundary>
    );

    expect(screen.getByText("Normal component content")).toBeInTheDocument();
  });

  it("renders default skeleton fallback when suspended", () => {
    render(
      <SuspenseBoundary>
        <SuspendingComponent />
      </SuspenseBoundary>
    );

    expect(screen.getByTestId("loading-skeleton-card")).toBeInTheDocument();
  });

  it("renders custom fallback when provided", () => {
    const customFallback = <div>Custom loading message</div>;

    render(
      <SuspenseBoundary fallback={customFallback}>
        <SuspendingComponent />
      </SuspenseBoundary>
    );

    expect(screen.getByText("Custom loading message")).toBeInTheDocument();
    expect(
      screen.queryByTestId("loading-skeleton-card")
    ).not.toBeInTheDocument();
  });

  it("uses specified variant for skeleton", () => {
    render(
      <SuspenseBoundary variant="dashboard">
        <SuspendingComponent />
      </SuspenseBoundary>
    );

    expect(
      screen.getByTestId("loading-skeleton-dashboard")
    ).toBeInTheDocument();
  });

  it("passes count to skeleton", () => {
    render(
      <SuspenseBoundary variant="list" count={5}>
        <SuspendingComponent />
      </SuspenseBoundary>
    );

    const skeleton = screen.getByTestId("loading-skeleton-list");
    expect(skeleton).toHaveAttribute("data-count", "5");
  });

  it("applies custom className", () => {
    render(
      <SuspenseBoundary className="custom-class">
        <SuspendingComponent />
      </SuspenseBoundary>
    );

    const container = screen.getByTestId("loading-skeleton-card").parentElement;
    expect(container).toHaveClass("custom-class");
  });
});

describe("CardSuspenseBoundary", () => {
  it("renders card variant skeleton", () => {
    render(
      <CardSuspenseBoundary>
        <SuspendingComponent />
      </CardSuspenseBoundary>
    );

    expect(screen.getByTestId("loading-skeleton-card")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(
      <CardSuspenseBoundary className="card-class">
        <SuspendingComponent />
      </CardSuspenseBoundary>
    );

    const container = screen.getByTestId("loading-skeleton-card").parentElement;
    expect(container).toHaveClass("card-class");
  });

  it("renders children when not suspended", () => {
    render(
      <CardSuspenseBoundary>
        <NormalComponent />
      </CardSuspenseBoundary>
    );

    expect(screen.getByText("Normal component content")).toBeInTheDocument();
  });
});

describe("DashboardSuspenseBoundary", () => {
  it("renders dashboard variant skeleton", () => {
    render(
      <DashboardSuspenseBoundary>
        <SuspendingComponent />
      </DashboardSuspenseBoundary>
    );

    expect(
      screen.getByTestId("loading-skeleton-dashboard")
    ).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(
      <DashboardSuspenseBoundary className="dashboard-class">
        <SuspendingComponent />
      </DashboardSuspenseBoundary>
    );

    const container = screen.getByTestId(
      "loading-skeleton-dashboard"
    ).parentElement;
    expect(container).toHaveClass("dashboard-class");
  });
});

describe("WidgetSuspenseBoundary", () => {
  it("renders widget variant skeleton", () => {
    render(
      <WidgetSuspenseBoundary>
        <SuspendingComponent />
      </WidgetSuspenseBoundary>
    );

    expect(screen.getByTestId("loading-skeleton-widget")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(
      <WidgetSuspenseBoundary className="widget-class">
        <SuspendingComponent />
      </WidgetSuspenseBoundary>
    );

    const container = screen.getByTestId(
      "loading-skeleton-widget"
    ).parentElement;
    expect(container).toHaveClass("widget-class");
  });
});

describe("ListSuspenseBoundary", () => {
  it("renders list variant skeleton with default count", () => {
    render(
      <ListSuspenseBoundary>
        <SuspendingComponent />
      </ListSuspenseBoundary>
    );

    const skeleton = screen.getByTestId("loading-skeleton-list");
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveAttribute("data-count", "3");
  });

  it("renders list variant skeleton with custom count", () => {
    render(
      <ListSuspenseBoundary count={7}>
        <SuspendingComponent />
      </ListSuspenseBoundary>
    );

    const skeleton = screen.getByTestId("loading-skeleton-list");
    expect(skeleton).toHaveAttribute("data-count", "7");
  });

  it("applies custom className", () => {
    render(
      <ListSuspenseBoundary className="list-class">
        <SuspendingComponent />
      </ListSuspenseBoundary>
    );

    const container = screen.getByTestId("loading-skeleton-list").parentElement;
    expect(container).toHaveClass("list-class");
  });
});

describe("Suspense Integration", () => {
  it("works with React Suspense", () => {
    render(
      <Suspense fallback={<div>React Suspense fallback</div>}>
        <SuspenseBoundary>
          <NormalComponent />
        </SuspenseBoundary>
      </Suspense>
    );

    expect(screen.getByText("Normal component content")).toBeInTheDocument();
  });

  it("nested suspense boundaries work correctly", () => {
    render(
      <SuspenseBoundary variant="dashboard">
        <SuspenseBoundary variant="card">
          <NormalComponent />
        </SuspenseBoundary>
      </SuspenseBoundary>
    );

    expect(screen.getByText("Normal component content")).toBeInTheDocument();
  });
});
