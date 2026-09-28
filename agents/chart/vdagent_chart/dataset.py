from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts import VisualTarget
from .errors import ChartError


def _metric_for(target: VisualTarget, artifacts: list[dict]) -> dict:
    allowed = set(target.artifact_ids)
    for artifact in artifacts:
        if artifact["artifact_type"] == "metric" and (not allowed or artifact["artifact_id"] in allowed):
            return artifact
    raise ChartError("DEP-005", f"no metric artifact available for target {target.target_id}", "dependency")


def assemble_dataset(target: VisualTarget, artifacts: list[dict], decision: dict[str, Any]) -> dict[str, Any]:
    if decision.get("top_n") is not None:
        raise ChartError("DAT-006", "top-N is not enabled by the demo policy", "data")
    metric = _metric_for(target, artifacts)
    records = metric["payload"]["records"]
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fields = sorted({field for record in records for field in record})
    return {
        "schema": [{"name": field, "role": "metric" if isinstance(next((r.get(field) for r in records if r.get(field) is not None), None), (int, float)) else "dimension"} for field in fields],
        "records": records,
        "row_count": len(records),
        "dataset_hash": f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}",
        "presentation_transforms": [],
        "unit": metric["payload"].get("unit"),
        "grain": metric["payload"].get("grain"),
    }
