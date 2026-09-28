from __future__ import annotations

import unittest

from vdagent_chart.dataset import assemble_dataset
from vdagent_chart.fixture_store import FixtureArtifactStore
from vdagent_chart.fixtures import load_demo_task


class DatasetTests(unittest.TestCase):
    def test_assembly_preserves_values_nulls_and_a_stable_hash(self) -> None:
        task = load_demo_task("price_trend")
        store = FixtureArtifactStore.demo()
        artifacts = [store.get_exact(ref) for ref in task.artifact_refs]
        first = assemble_dataset(task.visual_targets[0], artifacts, {"chart_type": "line"})
        second = assemble_dataset(task.visual_targets[0], artifacts, {"chart_type": "line"})

        self.assertEqual(first["records"], artifacts[0]["payload"]["records"])
        self.assertEqual(first["dataset_hash"], second["dataset_hash"])
        self.assertEqual(first["presentation_transforms"], [])

    def test_assembly_rejects_silent_top_n_and_never_changes_null_to_zero(self) -> None:
        task = load_demo_task("price_trend")
        store = FixtureArtifactStore.demo()
        artifacts = [store.get_exact(ref) for ref in task.artifact_refs]
        artifacts[0]["payload"]["records"][1]["price_m2"] = None

        data = assemble_dataset(task.visual_targets[0], artifacts, {"chart_type": "line"})
        self.assertIsNone(data["records"][1]["price_m2"])
        with self.assertRaisesRegex(Exception, "top-N"):
            assemble_dataset(task.visual_targets[0], artifacts, {"chart_type": "line", "top_n": 1})
