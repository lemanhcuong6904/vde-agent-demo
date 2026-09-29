import type { ChartSpecDTO } from "../../api/types";

export function chartAuditLines(chart: ChartSpecDTO): string[] {
  const refs = Array.isArray(chart.lineage.input_artifact_refs) ? chart.lineage.input_artifact_refs : [];
  const checks = Array.isArray(chart.validation.checks) ? chart.validation.checks : [];
  const validation = checks.join(", ") || String(chart.validation.overall_result || "not recorded");
  return [
    `Chart: ${chart.logical_chart_id} (revision ${chart.version})`,
    `Dataset: ${chart.dataset_hash}`,
    `Inputs: ${refs.length}`,
    `Validation: ${validation}`,
    ...chart.limitations.map((item) => `Limitation: ${item}`),
  ];
}

export function ChartAudit({ chart }: { chart: ChartSpecDTO }) {
  return <details className="chart-audit"><summary>Audit</summary><ul>{chartAuditLines(chart).map((line) => <li key={line}>{line}</li>)}</ul></details>;
}
