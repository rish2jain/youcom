import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import {
  CognitiveLoadOptimizer,
  createCognitiveElement,
  createContentSection,
  withCognitiveOptimization,
} from "../CognitiveLoadOptimizer";

// Mock Lucide React icons
jest.mock("lucide-react", () => ({
  Brain: "Brain",
  AlertTriangle: "AlertTriangle",
  CheckCircle: "CheckCircle",
  Info: "Info",
  Settings: "Settings",
}));

const mockSections = [
  createContentSection(
    "section-1",
    "Critical Section",
    [
      createCognitiveElement("element-1", "text", "low", "critical"),
      createCognitiveElement("element-2", "metric", "medium", "critical"),
    ],
    1
  ),
  createContentSection(
    "section-2",
    "Important Section",
    [
      createCognitiveElement("element-3", "chart", "high", "important"),
      createCognitiveElement("element-4", "action", "medium", "important"),
    ],
    2
  ),
  createContentSection(
    "section-3",
    "Supplementary Section",
    [
      createCognitiveElement("element-5", "table", "high", "supplementary"),
      createCognitiveElement("element-6", "image", "low", "supplementary"),
    ],
    3
  ),
];

describe("CognitiveLoadOptimizer Component", () => {
  it("renders cognitive load indicator", () => {
    render(
      <CognitiveLoadOptimizer sections={mockSections} userRole="analyst" />
    );

    expect(screen.getByText("Cognitive Load")).toBeInTheDocument();
    expect(screen.getByText("Cognitive Load")).toBeInTheDocument();
    expect(screen.getByText(/\d+\/\d+/)).toBeInTheDocument();
  });

  it("shows complexity indicator", () => {
    render(
      <CognitiveLoadOptimizer sections={mockSections} userRole="analyst" />
    );

    expect(screen.getByText(/complexity/)).toBeInTheDocument();
  });

  it("shows overload warning when cognitive load exceeds limit", () => {
    render(
      <CognitiveLoadOptimizer
        sections={mockSections}
        userRole="executive" // Lower cognitive load limit
      />
    );

    expect(screen.getByText("Overloaded")).toBeInTheDocument();
  });

  it("toggles optimization panel", async () => {
    render(
      <CognitiveLoadOptimizer sections={mockSections} userRole="analyst" />
    );

    const optimizeButton = screen.getByText("Optimize");
    fireEvent.click(optimizeButton);

    await waitFor(() => {
      expect(screen.getByText("User Role")).toBeInTheDocument();
      expect(screen.getByText("Executive")).toBeInTheDocument();
      expect(screen.getByText("Analyst")).toBeInTheDocument();
      expect(screen.getByText("Technical")).toBeInTheDocument();
    });

    // Click again to hide
    const hideButton = screen.getByText("Hide");
    fireEvent.click(hideButton);

    await waitFor(() => {
      expect(screen.queryByText("User Role")).not.toBeInTheDocument();
    });
  });

  it("changes user role and updates optimization", async () => {
    const mockOnOptimizationChange = jest.fn();

    render(
      <CognitiveLoadOptimizer
        sections={mockSections}
        userRole="analyst"
        onOptimizationChange={mockOnOptimizationChange}
      />
    );

    // Open optimization panel
    const optimizeButton = screen.getByText("Optimize");
    fireEvent.click(optimizeButton);

    await waitFor(() => {
      const executiveButton = screen.getByText("Executive");
      fireEvent.click(executiveButton);
    });

    // Should call optimization change callback
    expect(mockOnOptimizationChange).toHaveBeenCalled();
  });

  it("shows optimization recommendations", async () => {
    render(
      <CognitiveLoadOptimizer
        sections={mockSections}
        userRole="executive" // Will trigger optimization
      />
    );

    const optimizeButton = screen.getByText("Optimize");
    fireEvent.click(optimizeButton);

    await waitFor(() => {
      expect(
        screen.getByText("Optimization Recommendations")
      ).toBeInTheDocument();
    });
  });

  it("displays content analysis breakdown", async () => {
    render(
      <CognitiveLoadOptimizer sections={mockSections} userRole="analyst" />
    );

    const optimizeButton = screen.getByText("Optimize");
    fireEvent.click(optimizeButton);

    await waitFor(() => {
      expect(screen.getByText("Content Analysis")).toBeInTheDocument();
      // Should show counts for different element types
      expect(screen.getByText("Texts")).toBeInTheDocument();
      expect(screen.getByText("Metrics")).toBeInTheDocument();
      expect(screen.getByText("Charts")).toBeInTheDocument();
    });
  });

  it("shows improvement suggestions", async () => {
    const sectionsWithManyTables = [
      createContentSection(
        "section-1",
        "Table Heavy Section",
        [
          createCognitiveElement("table-1", "table", "high", "important"),
          createCognitiveElement("table-2", "table", "high", "important"),
          createCognitiveElement("table-3", "table", "high", "important"),
        ],
        1
      ),
    ];

    render(
      <CognitiveLoadOptimizer
        sections={sectionsWithManyTables}
        userRole="analyst"
      />
    );

    const optimizeButton = screen.getByText("Optimize");
    fireEvent.click(optimizeButton);

    await waitFor(() => {
      expect(screen.getByText("Improvement Suggestions")).toBeInTheDocument();
      expect(screen.getByText(/converting some tables/)).toBeInTheDocument();
    });
  });

  it("shows executive summary for executive role", () => {
    render(
      <CognitiveLoadOptimizer sections={mockSections} userRole="executive" />
    );

    expect(
      screen.getByText("Executive Summary (Auto-generated)")
    ).toBeInTheDocument();
  });

  it("shows debug information when enabled", async () => {
    render(
      <CognitiveLoadOptimizer
        sections={mockSections}
        userRole="analyst"
        showDebugInfo={true}
      />
    );

    const optimizeButton = screen.getByText("Optimize");
    fireEvent.click(optimizeButton);

    await waitFor(() => {
      expect(screen.getByText("Debug Information")).toBeInTheDocument();
      expect(screen.getByText(/Original sections:/)).toBeInTheDocument();
      expect(screen.getByText(/Optimized sections:/)).toBeInTheDocument();
      expect(screen.getByText(/Max cognitive load:/)).toBeInTheDocument();
    });
  });

  it("renders children content", () => {
    render(
      <CognitiveLoadOptimizer sections={mockSections} userRole="analyst">
        <div>Child Content</div>
      </CognitiveLoadOptimizer>
    );

    expect(screen.getByText("Child Content")).toBeInTheDocument();
  });
});

