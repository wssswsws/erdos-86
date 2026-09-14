# Six-run GraphGPS diagnostic results: Slurm 21929229

Reviewed through Omnissa Horizon on September 13, 2026. **All six runs completed normally. The best generated-and-repaired model graph has 294 edges; no model sample reached 300, 304, or 305.** Protecting reference weight showed a small positive signal, but did not establish a competitive search advantage over classical baselines.

## Execution and evidence

- Slurm: `COMPLETED`, exit code `0:0`, elapsed `02:04:42`, one A100: approximately **2.0783 GPU hours**.
- Suite status: `completed`; program time 7472.850 seconds. Slurm time includes additional startup overhead.
- Code: `51bfea0cccf024553a28dd43662082161bb3e6c8`.
- All runs completed 19,000 steps: **114,000 total training steps**.
- Each run produced 6,144 main-search samples and 1,280 stage-evaluation samples: **44,544 sampling events**, comprising 36,864 main and 7,680 evaluation events. Stage evaluation includes the untrained model; these are not asserted to be distinct graphs.
- Remote output is under the pinned worktree's `artifacts/experiments/slurm-21929229/diagnostics/`.

The local record `artifacts/experiments/slurm-21929229/observed-review/observed-completion.json` contains selected fields transcribed from the terminal, **not a complete transfer of the original reports**. That new local artifact is not included in this documentation-only publication. The best graph was transferred through an exact 448-bit encoding and independently rechecked locally. Full candidate streams and checkpoints have not yet been transferred and batch-audited.

## Paired-seed results

“Run maximum” includes main search and all stage evaluations. “Final mean” refers only to the fixed 256-sample evaluation at 19,000 steps.

| Seed | reference80 run maximum | legacy_topk run maximum | reference80 final repaired mean | legacy_topk final repaired mean | Mean difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8611 | 293 | 291 | 281.5352 | 280.3398 | +1.1953 |
| 8612 | 292 | 290 | 281.7305 | 279.5352 | +2.1953 |
| 8613 | 294 | 291 | 280.8594 | 280.7500 | +0.1094 |
| Mean across seeds | — | — | **281.3750** | **280.2083** | **+1.1667** |

Final raw-generation means averaged 277.3138 and 275.3060. The reference80 final-stage repaired maxima were 288, 290, and 290. The 294-edge graph came from an earlier stage; the final checkpoint is not reported to have generated it.

The report's overall best of 304 is an existing reference construction, not a model-generated result.

## After pretraining versus final evaluation

Held-out BCE below uses non-forced decisions only; smaller is better.

| Arm / seed | Post-pretraining holdout BCE | Final holdout BCE | Post-pretraining repaired mean | Final repaired mean |
| --- | ---: | ---: | ---: | ---: |
| reference80 / 8611 | 0.16737 | 0.15544 | 280.2188 | 281.5352 |
| reference80 / 8612 | 0.16192 | 0.16369 | 280.7227 | 281.7305 |
| reference80 / 8613 | 0.16774 | 0.16590 | 281.0195 | 280.8594 |
| legacy_topk / 8611 | 0.16288 | 0.17697 | 281.6914 | 280.3398 |
| legacy_topk / 8612 | 0.16905 | 0.17751 | 280.1641 | 279.5352 |
| legacy_topk / 8613 | 0.17201 | 0.17400 | 280.4414 | 280.7500 |

Across seeds, the reference80 repaired mean rose from 280.6536 to 281.3750, while legacy_topk fell from 280.7656 to 280.2083. Final holdout BCE averaged 0.16168 versus 0.17616.

This supports the limited interpretation that protecting high-quality reference sampling can reduce feedback deterioration. It is not improvement over pretraining on every seed, and three seeds provide limited statistical evidence. Pretraining outcomes already differed: the runs did not branch from one shared pretrained checkpoint. The observed differences cannot all be attributed to feedback weight. The holdout was reserved for these runs, while the earlier pilot had used all 180 orbits.

## Independently checked best graph

Source: `reference80-seed-8613/best-model.json`, labeled `repaired_model_sample`. Its three main-search round maxima were 294, 291, and 293. Thus the best appeared in the first round, after 10,000 pretraining steps and **before the first feedback update**. It cannot be credited to the 80% feedback policy.

The decoded local certificate `artifacts/experiments/slurm-21929229/observed-review/best-model-294.json` passed `erdos86_gps.verify.verify_edges`. The certificate is retained locally and is not included in this documentation-only publication:

- 294 valid Q7 edges, no duplicates.
- Zero C4s by all 672 square checks and by common-neighbor checks.
- Square-edge histogram: 1 empty, 105 with one edge, 39 with two edges, 527 with three edges.
- Degree histogram: 7 vertices of degree 3, 46 of degree 4, 67 of degree 5, and 8 of degree 6.

Its empty square shows that it is outside the odd-square subclass. That observation alone does not establish a route to 305.

## What the result means

The maximum increased from the earlier observed 293 to 294. However, a [simple deterministic construction](simple-293-baselines.md) already gives 294, and [random local search](random-293-baselines.md) repeatedly reaches 304 without a model or reference seed. The experiment therefore identifies a small training-distribution improvement, not a competitive construction-search method.

A useful next comparison would reuse saved checkpoints with the same stronger repairer and the same declared budget used for classical starting points. These results do not justify scaling training solely because the maximum reached 294.

The Iteris diagnostic task remains in `review`: GPU execution and final-summary checking are complete; full archive transfer and batch review are pending. No automatic retraining or resubmission is authorized by this report.
