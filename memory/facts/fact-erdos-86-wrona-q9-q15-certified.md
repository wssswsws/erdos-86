---
fact_id: fact:erdos-86:wrona-q9-q15-certified
problem_id: erdos-86
source_project: erdos-86
source_task: task-record-existing-research-20260912
predecessors: []
status: reviewed
fact_type: certificate_result
review_level: none
claim_policy: stable_claim
claim_summary: "Independent Q9-Q15 audit: 1505 3304 7164 15372 32856 69909 148126"
verification: null
---

## statement

All seven downloaded edge lists pass raw SHA-256 checks and an independently written integer-only checker using both exhaustive cube-face enumeration and common-neighbor pairs. Total faces checked: 1504512; no C4 found. This establishes those finite lower-bound witnesses. Only Q9-Q11 exceed the particular general BHN formula compared in the repository; no exhaustive novelty or optimality claim is made. This new audit supersedes the earlier local note that these seven files had not been rerun.

## notes

Evidence: scripts/verify_wrona_certificates.py; artifacts/experiments/literature-intake-20260912/wrona-independent-verification.json; references/user/source-pack/wrona/SHA256SUMS
Review scope: source audit by the assistant; for certificate results, independently executed integer checks. Not an Iteris agent-panel verified fact. No new result claimed.
