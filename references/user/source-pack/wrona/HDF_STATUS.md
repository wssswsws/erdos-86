# HDF Status

## Classification

```text
truth_type: hard_truth
maturity_level: public_project
claim_state: finite_certificate
spinout_status: successful
```

## Why This Is HDF-Compatible

This project follows the Hard Discovery Factory pattern:

```text
search space -> candidate generator -> evaluator/verifier -> baseline -> certificate
```

Mapping:

- `search space`: C4-free subgraphs of finite hypercubes.
- `candidate generator`: product lifts via hypercube automorphisms plus local
  ILP repair on C4-incidence neighborhoods.
- `evaluator/verifier`: direct 4-cycle enumeration and sparse cherry-counting
  verifier.
- `baseline`: Minamo Minamoto Q7/Q8 constructions and the commonly cited BHN
  general estimate.
- `certificate`: explicit JSON edge lists, SHA-256 hashes, verifier logs and
  independent cross-check notes.

## HDF Lesson

The project is a good public example of narrow claim discipline:

- publish finite certificates;
- provide standalone verifiers;
- disclose AI assistance;
- ask for verification and prior-art pointers;
- avoid claiming a solution, optimality, or broad novelty.

