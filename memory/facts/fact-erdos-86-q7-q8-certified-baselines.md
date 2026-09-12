---
fact_id: fact:erdos-86:q7-q8-certified-baselines
problem_id: erdos-86
source_project: erdos-86
source_task: task-record-existing-research-20260912
predecessors: []
status: reviewed
fact_type: certificate_result
review_level: none
claim_policy: stable_claim
claim_summary: "Independent edge-list checks: Q7 304 and Q8 682 are C4-free"
verification: null
---

## statement

The existing independent standard-library verifier checks every listed edge, uniqueness, every cube square, and common-neighbor pairs. Both published witnesses pass. The Q7 seed is not odd-square; the Q8 witness is odd-square. This verifies finite lower-bound witnesses, not optimality, novelty, or the original search process.

## notes

Evidence: references/baselines/86-verify.py; references/baselines/verification.json
Review scope: source audit by the assistant; for certificate results, independently executed integer checks. Not an Iteris agent-panel verified fact. No new result claimed.
