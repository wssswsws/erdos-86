---
fact_id: fact:erdos-86:lecture-wagner-cem
problem_id: erdos-86
source_project: erdos-86
source_task: task-record-existing-research-20260912
predecessors: []
status: reviewed
fact_type: literature_method
review_level: none
claim_policy: stable_claim
claim_summary: "Lecture 5.2 pages 103-110: Wagner deep cross-entropy method"
verification: null
---

## statement

Sequentially encode a graph as binary edge decisions, sample constructions from a policy network, keep elite scored trajectories, and train the network on those decisions. The primary paper is Wagner 2104.14516v1. The matching/spectral example gives a 19-vertex tree with two eight-leaf centers connected through an extra vertex; the conjecture had already been disproved before this smaller example. No CEM training was rerun here.

## notes

Evidence: references/user/source-pack/wagner-2104.14516.pdf; references/user/source-pack/lecture-selected-pages.txt; docs/ml-methods-from-lectures.md; https://arxiv.org/abs/2104.14516
Review scope: source audit by the assistant; for certificate results, independently executed integer checks. Not an Iteris agent-panel verified fact. No new result claimed.
