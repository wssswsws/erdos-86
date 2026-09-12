# Claim Boundary

This repository makes a narrow certificate-level claim.

## Claimed

- The bundled JSON files are explicit edge-list certificates for C4-free
  subgraphs of `Q9` through `Q15`.
- The listed edge counts are certified by the included verifiers.
- The direct verifier exhaustively enumerates all 4-cycles in the relevant
  hypercube and reports zero violations for each bundled certificate.
- The sparse cherry-counting verifier gives an independent certificate-level
  cross-check.
- The `Q9`, `Q10`, and `Q11` certificates slightly exceed the commonly cited
  Brass-Harborth-Nienborg general estimate
  `0.5 * (n + 0.9 * sqrt(n)) * 2^(n-1)`.

## Not Claimed

- This is not a solution of Erdos Problems #86.
- This is not an optimality claim for any `n >= 7`.
- This is not a novelty claim about all possible unpublished computations.
- The `Q12` through `Q15` certificates are not claimed to improve the cited BHN
  general estimate; they are included as explicit witnesses and as part of the
  construction chain.
- The finite certificates do not contradict the asymptotic conjecture.

## How To Evaluate The Claim

Evaluate the project by:

1. Checking the SHA-256 hashes in `SHA256SUMS`.
2. Running `python verify_c4_free.py`.
3. Running or inspecting `c4_sparse_verifier.py`.
4. Comparing the output with `VERIFY_ALL_CERTIFICATES.log`.
5. Checking whether earlier explicit published or unpublished certificates are
   known for these dimensions.

## Public Verification Request

The result was posted on the Erdos Problems forum as a certificate-verification
request:

https://www.erdosproblems.com/forum/thread/86

