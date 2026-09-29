import { describe, expect, it } from "vitest";
import { chartSpecMetadata, renderableChartSpec } from "./ChartView";

describe("chartSpecMetadata", () => {
  it("makes immutable lineage and limitations visible to a renderer user", () => {
    expect(
      chartSpecMetadata({
        lineage: { input_artifact_refs: [{ artifact_id: "metric_price", version: 2 }] },
        limitations: ["No causal interpretation"],
      }),
    ).toEqual(["1 input artifact", "Limitation: No causal interpretation"]);
  });

  it("renders the Vega-Lite projection from semantic chart specs", () => {
    const semantic = {
      schema_version: "chart-spec/2.0",
      chart_type: "pie",
      selection: { chart_type: "pie", fallback_reason: null },
      render_spec: {
        $schema: "https://vega.github.io/schema/vega-lite/v5.json",
        mark: { type: "arc", tooltip: true },
        data: { values: [{ status: "Available", count: 120 }] },
        encoding: { theta: { field: "count", type: "quantitative" } },
      },
    };

    expect(renderableChartSpec(semantic)).toEqual(semantic.render_spec);
  });
});