describe("Cognitive Load Management Utilities", () => {
  describe("createCognitiveElement", () => {
    it("creates element with correct properties", () => {
      const element = createCognitiveElement(
        "test-id",
        "chart",
        "high",
        "critical"
      );

      expect(element).toEqual({
        id: "test-id",
        type: "chart",
        complexity: "high",
        priority: "critical",
      });
    });

    it("uses default values for optional parameters", () => {
      const element = createCognitiveElement("test-id", "text");

      expect(element).toEqual({
        id: "test-id",
        type: "text",
        complexity: "medium",
        priority: "important",
      });
    });
  });

  describe("createContentSection", () => {
    it("creates section with correct properties", () => {
      const elements = [
        createCognitiveElement("el-1", "text"),
        createCognitiveElement("el-2", "metric"),
      ];

      const section = createContentSection(
        "section-id",
        "Section Title",
        elements,
        2
      );

      expect(section).toEqual({
        id: "section-id",
        title: "Section Title",
        elements,
        level: 2,
      });
    });

    it("uses default level when not specified", () => {
      const section = createContentSection("section-id", "Section Title", []);

      expect(section.level).toBe(1);
    });
  });
});

describe("withCognitiveOptimization HOC", () => {
  const TestComponent = ({ sections }: { sections: any[] }) => (
    <div>
      <div>Test Component</div>
      <div>Sections: {sections.length}</div>
    </div>
  );

  it("wraps component with cognitive optimization", () => {
    const OptimizedComponent = withCognitiveOptimization(
      TestComponent,
      mockSections
    );

    render(<OptimizedComponent userRole="analyst" />);

    expect(screen.getByText("Test Component")).toBeInTheDocument();
    expect(screen.getByText("Sections: 3")).toBeInTheDocument();
  });

  it("shows optimization warning when overloaded", () => {
    const OptimizedComponent = withCognitiveOptimization(
      TestComponent,
      mockSections
    );

    render(<OptimizedComponent userRole="executive" />);

    expect(
      screen.getByText(/Content optimized for better readability/)
    ).toBeInTheDocument();
  });

  it("passes through props correctly", () => {
    const TestComponentWithProps = ({
      sections,
      customProp,
    }: {
      sections: any[];
      customProp: string;
    }) => (
      <div>
        <div>Custom Prop: {customProp}</div>
        <div>Sections: {sections.length}</div>
      </div>
    );

    const OptimizedComponent = withCognitiveOptimization(
      TestComponentWithProps,
      mockSections
    );

    render(<OptimizedComponent userRole="analyst" customProp="test-value" />);

    expect(screen.getByText("Custom Prop: test-value")).toBeInTheDocument();
    expect(screen.getByText("Sections: 3")).toBeInTheDocument();
  });

  it("uses provided sections over default sections", () => {
    const customSections = [
      createContentSection("custom", "Custom Section", [], 1),
    ];

    const OptimizedComponent = withCognitiveOptimization(
      TestComponent,
      mockSections
    );

    render(<OptimizedComponent userRole="analyst" sections={customSections} />);

    expect(screen.getByText("Sections: 1")).toBeInTheDocument();
  });
});
