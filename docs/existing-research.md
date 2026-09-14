# Erdős #86: existing research and project checks

Source intake: September 12, 2026. Updated September 13 to distinguish the historical Q7 upper bounds, the project's counting argument, and completed GPU work. External source observations below are dated snapshots, not a continuously updated literature survey.

## Definitions and bounds

The hypercube $Q_n$ has vertex set $\{0,1\}^n$; an edge joins strings differing in one coordinate. Write $f(n)=\operatorname{ex}(Q_n,C_4)$. The original conjecture is $f(n)/(n2^{n-1})\to1/2$. Fixed-dimensional constructions, restricted-class optima, and the asymptotic problem are separate targets.

| Quantity | Recorded result | Evidence boundary |
| --- | --- | --- |
| Asymptotic edge density | $1/2\le\pi_e(C_4)\le0.60318$ | The upper bound is Baber's theorem, not a pointwise bound in every dimension. |
| Q7 | $304\le f(7)\le305$ | Imported lower-bound certificate; [project-reviewed counting proof](q7-upper-bound-305.md). No priority claim or Lean formalization. |
| Q8 | $682\le f(8)\le704$ | Imported lower-bound certificate; 704 is the older averaging estimate, retained as a valid coarse bound, not asserted to be strongest. |
| Odd-square subclass | $g(6)=132,\ g(7)=304,\ g(8)=682$ | Restricted-class theorems in Minamoto v5; they do not imply $f=g$. |

There are $2n$ codimension-one subcubes, and each edge belongs to $n-1$ of them. Therefore $(n-1)f(n)\le2nf(n-1)$. The historical value $f(6)=132$ yields 308 and then 704. This project did not reprove the historical $f(6)$ upper bound during intake.

The original source review missed a stronger old Q7 bound: [Graham–Harary–Livingston–Stout (1993), Table 2](https://web.eecs.umich.edu/~qstout/pap/subcubeft.pdf) gives $\lambda(7,2)\ge142$, where $\lambda$ is the minimum number of deleted edges needed to destroy every square. Thus $f(7)\le448-142=306$. The project subsequently checked the definition and table. The bound 308 was valid but weaker.

The September 13 project argument further excludes 306 edges. The [complete counting proof](q7-upper-bound-305.md) is independent of an earlier internal audit of 11 SAT branches. Neither provides a 305-edge construction or proves 304 optimal. Its historical novelty remains unchecked.

## 1. Baber: an asymptotic upper bound

[Turán densities of hypercubes, 1201.3587v2](https://arxiv.org/html/1201.3587v2), particularly Sections 3–4 and Theorem 4.1, proves $\pi_e(C_4)\le0.60318$.

The method counts small subcubes and applies nonnegative quadratic constraints from flag algebras in a semidefinite program. Partially specified edge colors reduce the computational size. The paper identifies `PartialB.txt` and `PartialHypercubeEdgeDensityChecker` in its arXiv source attachments. The paper was saved and read, but that upper-bound certificate was not obtained and rerun during intake.

This is a computer-assisted upper-bound proof, separate from neural search for finite constructions.

## 2. Minamoto v5: finite constructions and a special class

[2603.29127v5](https://arxiv.org/html/2603.29127v5), dated August 28, 2026, studies the odd-square class: every square retains one or three edges, which automatically prevents C4s. Local-field identities and integer restrictions establish its optima in dimensions 6, 7, and 8.

Of the published 19,866 Q7 samples, 389 lie in that class. The 180 orbits classify that catalogue, not every possible 304-edge graph. The values 304 and 682 have earlier origins in the physics literature; v5 corrects attribution and the earlier Q8=680 conjecture.

Initial intake directly checked selected edge lists. The subsequent [corpus audit](../references/corpora/q7-304-orbits/README.md) checked all catalogue graphs and orbit witnesses and reran upstream canonicalization. This does not independently verify every theorem in the paper.

## 3. Minamoto's repository: search versus verification

Sources were pinned to [commit b94577f](https://github.com/minamominamoto/c4free-hypercube/tree/b94577fd5e06e62e1c6895b7e4d2b0abeaea411b). The intake includes the README, license, main verifier, reproduction entrypoint, and selected search and structural-check scripts.

Simulated annealing and delete-and-repair routines find candidates; edge-list checks and mathematical arguments support conclusions. The README's statement that arXiv was still at v4 was stale relative to the requested v5. The repository also reports an unclosed general Q6 ILP gap and problems in some recovered historical scripts. Available files do not by themselves demonstrate a complete reproduction of a historical search.

The project's [independent Q7/Q8 verifier](../references/baselines/86-verify.py) remains unchanged.

## 4. Wrona's repository: lifts and local ILP repair

Sources were pinned to [commit 7b8554b](https://github.com/rafalwronapl/erdos86-hypercube-c4/tree/7b8554bf3e7562a4bc1fb217757e709ba63c3e26).

Place C4-free graphs in the two slices of $Q_{n+1}$, align them by a coordinate permutation and bit flips, and choose vertical edges. For slices $G$ and $gG$, the selected vertical vertices must be independent in $G\cap gG$, giving $2|E(G)|+\alpha(G\cap gG)$ edges. Local integer programming then replaces several edges at once. Published parameters are not a complete search implementation.

The project wrote a [separate verifier](../scripts/verify_wrona_certificates.py), without importing upstream code. It checked file hashes, vertex ranges, cube edges, duplicates, every square, and common-neighbor pairs.

| Dimension | Certificate edges | Square faces checked | C4s |
| --- | ---: | ---: | ---: |
| 9 | 1505 | 4608 | 0 |
| 10 | 3304 | 11520 | 0 |
| 11 | 7164 | 28160 | 0 |
| 12 | 15372 | 67584 | 0 |
| 13 | 32856 | 159744 | 0 |
| 14 | 69909 | 372736 | 0 |
| 15 | 148126 | 860160 | 0 |

The [verification output](../artifacts/experiments/literature-intake-20260912/wrona-independent-verification.json) covers 1,504,512 square faces. Q9–Q11 exceed the BHN general formula used for comparison in that repository; Q12–Q15 do not. This is not a complete historical novelty audit.

The draft still uses the historical Q8=680 starting point. Conditional upper bounds assuming $f(8)=680$ cannot be used in the present project.

## 5. Erdős Problems forum

At the September 12 browser observation, [thread 86](https://www.erdosproblems.com/forum/thread/86) was OPEN, with three comments, zero proof claims, and zero proof expositions. The comments concerned Baber's constant, Wrona's certificates, and subcube averaging. Author names, dates, and direct links are preserved in the [original observation](../references/user/source-pack/forum-86-observation.md).

Comments and claims that an AI or another reader checked a result are not independent proofs. The seven higher-dimensional certificates have a separate basis for trust: the project's direct integer checks.

## Implications and workflow

- A 305-edge Q7 search must leave the odd-square class.
- Preserve structurally different parent graphs: the densest parent need not produce the best lift.
- The [lecture methods](ml-methods-from-lectures.md) motivated a GraphGPS-style candidate generator. Its [completed diagnostics](graphgps-diagnostic-suite-results.md) have not demonstrated a competitive search advantage.
- Preserve constraints, budgets, seeds, outputs, and stopping reasons. A failed search is not an optimality result.

Input records are in `references/MANIFEST.json`; downloaded versions and hashes are in `references/user/source-pack/DOWNLOAD_MANIFEST.json`. Iteris facts and tasks retain source-specific evidence boundaries. The label `reviewed` records those checks, not external peer review or formal certification. Further research is currently paused.
