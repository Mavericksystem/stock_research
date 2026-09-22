import { describe, expect, it, vi } from "vitest";
import { createRef } from "react";
import { render } from "@testing-library/react";
import { axe } from "jest-axe";

import DashboardPage from "./DashboardPage";

/**
 * Automated accessibility smoke test (frontendchecklist.io
 * "testing/accessibility-testing" + "accessibility/form-labels").
 *
 * Guards the regression the manual audit originally caught: the chat
 * textarea must have an accessible name, not just a placeholder.
 */
describe("DashboardPage", () => {
  const baseProps = {
    messages: [],
    loading: false,
    steps: [],
    streamingAnswer: "",
    streamingSymbol: null,
    onSubmit: vi.fn(),
    onSuggestion: vi.fn(),
    onStock: vi.fn(),
    bottomRef: createRef<HTMLDivElement>(),
    suggestions: ["Why did AAPL move today?"],
    trackedStocks: ["AAPL", "MSFT"],
  };

  it("has no detectable accessibility violations in the empty state", async () => {
    const { container } = render(<DashboardPage {...baseProps} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("gives the chat textarea an accessible name", () => {
    const { getByRole } = render(<DashboardPage {...baseProps} />);
    expect(
      getByRole("textbox", { name: "Ask why a stock moved" }),
    ).toBeInTheDocument();
  });
});
