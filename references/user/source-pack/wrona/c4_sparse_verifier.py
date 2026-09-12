#!/usr/bin/env python3
"""
c4_sparse_verifier.py
A dependency-free, *sparse* verifier for C4-free subgraph certificates of the
hypercube Q_n. It scales to large n (tested through Q15, 32,768 vertices),
where dense adjacency-matrix methods can run
out of time/memory.

Method (independent of an enumerate-all-C4-of-Q_n approach):
  C4-free  <=>  no unordered vertex pair has >= 2 common neighbours
           <=>  no "cherry" (length-2 path) endpoint-pair occurs as a cherry
                centred at two different vertices.
Cost is O(sum_v deg(v)^2), which is small for these near-degree-n graphs.
On failure an explicit 4-cycle witness (a, b, w1, w2) is printed.

Checks performed:
  1. every endpoint is a valid Q_n vertex (0 <= x < 2**n)
  2. every edge is a genuine hypercube edge (Hamming distance exactly 1), no loops
  3. no duplicate edges
  4. edge count == --expected-edges
  5. C4-free (cherry counting)
Plus support size and degree range. Exit 0 = all pass, 1 = failure (CI-friendly).

Input formats accepted (auto-detected):
  * a whole-file JSON object {"n":.., "num_edges":.., "edges": [[u,v],...]}
  * a whole-file JSON array [[u,v],...]
  * JSONL with one such object/array per line; use --solution-index to pick one
Stdlib only. Usage:
  python3 c4_sparse_verifier.py FILE --n N --expected-edges E [--solution-index i]
"""
import argparse
import json
import sys
from collections import defaultdict


def extract_edges(obj):
    if isinstance(obj, dict):
        return obj["edges"]
    return obj  # already a list of [u, v]


def load(path, index):
    lines = [ln for ln in open(path) if ln.strip() and not ln.lstrip().startswith("#")]
    # Try whole-file parse first (covers pretty-printed multi-line JSON object/array).
    try:
        obj = json.loads("".join(lines))
        objs = obj if (isinstance(obj, list) and obj and isinstance(obj[0], dict)) else [obj]
    except json.JSONDecodeError:
        objs = [json.loads(ln) for ln in lines]  # JSONL
    if len(objs) > 1 and index is None:
        index = 0
    chosen = objs[index if index is not None else 0]
    return extract_edges(chosen), len(objs)


def verify(n, edges, expected):
    N = 1 << n
    seen_edges = set()
    bad_range = bad_dist = loops = dups = 0
    adj = defaultdict(set)
    for u, v in edges:
        u, v = int(u), int(v)
        if not (0 <= u < N and 0 <= v < N):
            bad_range += 1
            continue
        if u == v:
            loops += 1
            continue
        if (u ^ v).bit_count() != 1:
            bad_dist += 1
            continue
        e = (u, v) if u < v else (v, u)
        if e in seen_edges:
            dups += 1
            continue
        seen_edges.add(e)
        adj[u].add(v)
        adj[v].add(u)

    cherry_center = {}
    witness = None
    for c in adj:
        nb = sorted(adj[c])
        L = len(nb)
        for i in range(L):
            a = nb[i]
            for j in range(i + 1, L):
                key = (a, nb[j])
                if key in cherry_center:
                    witness = (a, nb[j], cherry_center[key], c)
                    break
                cherry_center[key] = c
            if witness:
                break
        if witness:
            break

    degs = [len(s) for s in adj.values()]
    return {
        "unique_edges": len(seen_edges),
        "count_ok": len(seen_edges) == expected,
        "bad_range": bad_range,
        "bad_dist": bad_dist,
        "loops": loops,
        "dups": dups,
        "c4_free": witness is None,
        "witness": witness,
        "support": len(adj),
        "deg_min": min(degs) if degs else 0,
        "deg_max": max(degs) if degs else 0,
    }


def main():
    ap = argparse.ArgumentParser(description="Sparse C4-free verifier for Q_n certificates.")
    ap.add_argument("file")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--expected-edges", type=int, required=True)
    ap.add_argument("--solution-index", type=int, default=None,
                    help="index of the solution to verify in a multi-solution file (default 0)")
    args = ap.parse_args()

    edges, nsol = load(args.file, args.solution_index)
    r = verify(args.n, edges, args.expected_edges)
    idx = args.solution_index if args.solution_index is not None else 0

    print("file          : {}".format(args.file))
    print("n             : {}".format(args.n))
    print("solutions     : {} (verifying index {})".format(nsol, idx))
    print("unique edges  : {} (== {}: {})".format(r["unique_edges"], args.expected_edges, r["count_ok"]))
    print("invalid edges : range={} dist={} loop={} dup={}".format(r["bad_range"], r["bad_dist"], r["loops"], r["dups"]))
    print("C4-free       : {}".format(r["c4_free"]) + ("" if r["c4_free"] else "  4-cycle witness {}".format(r["witness"])))
    print("support       : {} / {} vertices".format(r["support"], 1 << args.n))
    print("degree range  : {}..{}".format(r["deg_min"], r["deg_max"]))

    ok = (r["c4_free"] and r["count_ok"] and r["bad_range"] == 0
          and r["bad_dist"] == 0 and r["loops"] == 0 and r["dups"] == 0)
    print("\n{}".format("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
