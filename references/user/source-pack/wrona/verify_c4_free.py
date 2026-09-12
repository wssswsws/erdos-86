"""Verify C4-free edge-list certificates for hypercubes Q9 through Q15."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path


CERTIFICATES = [
    (9, 1505, "q9_edges_repair_from1503_iter2.json"),
    (10, 3304, "q10_edges_repair_from3302_iter5.json"),
    (11, 7164, "q11_edges_repair_from7160_probe_fast2.json"),
    (12, 15372, "q12_edges_repair_from15366_iter3.json"),
    (13, 32856, "q13_edges_repair_from32842_iter2.json"),
    (14, 69909, "q14_edges_repair_from69895_iter2.json"),
    (15, 148126, "q15_edges_repair_from148111_iter1.json"),
]


def load_edges(path: Path) -> list[tuple[int, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    edges = data.get("edges", data) if isinstance(data, dict) else data
    return [(int(u), int(v)) for u, v in edges]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_c4_free(n: int, edges: list[tuple[int, int]]) -> tuple[int, int]:
    edge_set: set[tuple[int, int]] = set()

    for u, v in edges:
        if not (0 <= u < 2**n and 0 <= v < 2**n):
            raise ValueError(f"invalid vertex for Q{n}: {(u, v)}")
        if (u ^ v).bit_count() != 1:
            raise ValueError(f"not a hypercube edge in Q{n}: {(u, v)}")
        if u == v:
            raise ValueError(f"loop edge: {(u, v)}")
        edge = (u, v) if u < v else (v, u)
        if edge in edge_set:
            raise ValueError(f"duplicate edge: {edge}")
        edge_set.add(edge)

    violations = 0
    cycles = 0
    for base in range(1 << n):
        for d1 in range(n):
            if (base >> d1) & 1:
                continue
            for d2 in range(d1 + 1, n):
                if (base >> d2) & 1:
                    continue
                a = base
                b = base | (1 << d1)
                c = base | (1 << d2)
                d = base | (1 << d1) | (1 << d2)
                square = [(a, b), (a, c), (b, d), (c, d)]
                cycles += 1
                if all((min(x, y), max(x, y)) in edge_set for x, y in square):
                    violations += 1

    return cycles, violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional certificate files. If omitted, verify the bundled list.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    selected = CERTIFICATES
    if args.files:
        selected = []
        for filename in args.files:
            stem = Path(filename).name
            try:
                n = int(stem.split("_edges", 1)[0].lstrip("q"))
            except Exception as exc:
                raise SystemExit(f"Cannot infer n from filename: {filename}") from exc
            selected.append((n, None, filename))

    t0 = time.time()
    total_files = 0
    for n, expected_edges, filename in selected:
        path = root / filename
        edges = load_edges(path)
        if expected_edges is not None and len(edges) != expected_edges:
            raise SystemExit(
                f"{filename}: expected {expected_edges} edges, found {len(edges)}"
            )
        cycles, violations = verify_c4_free(n, edges)
        digest = sha256(path)
        print(
            f"{path.name}: n={n}, edges={len(edges)}, cycles={cycles}, "
            f"violations={violations}, sha256={digest}"
        )
        if violations:
            raise SystemExit(f"{filename}: certificate is not C4-free")
        total_files += 1

    print(f"TOTAL files={total_files}, elapsed_seconds={time.time() - t0:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
