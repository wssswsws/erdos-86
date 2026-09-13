---
fact_id: fact:erdos-86:q7-corpus-180-verified
problem_id: erdos-86
source_project: erdos-86
source_task: task-q7-training-corpus-audit
predecessors: []
status: reviewed
fact_type: computational_result
review_level: none
claim_policy: stable_claim
claim_summary: "Validated 19866 published 304-edge graphs and prepared 180 cube-orbit representatives for the first single-A100 pilot"
verification: null
---

## statement

All 19866 graphs from upstream b94577fd5e06e62e1c6895b7e4d2b0abeaea411b passed independent integer C4 and edge checks, and all representative-to-member symmetry witnesses matched. The reviewed upstream canonical checker was rerun over all 645120 cube symmetries for each of 180 representatives and passed. The initial population contains one 304-edge representative per orbit, including 6 odd-square orbits. This is only the released catalogue; all representatives are training data, with no held-out generalization claim. Later elite updates remain exact-label deduplicated.

## notes

Evidence: references/corpora/q7-304-orbits/audit.json and canonical-check.log; docs/corpus-single-gpu-pilot.md; artifacts/experiments/q7-corpus-pilot-preparation/. Source/code audit and computational verification only, not Lean or Iteris panel certification. User authorized one A100 pilot with a one-hour Slurm limit.
