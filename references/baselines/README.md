# Known construction certificates

These files were imported from the September 12, 2026 research checks. They reproduce known constructions rather than establish new lower bounds.

Upstream: [c4free-hypercube](https://github.com/minamominamoto/c4free-hypercube), pinned to `b94577fd5e06e62e1c6895b7e4d2b0abeaea411b`. Paper: [2603.29127v5](https://arxiv.org/html/2603.29127v5).

| File | Construction | SHA-256 of original bytes |
| --- | --- | --- |
| `86-selected_edges_best.json` | Q7, 304 edges; outside the odd-square class | `8e3c8d23643d2d34c493acd95013faea6f98c0a0f9db20ae77eee1a698d0980c` |
| `86-q8_odd_square_682.json` | Q8, 682 edges; in the odd-square class | `7243042c407dbf2e389bc13d0320a7d2fa1ae94db83caf5068a0d77bdb082258` |

`86-ODDSQUARE_BRIDGE_SHA256SUMS.txt` is the upstream checksum list. `86-verify.py` is the independently written standard-library verifier used in the earlier review. It checks common neighbors and all squares. Do not run with `python -O`, which disables its assertions.

From the repository root:

```bash
python3 references/baselines/86-verify.py
```

`verification.json` records the initialization checks. Validating these edge lists does not prove unrestricted Q7/Q8 optimality, and the certificates are not new project constructions.
