---
fact_id: fact:erdos-86:finite-averaging-intervals
problem_id: erdos-86
source_project: erdos-86
source_task: task-record-existing-research-20260912
predecessors:
  - fact:erdos-86:q7-q8-certified-baselines
status: reviewed
fact_type: derived_result
review_level: none
claim_policy: stable_claim
claim_summary: "Finite averaging: 304<=f7<=308 and 682<=f8<=704"
verification: null
---

## statement

Each edge belongs to n-1 of the 2n codimension-one subcubes, so (n-1)f(n)<=2nf(n-1). Conditional only on the cited established historical value f(6)=132, this yields f(7)<=308 and f(8)<=704. The counting argument is checked directly in docs/existing-research.md; the historical f(6) upper-bound proof was not rerun. The observation is already in forum post 8612 and is not new.

## notes

Evidence: docs/existing-research.md; https://www.erdosproblems.com/forum/thread/86#post-8612
Review scope: source audit by the assistant; for certificate results, independently executed integer checks. Not an Iteris agent-panel verified fact. No new result claimed.
