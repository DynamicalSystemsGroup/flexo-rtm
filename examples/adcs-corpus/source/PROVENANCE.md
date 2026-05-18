<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# ADCS corpus — source provenance

These are verbatim copies of the prototype's RDF, kept here for provenance.

| File | Source |
|---|---|
| `rtm.ttl` | [`ADCS-lifecycle-demo/output/rtm.ttl`](https://github.com/DynamicalSystemsGroup/ADCS-lifecycle-demo/blob/main/output/rtm.ttl) — assembled post-attestation RTM |
| `satellite.ttl` | [`ADCS-lifecycle-demo/structural/satellite.ttl`](https://github.com/DynamicalSystemsGroup/ADCS-lifecycle-demo/blob/main/structural/satellite.ttl) — SysMLv2 structural model |
| `parameters.ttl` | [`ADCS-lifecycle-demo/structural/parameters.ttl`](https://github.com/DynamicalSystemsGroup/ADCS-lifecycle-demo/blob/main/structural/parameters.ttl) — satellite parameters |

The prototype uses an older internal vocabulary at `<http://example.org/ontology/rtm#>` with terms like `rtm:addresses`, `rtm:ProofArtifact`, `rtm:SimulationResult` (now obsolete in `flexo-rtm`'s framework half). [`scripts/translate_adcs_corpus.py`](../../../scripts/translate_adcs_corpus.py) generates the flexo-rtm-vocab version in [`../rtm.ttl`](../rtm.ttl), which is what the regression test loads.

Per [`ADCS Prototype Lessons`](https://github.com/dynamicalsystemsgroup/flexo-rtm-research/wiki/ADCS-Prototype-Lessons) §7, the prototype will migrate to depend on `flexo-rtm`; at that point the prototype's source TTLs will already use the flexo-rtm vocabulary and this translation step disappears.
