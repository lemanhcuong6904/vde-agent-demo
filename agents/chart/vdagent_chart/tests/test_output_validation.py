from vdagent_chart.output_validation import validate_chart_spec


def test_rejects_semantic_spec_without_exact_lineage():
    outcome = validate_chart_spec({"schema_version": "chart-spec/2.0", "dataset": {"records": []}})
    assert outcome["overall_result"] == "fail"
    assert "lineage" in outcome["checks"]
