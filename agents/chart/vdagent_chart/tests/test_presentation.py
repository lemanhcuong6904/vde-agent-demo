from __future__ import annotations

import unittest

from vdagent_chart.presentation import build_presentation


class PresentationTests(unittest.TestCase):
    def test_rejects_causal_language_and_sanitizes_html(self) -> None:
        with self.assertRaisesRegex(Exception, "causal"):
            build_presentation("Price causes DOM to increase", "scope")
        presentation = build_presentation("<b>DOM</b> by month", "VHOP")
        self.assertNotIn("<", presentation["title"])
