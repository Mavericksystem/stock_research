import "@testing-library/jest-dom/vitest";
import { expect } from "vitest";
import { toHaveNoViolations } from "jest-axe";

// Extends Vitest's `expect` with `.toHaveNoViolations()` so a11y assertions
// read the same way they would with jest-axe under Jest.
expect.extend(toHaveNoViolations);
