# SPDX-License-Identifier: Apache-2.0
"""Forward + backward coverage stats over a materialised scope.

Quantitative Outcomes §v0.1 coverage metrics.
"""

from __future__ import annotations

from oracle.analysis.coverage import compute_coverage
from rdflib import Graph

# 3 requirements (r1, r2, r3); 2 artifacts (a1, a2).
# a1 satisfies r1 and r2; a2 satisfies nothing → backward 50%.
# r1, r2 covered; r3 orphan → forward 66.66%.
RTM_TURTLE = """
@prefix rtm: <https://flexo-rtm.dev/ontology#> .
@prefix ex:  <https://rtm.example/> .

ex:r1 a rtm:Requirement .
ex:r2 a rtm:Requirement .
ex:r3 a rtm:Requirement .

ex:a1 a rtm:Artifact .
ex:a2 a rtm:Artifact .

ex:a1 rtm:addresses ex:r1 .
ex:a1 rtm:addresses ex:r2 .
"""


def _toy() -> Graph:
    g = Graph()
    g.parse(data=RTM_TURTLE, format="turtle")
    return g


def test_forward_coverage_is_two_of_three() -> None:
    stats = compute_coverage(_toy())
    assert stats.forward_percent == pytest.approx(200 / 3)


def test_backward_coverage_is_one_of_two() -> None:
    stats = compute_coverage(_toy())
    assert stats.backward_percent == 50.0


def test_coverage_empty_graph_yields_zero_population_signal() -> None:
    stats = compute_coverage(Graph())
    # No requirements ⇒ forward % is vacuous; convention: 100% (no failures).
    # No artifacts ⇒ backward % is vacuous; convention: 100%.
    assert stats.forward_percent == 100.0
    assert stats.backward_percent == 100.0


import pytest  # noqa: E402  -- imported here so the failure message in the assert reads cleanly
