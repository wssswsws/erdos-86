# Q7 random-search baselines without learning or reference constructions

**293 edges is within the reach of inexpensive random search and bounded local repair.** These searches use only generated Q7 topology and RNG seeds. They do not read a model, corpus, candidate certificate, or known 304-edge construction, and do not impose odd-square or signed-spin structure.

The first random-search start reached 304. A separate prespecified batch of 100 starts, each limited to 5,000 moves, exceeded 293 every time and reached 304 in 14 cases. Simple deletion followed by greedy refill also reached 304. These reproduce an existing edge-count level; failure to reach 305 proves no upper bound.

## Fixed-budget results

Each sample is the best graph reached from a **fresh random greedy start within its move budget**. The 256-, 1024-, and 4096-move force experiments share starts; the 5000-move batch uses different seeds.

| Method | Starts × moves | Mean | Median | Range | At least 294 | At least 300 | Equal to 304 | Total process CPU sec |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Original Python empty-start baseline | 6144 × 16 | 273.926 | 274 | 265–283 | 0 | 0 | 0 | 52.216 |
| Forced-edge exchange + greedy | 6144 × 16 | 269.930 | 270 | 259–281 | 0 | 0 | 0 | 0.741 |
| Forced-edge exchange + greedy | 512 × 256 | 288.639 | 289 | 283–295 | 5 | 0 | 0 | 0.807 |
| Forced-edge exchange + greedy | 512 × 1024 | 294.119 | 294 | 290–303 | 320 | 2 | 0 | 2.984 |
| Forced-edge exchange + greedy | 512 × 4096 | 298.098 | 297 | 295–304 | 512 | 97 | 62 | 11.869 |
| Forced-edge exchange, separate seed batch | 100 × 5000 | 298.450 | 298 | 295–304 | 100 | 22 | 14 | 2.915 |
| Random/face-region deletion + greedy | 512 × 4096 | 296.561 | 296 | 292–304 | 471 | 69 | 2 | 13.256 |

Sixteen force moves alone are weaker than the original 16 larger deletion kicks. The improvement depends on search neighborhood and depth; the empty-start 16-kick baseline is not an upper limit on classical random methods.

The exact Python baseline calls `erdos86_gps.search.local_search` from an empty graph with `kicks=16`, deletion range 8–24, `kick_mode='mixed'`, and temperatures 2.0 to 0.25. Its 6,144 seeds are 932930000–932936143. Unrepaired greedy starts had mean 262.3875 and maximum 275; repair reached 283 three times.

C++ uses `std::mt19937_64`, with start $i$ seeded by `base_seed + i * 104729`. The 16/256/1024/4096-move and deletion experiments use base seed 932932001; the 100-start, 5000-move batch uses 932933001.

## Algorithms

Both C++ methods shuffle all 448 edges and greedily add legal edges from the empty graph to obtain a maximal C4-free start. Each local move is followed by a random-order greedy refill. Every restart retains its best certificate separately.

**`force_ils`:** with 95% probability, sample 1–12 missing edges and choose one blocked by the fewest three-edge square faces. Delete one existing edge from each blocking face, add the chosen edge, and refill. Within a blocking face, deletion maximizes `U[0,1) + b * number_of_incident_three_edge_faces`, with `b` independently chosen as 0 or 0.4. The other 5% of moves delete 4–16 edges, half using a random region and half a region grown through shared squares, before refill.

Accept a nondecreasing edge count; otherwise accept with probability `exp(delta/T)`, where `T = 0.5 - 0.45 * ((step mod 50000) / 49999)`. Each restart resets this schedule. A 5000-move run only cools to approximately 0.455. After 20,000 moves without improvement, longer runs periodically return to their best graph every 10,000 moves; short experiments do not reach that condition.

**`mixed_ils`:** delete 2–10 edges with 95% probability, or 12–28 with 5% probability. Choose equally between global random edges and a shared-square region, then greedily refill. Use `T = 0.8 - 0.65 * ((step mod 50000) / 49999)` with the same acceptance and best-retention rules. It never explicitly selects a missing edge to force in.

Both maintain only the condition that every square has at most three selected edges. Neither initializes from an existing good construction.

## First hit and the separate 120-second exploration

The first run used base seed 932931001, a prespecified 120 CPU-second limit, and at most 50,000 moves per start. Its first start reached:

| Edge count | Move | In-run CPU sec | In-run wall sec |
| --- | ---: | ---: | ---: |
| 293 | 1218 | 0.009714 | 0.009902 |
| 294 | 1226 | 0.009924 | 0.010111 |
| 300 | 2580 | 0.016774 | 0.017331 |
| 304 | 3450 | 0.020566 | 0.021123 |

The local certificate `artifacts/experiments/random-293-baselines/force-ils-120s/best-304.json` and accompanying events retain the trajectory. Twenty milliseconds excludes compilation, startup, and external verification and is not a typical-hit-time guarantee. A separate project rerun recompiled the source and reproduced the identical 304-edge graph at move 3450 with the same seed.

The longer batch took 120.000579 CPU seconds: 639 complete 50,000-move starts and 12,800 moves of a 640th start, totaling 31,962,800 moves. Best-per-start mean was 303.8125, median 304, range 299–304; 610 starts reached 304. None reached 305. This exploration is separate from the fixed small-budget table.

The deletion-only method first reached 294 on start one at move 1209. It first reached 304 on start 80, after 326,734 cumulative moves and 2.221949 CPU seconds.

## Verification and timing boundaries

All 239 saved run-record improvements were checked by both `erdos86_gps/verify.py` and `research/shared/verify_candidate.py`. The latter independently enumerates all 672 squares and common-neighbor pairs and checks endpoint ranges, cube edges, duplicates, and actual edge count. Per-run `independent-verification.json` files record success. Its edge-list SHA-256 normalizes the labeling; it is not a symmetry-orbit certificate.

The Python reference also internally checked all 6,144 final graphs. C++ maintains square counts and recomputes consistency when saving a new record. It does not use the Python verifier to guide search.

The recorded environment was macOS 26.3 / arm64, Apple clang 17.0.0, compiled with `-O3 -std=c++17`; searches were single-threaded. C++ timing begins after topology construction and includes search and progress/certificate writes, but excludes compilation, process startup, external Python checks, and analysis. Python baseline time also includes internal verification and an extra greedy pass for raw-score statistics. These timings do not support a rigorous Python/C++ or CPU/GPU speed ratio.

## Evidence and publication scope

The local research workspace contains the C++ search in `scripts/random_293_baselines.cpp`, its Python runner in `scripts/random_293_baselines.py`, and the independent checker in `research/shared/verify_candidate.py`. The aggregate record at `artifacts/experiments/random-293-baselines/summary.json` binds source hashes, compiler details, parameters, and score distributions.

These additional sources and experiment archives are **not included in this documentation-only publication**. The algorithms and observed results are described above, but a reader cannot reproduce the exact recorded runs from the published repository alone. Fixed-step replication also depends on compiler and standard-library behavior; runtime varies by machine.

The existing experiments changed no training algorithm and used no GPU. They show that the previously weak empty-start comparison cannot establish a competitive advantage for GraphGPS. Further project computation remains paused.
