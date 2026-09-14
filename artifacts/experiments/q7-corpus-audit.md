# Q7 training-corpus audit

Completed September 12, 2026. See [audit.json](../../references/corpora/q7-304-orbits/audit.json) and the [corpus README](../../references/corpora/q7-304-orbits/README.md).

- All 19,866 constructions independently verified as C4-free with 304 edges; no duplicate exact labelings.
- All 19,866 orbit-membership mapping witnesses independently checked.
- Upstream canonicalization completely rerun over all 645,120 cube symmetries for each representative; 180 distinct canonical forms.
- One representative extracted per orbit: six odd-square and 174 other representatives.
- The first pilot used all representatives, with no holdout. This did not establish unseen-orbit generalization or completeness over all 304-edge graphs.

The original task mentioned designing a split. The first construction-search pilot deliberately used all orbit-balanced references; the later diagnostic experiment introduced a 144/36 split. This record describes reviewed computational evidence, not Lean formalization or Iteris agent-panel certification.
