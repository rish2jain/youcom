import { render, screen } from "@testing-library/react";
import { ComparisonTable } from "../ComparisonTable";

describe("ComparisonTable Component", () => {
  it("renders table title and description", () => {
    render(<ComparisonTable />);

    expect(screen.getByText("Manual vs. Automated Intelligence")).toBeInTheDocument();
    expect(screen.getByText("See how Enterprise CIA transforms competitive research")).toBeInTheDocument();
  });

  it("renders table headers correctly", () => {
    render(<ComparisonTable />);

    expect(screen.getByText("Metric")).toBeInTheDocument();
    expect(screen.getByText("Manual Process")).toBeInTheDocument();
    expect(screen.getByText("Enterprise CIA")).toBeInTheDocument();
    expect(screen.getByText("Improvement")).toBeInTheDocument();
  });

  it("displays header descriptions", () => {
    render(<ComparisonTable />);

    expect(screen.getByText("Traditional approach")).toBeInTheDocument();
    expect(screen.getByText("Powered by You.com APIs")).toBeInTheDocument();
  });

  it("renders all comparison metrics", () => {
    render(<ComparisonTable />);

    expect(screen.getByText("Research Time")).toBeInTheDocument();
    expect(screen.getByText("Sources Analyzed")).toBeInTheDocument();
    expect(screen.getByText("Cost per Report")).toBeInTheDocument();
    expect(screen.getByText("Update Frequency")).toBeInTheDocument();
  });

  it("displays manual process values correctly", () => {
    render(<ComparisonTable />);

    expect(screen.getByText("2-4 hours")).toBeInTheDocument();
    expect(screen.getByText("10-20")).toBeInTheDocument();
    expect(screen.getByText("$500")).toBeInTheDocument();
    expect(screen.getByText("Weekly")).toBeInTheDocument();
  });

  it("displays automated process values correctly", () => {
    render(<ComparisonTable />);

    expect(screen.getByText("<2 minutes")).toBeInTheDocument();
    expect(screen.getByText("400+")).toBeInTheDocument();
    expect(screen.getByText("$5")).toBeInTheDocument();
    expect(screen.getByText("Real-time")).toBeInTheDocument();
  });

  it("displays improvement values correctly", () => {
    render(<ComparisonTable />);

    expect(screen.getByText("120x faster")).toBeInTheDocument();
    expect(screen.getByText("20x more")).toBeInTheDocument();
    expect(screen.getByText("100x cheaper")).toBeInTheDocument();
    expect(screen.getByText("Continuous")).toBeInTheDocument();
  });

  it("renders all metric icons", () => {
    render(<ComparisonTable />);

    // Icons should be rendered (lucide-react renders SVGs)
    const icons = document.querySelectorAll("svg");
    expect(icons.length).toBeGreaterThan(0);
  });

  it("displays ROI calculator section", () => {
    render(<ComparisonTable />);

    expect(screen.getByText("ROI Calculator")).toBeInTheDocument();
    expect(screen.getByText("For a company monitoring 20 competitors monthly")).toBeInTheDocument();
    expect(screen.getByText("$119,000")).toBeInTheDocument();
    expect(screen.getByText("Annual savings")).toBeInTheDocument();
  });

  it("renders table with hover effects", () => {
    render(<ComparisonTable />);

    const rows = document.querySelectorAll("tr.hover\\:bg-gray-50");
    expect(rows.length).toBeGreaterThan(0);
  });

  it("applies correct color classes to metrics", () => {
    render(<ComparisonTable />);

    // Check for color-coded elements (blue, green, purple, orange)
    const coloredElements = document.querySelectorAll('[class*="bg-blue-"], [class*="bg-green-"], [class*="bg-purple-"], [class*="bg-orange-"]');
    expect(coloredElements.length).toBeGreaterThan(0);
  });

  it("renders Check and X icons in header", () => {
    render(<ComparisonTable />);

    // Both Check and X icons should be present
    const checkIcons = document.querySelectorAll(".text-green-500");
    const xIcons = document.querySelectorAll(".text-red-500");

    expect(checkIcons.length).toBeGreaterThan(0);
    expect(xIcons.length).toBeGreaterThan(0);
  });

  it("displays values with correct emphasis colors", () => {
    render(<ComparisonTable />);

    const manualValues = document.querySelectorAll(".text-red-600");
    const automatedValues = document.querySelectorAll(".text-green-600");

    expect(manualValues.length).toBeGreaterThan(0);
    expect(automatedValues.length).toBeGreaterThan(0);
  });

  it("renders with responsive layout", () => {
    render(<ComparisonTable />);

    const table = screen.getByRole("table");
    expect(table).toBeInTheDocument();

    const container = document.querySelector(".overflow-x-auto");
    expect(container).toBeInTheDocument();
  });

  it("has correct gradient background for ROI section", () => {
    render(<ComparisonTable />);

    const roiSection = document.querySelector(".bg-gradient-to-r");
    expect(roiSection).toBeInTheDocument();
    expect(roiSection?.classList.contains("from-blue-50")).toBeTruthy();
  });

  it("renders all rows with correct structure", () => {
    render(<ComparisonTable />);

    const tableRows = document.querySelectorAll("tbody tr");
    expect(tableRows).toHaveLength(4); // 4 comparison metrics
  });

  it("displays improvement badges with correct styling", () => {
    render(<ComparisonTable />);

    const badges = document.querySelectorAll(".rounded-full");
    expect(badges.length).toBeGreaterThan(0);
  });

  it("renders all table cells with correct content", () => {
    render(<ComparisonTable />);

    // Check that we have cells for metrics, manual, automated, and improvement
    const tableCells = document.querySelectorAll("td");
    expect(tableCells.length).toBe(16); // 4 rows × 4 columns
  });
});
