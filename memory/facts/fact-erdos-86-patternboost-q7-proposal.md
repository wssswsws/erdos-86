---
fact_id: fact:erdos-86:patternboost-q7-proposal
problem_id: erdos-86
source_project: erdos-86
source_task: task-record-existing-research-20260912
predecessors:
  - fact:erdos-86:minamoto-odd-square-scope
  - fact:erdos-86:minamoto-catalogue-scope
  - fact:erdos-86:lecture-patternboost
status: reviewed
fact_type: research_proposal
review_level: none
claim_policy: stable_claim
claim_summary: "Proposed Q7 PatternBoost experiment with 448 edge decisions"
verification: null
---

## statement

Proposed, not implemented: train/generate using only the 448 possible Q7 edges, apply C4 repair and local improvement, and compare against local search alone under equal total compute and evaluation budgets. Use independent exact verification for candidates and avoid restricting all samples to odd-square. Track diversity and deduplicate cube-symmetry copies. The 19866 sample catalogue has not yet been imported as a training set.

## notes

Evidence: docs/ml-methods-from-lectures.md
Review scope: source audit by the assistant; for certificate results, independently executed integer checks. Not an Iteris agent-panel verified fact. No new result claimed.
