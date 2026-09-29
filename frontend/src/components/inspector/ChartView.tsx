import { useEffect, useRef, useState } from "react";
import type { VisualizationSpec } from "vega-embed";
import type { ChartSpecDTO } from "../../api/types";
import { useChart, useChartSpec } from "../../api/queries";
import { ArtifactLink } from "../ArtifactLink";
import { ChartAudit } from "./ChartAudit";

/** Chart artifact metadata rendered beside the lazily loaded chart projection. */
export function chartSpecMetadata(
  chart: Pick<ChartSpecDTO, "lineage" | "limitations">,
): string[] {
  const refs = chart.lineage.input_artifact_refs;
  const sourceCount = Array.isArray(refs) ? refs.length : 0;
  const sourceLabel = `${sourceCount} input artifact${sourceCount === 1 ? "" : "s"}`;
  return [sourceLabel, ...chart.limitations.map((limitation) => `Limitation: ${limitation}`)];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function renderableChartSpec(spec: Record<string, unknown>): Record<string, unknown> {
  const projection = spec.render_spec;
  if (isRecord(projection)) return projection;
  return spec;
}

export function rendererForSpec(spec: Record<string, unknown>): "plotly" | "vega" {
  return spec.renderer === "plotly" ? "plotly" : "vega";
}

export function plotlyRenderDependencies(spec: Record<string, unknown>): string[] {
  return rendererForSpec(spec) === "plotly" ? ["mathjax/es5/tex-svg.js", "plotly.js-dist-min"] : ["vega-embed"];
}

async function loadPlotlyRenderer() {
  const root = globalThis as typeof globalThis & { MathJax?: unknown };
  if (!root.MathJax) {
    root.MathJax = {
      tex: { inlineMath: [["$", "$"], ["\\(", "\\)"]] },
      svg: { fontCache: "global" },
    };
  }
  await import("mathjax/es5/tex-svg.js");
  return import("plotly.js-dist-min");
}

export function ChartView({ id }: { id: string }) {
  const isImmutable = id.startsWith("csp_");
  const legacyQuery = useChart(id);
  const immutableQuery = useChartSpec(id);
  const query = isImmutable ? immutableQuery : legacyQuery;
  const container = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const spec = isImmutable
    ? immutableQuery.data && renderableChartSpec(immutableQuery.data.chart_spec)
    : legacyQuery.data?.spec;

  useEffect(() => {
    const el = container.current;
    if (!el || !spec) return;
    let disposed = false;
    let finalize: (() => void) | undefined;
    setError(null);
    el.innerHTML = "";
    const render =
      rendererForSpec(spec) === "plotly"
        ? loadPlotlyRenderer().then((Plotly) => {
            const plotly = Plotly.default ?? Plotly;
            return plotly
              .newPlot(
                el,
                Array.isArray(spec.data) ? spec.data : [],
                isRecord(spec.layout) ? spec.layout : {},
                isRecord(spec.config) ? spec.config : {},
              )
              .then(() => ({ finalize: () => plotly.purge(el) }));
          })
        : import("vega-embed").then(({ default: embed }) =>
            embed(el, { ...spec, width: "container", autosize: { type: "fit", contains: "padding" } } as VisualizationSpec, {
              actions: false,
              renderer: "svg",
            }),
          );
    render
      .then((result) => {
        if (disposed) result.finalize();
        else finalize = () => result.finalize();
      })
      .catch((err: unknown) => {
        if (!disposed) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      disposed = true;
      finalize?.();
    };
  }, [spec]);

  if (query.isPending) return <div className="muted small">Loading {id}…</div>;
  if (query.isError) return <div className="error-text">{id}: {query.error.message}</div>;
  return (
    <figure className="chart">
      <figcaption className="chart-head">
        <span className="mono artifact-id">{id}</span>
        <span className="chart-title">{query.data?.title}</span>
        {isImmutable ? (
          <span className="muted small">
            {immutableQuery.data && chartSpecMetadata(immutableQuery.data).join(" · ")}
          </span>
        ) : (
          <span className="muted small">
            from <ArtifactLink id={legacyQuery.data!.dataset_id} />
          </span>
        )}
      </figcaption>
      <div className="chart-canvas" ref={container} />
      {isImmutable && immutableQuery.data && <ChartAudit chart={immutableQuery.data} />}
      {error && <div className="error-text">Chart failed to render: {error}</div>}
    </figure>
  );
}
