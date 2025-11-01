import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import {
  ProgressiveDisclosure,
  DisclosureSection,
  MetricDisplay,
} from "../ProgressiveDisclosure";

// Mock Lucide React icons
jest.mock("lucide-react", () => ({
  ChevronDown: "ChevronDown",
  ChevronRight: "ChevronRight",
  Info: "Info",
  Settings: "Settings",
  Eye: "Eye",
  EyeOff: "EyeOff",
  Layers: "Layers",
  Brain: "Brain",
}));

const mockLevels = [
  {
    id: "level-1",
    title: "Critical Insights",
    content: <div>Level 1 Content</div>,
    defaultExpanded: true,
    badge: "3 items",
    priority: "critical" as const,
    cognitiveWeight: 5,
  },
  {
    id: "level-2",
    title: "Supporting Evidence",
    content: <div>Level 2 Content</div>,
    badge: "10 sources",
    priority: "important" as const,
    cognitiveWeight: 8,
  },
  {
    id: "level-3",
    title: "Technical Details",
    content: <div>Level 3 Content</div>,
    badge: "API data",
    priority: "supplementary" as const,
    cognitiveWeight: 12,
  },
];

describe("ProgressiveDisclosure Component", () => {
  it("renders with title and subtitle", () => {
    render(
      <ProgressiveDisclosure
        title="Test Title"
        subtitle="Test Subtitle"
        levels={mockLevels}
      />
    );

    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("Test Subtitle")).toBeInTheDocument();
  });

  it("shows mode selector with all three modes", () => {
    render(<ProgressiveDisclosure title="Test" levels={mockLevels} />);

    expect(screen.getByText("Executive")).toBeInTheDocument();
    expect(screen.getByText("Analyst")).toBeInTheDocument();
    expect(screen.getByText("Technical")).toBeInTheDocument();
  });

  it("displays cognitive load indicator", () => {
    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        maxCognitiveLoad={15}
      />
    );

    expect(screen.getByText(/elements/)).toBeInTheDocument();
    expect(screen.getByText(/elements/)).toBeInTheDocument();
  });

  it("expands default expanded levels", () => {
    render(<ProgressiveDisclosure title="Test" levels={mockLevels} />);

    expect(screen.getByText("Level 1 Content")).toBeInTheDocument();
    expect(screen.queryByText("Level 2 Content")).not.toBeInTheDocument();
    expect(screen.queryByText("Level 3 Content")).not.toBeInTheDocument();
  });

  it("toggles level expansion on click", async () => {
    render(<ProgressiveDisclosure title="Test" levels={mockLevels} />);

    // Level 2 should be collapsed initially
    expect(screen.queryByText("Level 2 Content")).not.toBeInTheDocument();

    // Click to expand level 2
    const level2Button = screen.getByText("Supporting Evidence");
    fireEvent.click(level2Button);

    await waitFor(() => {
      expect(screen.getByText("Level 2 Content")).toBeInTheDocument();
    });

    // Click again to collapse
    fireEvent.click(level2Button);

    await waitFor(() => {
      expect(screen.queryByText("Level 2 Content")).not.toBeInTheDocument();
    });
  });

  it("changes mode and auto-expands appropriate levels", async () => {
    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        mode="executive"
      />
    );

    // Initially in executive mode - only level 1 visible
    expect(screen.getByText("Level 1 Content")).toBeInTheDocument();
    expect(screen.queryByText("Level 2 Content")).not.toBeInTheDocument();

    // Switch to analyst mode
    const analystButton = screen.getByText("Analyst");
    fireEvent.click(analystButton);

    await waitFor(() => {
      expect(screen.getByText("Level 1 Content")).toBeInTheDocument();
      expect(screen.getByText("Level 2 Content")).toBeInTheDocument();
      expect(screen.queryByText("Level 3 Content")).not.toBeInTheDocument();
    });

    // Switch to technical mode
    const technicalButton = screen.getByText("Technical");
    fireEvent.click(technicalButton);

    await waitFor(() => {
      expect(screen.getByText("Level 1 Content")).toBeInTheDocument();
      expect(screen.getByText("Level 2 Content")).toBeInTheDocument();
      expect(screen.getByText("Level 3 Content")).toBeInTheDocument();
    });
  });

  it("shows correct number of visible levels based on mode", () => {
    const { rerender } = render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        mode="executive"
      />
    );

    // Executive mode: only 1 level visible
    expect(screen.getByText("Critical Insights")).toBeInTheDocument();
    expect(screen.queryByText("Supporting Evidence")).not.toBeInTheDocument();
    expect(screen.queryByText("Technical Details")).not.toBeInTheDocument();

    rerender(
      <ProgressiveDisclosure title="Test" levels={mockLevels} mode="analyst" />
    );

    // Analyst mode: 2 levels visible
    expect(screen.getByText("Critical Insights")).toBeInTheDocument();
    expect(screen.getByText("Supporting Evidence")).toBeInTheDocument();
    expect(screen.queryByText("Technical Details")).not.toBeInTheDocument();

    rerender(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        mode="technical"
      />
    );

    // Technical mode: all levels visible
    expect(screen.getByText("Critical Insights")).toBeInTheDocument();
    expect(screen.getByText("Supporting Evidence")).toBeInTheDocument();
    expect(screen.getByText("Technical Details")).toBeInTheDocument();
  });

  it("displays level badges", () => {
    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        mode="technical"
      />
    );

    expect(screen.getByText("3 items")).toBeInTheDocument();
    expect(screen.getByText("10 sources")).toBeInTheDocument();
    expect(screen.getByText("API data")).toBeInTheDocument();
  });

  it("shows expand/collapse all buttons", () => {
    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        mode="technical"
      />
    );

    expect(screen.getByText("Collapse All")).toBeInTheDocument();
    expect(screen.getByText("Expand All")).toBeInTheDocument();
  });

  it("expands all levels when clicking Expand All", async () => {
    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        mode="technical"
      />
    );

    const expandAllButton = screen.getByText("Expand All");
    fireEvent.click(expandAllButton);

    await waitFor(() => {
      expect(screen.getByText("Level 1 Content")).toBeInTheDocument();
      expect(screen.getByText("Level 2 Content")).toBeInTheDocument();
      expect(screen.getByText("Level 3 Content")).toBeInTheDocument();
    });
  });

  it("collapses all levels when clicking Collapse All", async () => {
    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        mode="technical"
      />
    );

    // First expand all
    const expandAllButton = screen.getByText("Expand All");
    fireEvent.click(expandAllButton);

    await waitFor(() => {
      expect(screen.getByText("Level 1 Content")).toBeInTheDocument();
    });

    // Then collapse all
    const collapseAllButton = screen.getByText("Collapse All");
    fireEvent.click(collapseAllButton);

    await waitFor(() => {
      expect(screen.queryByText("Level 1 Content")).not.toBeInTheDocument();
      expect(screen.queryByText("Level 2 Content")).not.toBeInTheDocument();
      expect(screen.queryByText("Level 3 Content")).not.toBeInTheDocument();
    });
  });

  it("shows 'Show all details' button in non-technical modes", () => {
    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        mode="executive"
      />
    );

    expect(screen.getByText("Show all details")).toBeInTheDocument();
  });

  it("switches to technical mode when clicking 'Show all details'", async () => {
    const mockOnModeChange = jest.fn();

    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        mode="executive"
        onModeChange={mockOnModeChange}
      />
    );

    const showAllButton = screen.getByText("Show all details");
    fireEvent.click(showAllButton);

    expect(mockOnModeChange).toHaveBeenCalledWith("technical");
  });

  it("calls onModeChange when mode is changed", () => {
    const mockOnModeChange = jest.fn();

    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        onModeChange={mockOnModeChange}
      />
    );

    const executiveButton = screen.getByText("Executive");
    fireEvent.click(executiveButton);

    expect(mockOnModeChange).toHaveBeenCalledWith("executive");
  });

  it("shows section count in footer", () => {
    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        mode="technical"
      />
    );

    expect(screen.getByText(/Showing \d+ of \d+ sections/)).toBeInTheDocument();
  });

  it("handles cognitive load optimization", () => {
    const mockOnCognitiveLoadChange = jest.fn();

    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        maxCognitiveLoad={10}
        onCognitiveLoadChange={mockOnCognitiveLoadChange}
      />
    );

    // Should call the callback with calculated cognitive load
    expect(mockOnCognitiveLoadChange).toHaveBeenCalled();
  });

  it("shows high cognitive load warning", () => {
    render(
      <ProgressiveDisclosure
        title="Test"
        levels={mockLevels}
        maxCognitiveLoad={3} // Very low limit to trigger warning
        mode="technical"
      />
    );

    // Expand all to increase cognitive load
    const expandAllButton = screen.getByText("Expand All");
    fireEvent.click(expandAllButton);

    expect(screen.getByText("⚠️ High cognitive load")).toBeInTheDocument();
  });
});

