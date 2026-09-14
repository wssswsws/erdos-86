# A counting proof that a C4-free subgraph of Q7 has at most 305 edges

Project review date: September 13, 2026. This English presentation follows the internally reviewed facet-congruence argument. It is a mathematical argument, independent of the project's earlier SAT exclusions. It has not been externally peer reviewed or formalized in Lean, and its historical novelty has not been established.

Together with the [known 304-edge certificate](../references/baselines/README.md), it gives

$$304\le\operatorname{ex}(Q_7,C_4)\le305.$$

There is no 305-edge construction here and no proof that 304 is optimal. The original asymptotic Erdős problem remains separate.

## 1. Count three-edge stars

Let $G\subseteq Q_7$ be C4-free, with $m$ edges. Fix either side $V$ of the cube's bipartition. It contains 64 vertices, and $\sum_{v\in V}d(v)=m$.

Within any three-dimensional coordinate face, at most one vertex of $V$ can have all three incident face edges present. Indeed, any two distinct same-side vertices of a 3-cube are at distance two; if both were such centers, their two common neighbors would complete a C4.

There are $\binom73 2^4=560$ three-dimensional faces. Every choice of three edges at a vertex specifies one such face, so

$$T=\sum_{v\in V}\binom{d(v)}3\le560.$$

Define $k(d)=\binom d3-6d+20$. For $d=0,\ldots,7$, its values are

$$20,14,8,3,0,0,4,13.$$

They are nonnegative. Consequently $6m-1280\le560$, giving $m\le306$, and

$$K=\sum_{v\in V}k(d(v))\le1840-6m.$$

Call a three-dimensional face **uncovered on side $V$** when it has no such star center. Its total count is $\delta=560-T$.

## 2. Count uncovered faces inside six-dimensional facets

Suppose all degrees on $V$ lie between 3 and 6. Let $b$ and $c$ count its degree-3 and degree-6 vertices. Then

$$\delta=1840-6m-3b-4c.$$

For each of the 14 six-dimensional coordinate facets $F$, let $\delta_F$ count its uncovered three-dimensional faces. Let $a_F$ and $c_F$ count the vertices of $V\cap F$ whose degrees **within $F$** are 2 and 6. There are 32 vertices in $V\cap F$, and their local degrees lie between 2 and 6. Hence

$$\delta_F=160-\sum_{v\in V\cap F}\binom{d_F(v)}3\ge0.$$

For local degrees $2,3,4,5,6$, the binomial coefficients modulo 3 are respectively $0,1,1,1,2$. Therefore

$$\delta_F\equiv2+a_F-c_F\pmod3.$$

It follows that

$$\delta_F\ge2-2a_F-c_F.$$

Only $(a_F,c_F)=(0,0)$ and $(0,1)$ need the congruence: it forces $\delta_F\ge2$ and $\delta_F\ge1$, respectively. In every other case, the right side is nonpositive.

Every three-dimensional face belongs to four six-dimensional facets. A global degree-3 vertex has local degree 2 in exactly three facets; a global degree-6 vertex has local degree 6 in exactly one facet. Thus

$$\sum_F\delta_F=4\delta,\qquad\sum_Fa_F=3b,\qquad\sum_Fc_F=c.$$

Summing the inequality over the 14 facets yields

$$4(1840-6m-3b-4c)\ge28-6b-c,$$

or equivalently

$$\boxed{24m+6b+15c\le7332.}$$

## 3. Exclude 306 edges

If $m=306$, the first section gives $K\le4$. The table of $k(d)$ excludes degrees 0, 1, 2, and 7. Thus the facet inequality applies on either side. But

$$24\cdot306=7344>7332,$$

a contradiction. Since $m\le306$ was already established, every C4-free subgraph of Q7 has at most 305 edges.

## 4. Restrict the degrees of a hypothetical 305-edge graph

If $m=305$, then $K\le10$, which first excludes degrees 0, 1, and 7. If one bipartition side contains a degree-2 vertex, it is unique and every other vertex on that side has degree 4 or 5: a second degree-2 vertex, or even one degree-3 or degree-6 vertex, would exceed the $K$ budget. In this case $\delta=2$.

Let $\delta_i$ count the uncovered three-dimensional faces containing direction $i$. Counting the 240 three-dimensional faces containing that direction by their star centers gives

$$240-\delta_i=\sum_{\substack{v\in V:\text{the direction-}i\text{ edge at }v\text{ is present}}}\binom{d(v)-1}{2}.$$

For degrees 2, 4, and 5, the contributions are 0, 3, and 6. Thus each $\delta_i$ is divisible by 3. Since $0\le\delta_i\le\delta=2$, they all vanish. This contradicts $\sum_i\delta_i=3\delta=6$. Neither side can contain a degree-2 vertex.

The facet inequality now applies. Substituting $m=305$ gives

$$6b+15c\le12,\qquad 2b+5c\le4.$$

Therefore $c=0$ and $b\le2$ on each side. **Every vertex has degree 3, 4, or 5, with at most two degree-3 vertices on either bipartition side.**

## Review scope

The original project review independently rederived this chain and checked the small arithmetic tables and cube incidences. Those finite checks assist the proof; the argument above supplies the general coverage.

An earlier, separate project audit reconstructed 11 SAT formulas and replayed 526,763 RUP additions to exclude 306 edges. The direct proof here does not depend on those solver outputs, a classification of Q5/Q6 extremal graphs, or restrictions to an odd-square family.

For the historical distinction between the averaging bound 308 and the earlier published bound 306, see the [research overview](existing-research.md). Further structural claims and unfinished searches do not acquire reviewed status merely by being combined with this argument.
