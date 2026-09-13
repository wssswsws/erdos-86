"""Fixed hypercube variable/factor topology; independent of neural networks."""
from dataclasses import dataclass
from itertools import combinations


@dataclass
class Cube:
    n: int
    edges: list[tuple[int, int]]
    faces: list[tuple[int, ...]]
    edge_faces: list[list[int]]

    @classmethod
    def build(cls, n=7):
        if not 2 <= n <= 8:
            raise ValueError('Supported smoke/research dimensions: 2..8')
        edges = [(u, u ^ (1 << i)) for u in range(1 << n)
                 for i in range(n) if not u & (1 << i)]
        index = {edge: i for i, edge in enumerate(edges)}
        faces = []
        for i, j in combinations(range(n), 2):
            for u in range(1 << n):
                if u & ((1 << i) | (1 << j)):
                    continue
                v = [u, u ^ (1 << i), u ^ (1 << i) ^ (1 << j), u ^ (1 << j)]
                faces.append(tuple(index[tuple(sorted((v[k], v[(k + 1) % 4])))] for k in range(4)))
        edge_faces = [[] for _ in edges]
        for f, face in enumerate(faces):
            for e in face:
                edge_faces[e].append(f)
        return cls(n, edges, faces, edge_faces)

    def encode(self, edges):
        index = {edge: i for i, edge in enumerate(self.edges)}
        bits = [0] * len(index)
        for edge in edges:
            e = index[tuple(sorted(edge))]
            if bits[e]:
                raise ValueError('Duplicate edge')
            bits[e] = 1
        return bits

    def decode(self, bits):
        if len(bits) != len(self.edges) or any(x not in (0, 1) for x in bits):
            raise ValueError('Expected a binary edge vector')
        return [list(e) for e, keep in zip(self.edges, bits) if keep]

    def relabel(self, bits, permutation, flip):
        """Coordinate permutation followed by XOR; a true cube automorphism."""
        if sorted(permutation) != list(range(self.n)) or not 0 <= flip < 1 << self.n:
            raise ValueError('Invalid cube automorphism')
        def transform(u):
            return sum(((u >> i) & 1) << permutation[i] for i in range(self.n)) ^ flip
        return self.encode([(transform(u), transform(v)) for u, v in self.decode(bits)])
