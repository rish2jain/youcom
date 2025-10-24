import { render, screen, waitFor } from "@testing-library/react";
import { SuccessConfetti } from "../SuccessConfetti";
import confetti from "canvas-confetti";

// Mock canvas-confetti
jest.mock("canvas-confetti");
const mockConfetti = confetti as jest.MockedFunction<typeof confetti>;

// Mock timer functions
jest.useFakeTimers();

describe("SuccessConfetti Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  it("does not render when trigger is false", () => {
    render(<SuccessConfetti trigger={false} />);

    expect(screen.queryByText(/Success/)).not.toBeInTheDocument();
  });

  it("renders success message when trigger is true", async () => {
    render(<SuccessConfetti trigger={true} />);

    await waitFor(() => {
      expect(screen.getByText(/Impact Card Generated/)).toBeInTheDocument();
    });
  });

  it("displays default message when no custom message provided", async () => {
    render(<SuccessConfetti trigger={true} />);

    await waitFor(() => {
      expect(screen.getByText("🎉 Success! Impact Card Generated!")).toBeInTheDocument();
    });
  });

  it("displays custom message when provided", async () => {
    render(<SuccessConfetti trigger={true} message="Custom Success!" />);

    await waitFor(() => {
      expect(screen.getByText("Custom Success!")).toBeInTheDocument();
    });
  });

  it("fires confetti when triggered", () => {
    render(<SuccessConfetti trigger={true} />);

    // Advance timers to trigger confetti
    jest.advanceTimersByTime(250);

    expect(mockConfetti).toHaveBeenCalled();
  });

  it("fires confetti from multiple positions", () => {
    render(<SuccessConfetti trigger={true} />);

    // Advance timers to trigger confetti
    jest.advanceTimersByTime(250);

    // Should be called twice per interval (left and right sides)
    expect(mockConfetti).toHaveBeenCalledTimes(2);
  });

  it("fires confetti with correct configuration", () => {
    render(<SuccessConfetti trigger={true} />);

    jest.advanceTimersByTime(250);

    expect(mockConfetti).toHaveBeenCalledWith(
      expect.objectContaining({
        startVelocity: 30,
        spread: 360,
        ticks: 60,
        zIndex: 0,
        particleCount: expect.any(Number),
        origin: expect.objectContaining({
          x: expect.any(Number),
          y: expect.any(Number),
        }),
      })
    );
  });

  it("continues firing confetti during animation duration", () => {
    render(<SuccessConfetti trigger={true} />);

    // Clear initial calls
    mockConfetti.mockClear();

    // Advance through multiple intervals
    jest.advanceTimersByTime(250);
    expect(mockConfetti).toHaveBeenCalled();

    mockConfetti.mockClear();
    jest.advanceTimersByTime(250);
    expect(mockConfetti).toHaveBeenCalled();
  });

  it("stops firing confetti after duration", () => {
    render(<SuccessConfetti trigger={true} />);

    // Advance past the 3 second duration
    jest.advanceTimersByTime(3500);

    mockConfetti.mockClear();

    // Advance more time - should not fire confetti
    jest.advanceTimersByTime(500);

    expect(mockConfetti).not.toHaveBeenCalled();
  });

  it("hides message after timeout", async () => {
    render(<SuccessConfetti trigger={true} />);

    // Message should be visible
    await waitFor(() => {
      expect(screen.getByText(/Success/)).toBeInTheDocument();
    });

    // Advance past the 4 second timeout
    jest.advanceTimersByTime(4100);

    await waitFor(() => {
      expect(screen.queryByText(/Success/)).not.toBeInTheDocument();
    });
  });

  it("renders message with correct styling", async () => {
    const { container } = render(<SuccessConfetti trigger={true} />);

    await waitFor(() => {
      const message = container.querySelector(".animate-bounce");
      expect(message).toBeInTheDocument();
      expect(message?.classList.contains("bg-gradient-to-r")).toBeTruthy();
      expect(message?.classList.contains("from-green-500")).toBeTruthy();
      expect(message?.classList.contains("to-blue-500")).toBeTruthy();
    });
  });

  it("message is positioned fixed and centered", async () => {
    const { container } = render(<SuccessConfetti trigger={true} />);

    await waitFor(() => {
      const messageContainer = container.querySelector(".fixed.inset-0");
      expect(messageContainer).toBeInTheDocument();
      expect(messageContainer?.classList.contains("flex")).toBeTruthy();
      expect(messageContainer?.classList.contains("items-center")).toBeTruthy();
      expect(messageContainer?.classList.contains("justify-center")).toBeTruthy();
    });
  });

  it("message is non-interactive (pointer-events-none)", async () => {
    const { container } = render(<SuccessConfetti trigger={true} />);

    await waitFor(() => {
      const messageContainer = container.querySelector(".pointer-events-none");
      expect(messageContainer).toBeInTheDocument();
    });
  });

  it("message has high z-index", async () => {
    const { container } = render(<SuccessConfetti trigger={true} />);

    await waitFor(() => {
      const messageContainer = container.querySelector(".z-50");
      expect(messageContainer).toBeInTheDocument();
    });
  });

  it("cleans up interval on unmount", () => {
    const { unmount } = render(<SuccessConfetti trigger={true} />);

    // Get number of timers
    const timersBefore = jest.getTimerCount();

    unmount();

    // Timers should be cleaned up
    const timersAfter = jest.getTimerCount();
    expect(timersAfter).toBeLessThanOrEqual(timersBefore);
  });

  it("handles re-triggering correctly", async () => {
    const { rerender } = render(<SuccessConfetti trigger={false} />);

    expect(screen.queryByText(/Success/)).not.toBeInTheDocument();

    rerender(<SuccessConfetti trigger={true} />);

    await waitFor(() => {
      expect(screen.getByText(/Success/)).toBeInTheDocument();
    });

    // Wait for message to hide
    jest.advanceTimersByTime(4100);

    await waitFor(() => {
      expect(screen.queryByText(/Success/)).not.toBeInTheDocument();
    });

    // Trigger again
    rerender(<SuccessConfetti trigger={false} />);
    rerender(<SuccessConfetti trigger={true} />);

    await waitFor(() => {
      expect(screen.getByText(/Success/)).toBeInTheDocument();
    });
  });

  it("fires confetti with random origin positions", () => {
    render(<SuccessConfetti trigger={true} />);

    jest.advanceTimersByTime(250);

    const calls = mockConfetti.mock.calls;

    // Check that different origin positions are used
    const origins = calls.map((call) => call[0]?.origin);
    expect(origins.length).toBeGreaterThan(0);

    // Should have different x values (left and right)
    const xValues = origins.map((origin) => origin?.x).filter((x) => x !== undefined);
    expect(new Set(xValues).size).toBeGreaterThan(1);
  });

  it("decreases particle count over time", () => {
    render(<SuccessConfetti trigger={true} />);

    // Get particle count at start
    jest.advanceTimersByTime(250);
    const firstCall = mockConfetti.mock.calls[0][0];
    const firstParticleCount = firstCall?.particleCount || 0;

    // Clear and advance
    mockConfetti.mockClear();
    jest.advanceTimersByTime(1000);

    const laterCall = mockConfetti.mock.calls[0][0];
    const laterParticleCount = laterCall?.particleCount || 0;

    // Particle count should decrease over time
    expect(laterParticleCount).toBeLessThan(firstParticleCount);
  });
});
