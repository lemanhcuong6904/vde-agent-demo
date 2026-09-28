import type { ChartSpecDTO } from "../../api/types";

export function chartAuditLines(chart: ChartSpecDTO): string[] {
  const refs = Array.isArray(chart.lineage.input_artifact_refs) ? chart.lineage.input_artifact_refs : [];
  const checks = Array.isArray(chart.validation.checks) ? chart.validation.checks : [];
  return [`Dataset: ${chart.dataset_hash}`, `Inputs: ${refs.length}`, `Validation: ${checks.join(", ") || "not recorded"}`, ...chart.limitations.map((item) => `Limitation: ${item}`)];
}

export function ChartAudit({ chart }: { chart: ChartSpecDTO }) {
  return <details className="chart-audit"><summary>Audit</summary><ul>{chartAuditLines(chart).map((line) => <li key={line}>{line}</li>)}</ul></details>;
}
