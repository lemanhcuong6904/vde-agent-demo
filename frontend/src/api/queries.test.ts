import { describe, expect, it } from "vitest";
import { shouldLoadLegacyChart } from "./queries";

describe("shouldLoadLegacyChart", () => {
  it("does not load the legacy chart endpoint for immutable chart specs", () => {
    expect(shouldLoadLegacyChart("csp_600eacbd2094")).toBe(false);
  });

  it("loads the legacy chart endpoint for legacy chart ids", () => {
    expect(shouldLoadLegacyChart("ch_600eacbd2094")).toBe(true);
  });
});