describe("DisclosureSection Component", () => {
  it("renders children with proper styling", () => {
    render(
      <DisclosureSection>
        <div>Test Content</div>
      </DisclosureSection>
    );

    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(
      <DisclosureSection className="custom-class">
        <div>Test Content</div>
      </DisclosureSection>
    );

    const container = screen.getByText("Test Content").parentElement;
    expect(container).toHaveClass("custom-class");
  });
});

describe("MetricDisplay Component", () => {
  it("renders label and value", () => {
    render(<MetricDisplay label="Test Metric" value="100" unit="%" />);

    expect(screen.getByText("Test Metric:")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("shows trend indicators", () => {
    const { rerender } = render(
      <MetricDisplay label="Test" value="100" trend="up" />
    );

    expect(screen.getByText("↗️")).toBeInTheDocument();

    rerender(<MetricDisplay label="Test" value="100" trend="down" />);

    expect(screen.getByText("↘️")).toBeInTheDocument();

    rerender(<MetricDisplay label="Test" value="100" trend="neutral" />);

    expect(screen.getByText("→")).toBeInTheDocument();
  });

  it("applies custom color", () => {
    render(<MetricDisplay label="Test" value="100" color="text-red-600" />);

    const valueElement = screen.getByText("100");
    expect(valueElement).toHaveClass("text-red-600");
  });

  it("handles numeric values", () => {
    render(<MetricDisplay label="Test" value={42} unit=" items" />);

    expect(screen.getByText("42 items")).toBeInTheDocument();
  });
});
