import { describe, expect, it } from "vitest";
import { ARTIFACT_EXACT, artifactKind } from "./artifacts";

describe("ChartSpec artifact ids", () => {
  it("treats immutable csp ids as charts while preserving legacy chart ids", () => {
    expect(ARTIFACT_EXACT.test("csp_0123456789ab")).toBe(true);
    expect(artifactKind("csp_0123456789ab")).toBe("chart");
    expect(artifactKind("ch_0123456789ab")).toBe("chart");
  });
});
