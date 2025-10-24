import { render, screen } from "@testing-library/react";
import { PulseAnimation } from "../PulseAnimation";

describe("PulseAnimation Component", () => {
  it("renders children correctly", () => {
    render(
      <PulseAnimation isActive={false}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("does not show animation when isActive is false", () => {
    const { container } = render(
      <PulseAnimation isActive={false}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    const animatedElement = container.querySelector(".animate-pulse-ring");
    expect(animatedElement).not.toBeInTheDocument();
  });

  it("shows animation when isActive is true", () => {
    const { container } = render(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    const animatedElement = container.querySelector(".animate-pulse-ring");
    expect(animatedElement).toBeInTheDocument();
  });

  it("renders ring layers when active", () => {
    const { container } = render(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    // Should have two ring layers (ping and static)
    const ringLayers = container.querySelectorAll(".ring-4");
    expect(ringLayers.length).toBe(2);
  });

  it("applies ping animation to first ring layer", () => {
    const { container } = render(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    const pingRing = container.querySelector(".animate-ping");
    expect(pingRing).toBeInTheDocument();
  });

  it("uses default blue color when color prop is not provided", () => {
    const { container } = render(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    const blueRing = container.querySelector(".ring-blue-400");
    expect(blueRing).toBeInTheDocument();
  });

  it("applies green color when specified", () => {
    const { container } = render(
      <PulseAnimation isActive={true} color="green">
        <div>Test Content</div>
      </PulseAnimation>
    );

    const greenRings = container.querySelectorAll(".ring-green-400");
    expect(greenRings.length).toBeGreaterThan(0);
  });

  it("applies purple color when specified", () => {
    const { container } = render(
      <PulseAnimation isActive={true} color="purple">
        <div>Test Content</div>
      </PulseAnimation>
    );

    const purpleRings = container.querySelectorAll(".ring-purple-400");
    expect(purpleRings.length).toBeGreaterThan(0);
  });

  it("applies orange color when specified", () => {
    const { container } = render(
      <PulseAnimation isActive={true} color="orange">
        <div>Test Content</div>
      </PulseAnimation>
    );

    const orangeRings = container.querySelectorAll(".ring-orange-400");
    expect(orangeRings.length).toBeGreaterThan(0);
  });

  it("has correct opacity on animated ring layer", () => {
    const { container } = render(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    const animatedRing = container.querySelector(".opacity-75.animate-ping");
    expect(animatedRing).toBeInTheDocument();
  });

  it("has correct opacity on static ring layer", () => {
    const { container } = render(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    const staticRing = container.querySelector(".opacity-50:not(.animate-ping)");
    expect(staticRing).toBeInTheDocument();
  });

  it("wraps content in relative positioned div", () => {
    const { container } = render(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    const relativeDiv = container.querySelector(".relative");
    expect(relativeDiv).toBeInTheDocument();
  });

  it("applies rounded corners to ring layers", () => {
    const { container } = render(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    const roundedRings = container.querySelectorAll(".rounded-lg");
    expect(roundedRings.length).toBeGreaterThan(0);
  });

  it("children are rendered in relative z-index layer", () => {
    render(
      <PulseAnimation isActive={true}>
        <div data-testid="child-content">Test Content</div>
      </PulseAnimation>
    );

    const childContent = screen.getByTestId("child-content");
    expect(childContent).toBeInTheDocument();
  });

  it("toggles animation correctly", () => {
    const { container, rerender } = render(
      <PulseAnimation isActive={false}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    expect(container.querySelector(".animate-pulse-ring")).not.toBeInTheDocument();

    rerender(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    expect(container.querySelector(".animate-pulse-ring")).toBeInTheDocument();
  });

  it("maintains children content when animation state changes", () => {
    const { rerender } = render(
      <PulseAnimation isActive={false}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    expect(screen.getByText("Test Content")).toBeInTheDocument();

    rerender(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("can wrap complex children", () => {
    render(
      <PulseAnimation isActive={true}>
        <div>
          <h1>Title</h1>
          <p>Description</p>
          <button>Action</button>
        </div>
      </PulseAnimation>
    );

    expect(screen.getByText("Title")).toBeInTheDocument();
    expect(screen.getByText("Description")).toBeInTheDocument();
    expect(screen.getByText("Action")).toBeInTheDocument();
  });

  it("renders with absolute positioned ring layers", () => {
    const { container } = render(
      <PulseAnimation isActive={true}>
        <div>Test Content</div>
      </PulseAnimation>
    );

    const absoluteRings = container.querySelectorAll(".absolute.inset-0");
    expect(absoluteRings.length).toBe(2);
  });
});
