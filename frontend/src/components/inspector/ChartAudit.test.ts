import { describe, expect, it } from "vitest";
import { chartAuditLines } from "./ChartAudit";

describe("chartAuditLines", () => {
  it("exposes lineage, validation, and limitations", () => {
    expect(chartAuditLines({ dataset_hash: "sha256:x", lineage: { input_artifact_refs: ["metric@1"] }, validation: { checks: ["scope"] }, limitations: ["Gap"] } as never)).toEqual([
      "Dataset: sha256:x", "Inputs: 1", "Validation: scope", "Limitation: Gap",
    ]);
  });
});
