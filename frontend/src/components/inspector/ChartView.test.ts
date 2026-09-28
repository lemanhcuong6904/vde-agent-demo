import { describe, expect, it } from "vitest";
import { chartSpecMetadata } from "./ChartView";

describe("chartSpecMetadata", () => {
  it("makes immutable lineage and limitations visible to a renderer user", () => {
    expect(
      chartSpecMetadata({
        lineage: { input_artifact_refs: [{ artifact_id: "metric_price", version: 2 }] },
        limitations: ["No causal interpretation"],
      }),
    ).toEqual(["1 input artifact", "Limitation: No causal interpretation"]);
  });
});
