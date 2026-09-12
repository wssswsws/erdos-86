# Reproduce

## Requirements

- Python 3.11+ is recommended.
- No external Python packages are required for the main verifier.

## Verify All Certificates

From the repository root:

```bash
python verify_c4_free.py
```

Expected summary:

```text
q9_edges_repair_from1503_iter2.json: n=9, edges=1505, cycles=4608, violations=0
q10_edges_repair_from3302_iter5.json: n=10, edges=3304, cycles=11520, violations=0
q11_edges_repair_from7160_probe_fast2.json: n=11, edges=7164, cycles=28160, violations=0
q12_edges_repair_from15366_iter3.json: n=12, edges=15372, cycles=67584, violations=0
q13_edges_repair_from32842_iter2.json: n=13, edges=32856, cycles=159744, violations=0
q14_edges_repair_from69895_iter2.json: n=14, edges=69909, cycles=372736, violations=0
q15_edges_repair_from148111_iter1.json: n=15, edges=148126, cycles=860160, violations=0
```

## Check Hashes

On Linux/macOS:

```bash
sha256sum -c SHA256SUMS
```

On Windows PowerShell:

```powershell
Get-Content .\SHA256SUMS | ForEach-Object {
  $parts = $_ -split '\s+'
  $expected = $parts[0]
  $file = $parts[-1]
  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash.ToLower()
  if ($actual -ne $expected) {
    throw "Hash mismatch for $file"
  }
  "$file OK"
}
```

## Independent Sparse Check

The repository also includes a sparse cherry-counting verifier. Example for the
`Q11` certificate:

```bash
python c4_sparse_verifier.py q11_edges_repair_from7160_probe_fast2.json --n 11 --expected-edges 7164
```

See `independent_crosscheck.md` for the independent certificate-level check.

## Reproduction Standard

A successful reproduction should confirm:

- all hashes match;
- all listed edges are valid hypercube edges;
- there are no loops or duplicate edges;
- the direct verifier reports zero C4 violations;
- the sparse verifier reports no pair of vertices with two common neighbours.
