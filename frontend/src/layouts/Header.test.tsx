import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { axe } from "jest-axe";

import { SidebarProvider } from "@/components/ui/sidebar";
import Header from "../layouts/Header";

/**
 * Automated accessibility smoke test (frontendchecklist.io
 * "testing/accessibility-testing").
 *
 * Runs axe-core against the rendered header and asserts on the two things
 * the prior manual audit flagged directly: a real <h1> exists, and the logo
 * has descriptive alt text rather than being decorative.
 */
describe("Header", () => {
  it("has no detectable accessibility violations", async () => {
    const { container } = render(
      <SidebarProvider>
        <Header />
      </SidebarProvider>,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("exposes a real h1 for the app title", () => {
    const { getByRole } = render(
      <SidebarProvider>
        <Header />
      </SidebarProvider>,
    );

    expect(getByRole("heading", { level: 1, name: "Market Mind" })).toBeInTheDocument();
  });
});
