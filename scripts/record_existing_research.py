"""Record the 2026-09-12 literature intake through Iteris's public APIs/CLI.

Usage (with the Iteris virtual-environment Python):
    python scripts/record_existing_research.py /path/to/source-pack
Only writes project records. Does not launch research agents or ML training.
"""
from pathlib import Path
import json
import subprocess
import sys

from iteris.events import record_event
from iteris.project import now_iso, write_json
from iteris.references import import_references
from iteris.tasks import upsert_pool_task

ROOT = Path(__file__).resolve().parents[1]
TASK = 'task-record-existing-research-20260912'
ART = 'artifacts/experiments/literature-intake-20260912'
PACK = 'references/user/source-pack'

FACTS = [
    ('baber-asymptotic-bound', 'literature_result',
     'Baber flag algebra: asymptotic C4 density at most 0.60318',
     'Baber 1201.3587v2 Theorem 4.1 gives pi_e(C4) <= 0.60318 via partial hypercubes and semidefinite flag algebra. This is an asymptotic density statement, not a bound valid at each finite dimension. The paper identifies PartialB.txt and PartialHypercubeEdgeDensityChecker in its arXiv source attachment. We read the paper but have not obtained or rerun that certificate.',
     f'{PACK}/baber-1201.3587v2.html; https://arxiv.org/html/1201.3587v2#S4', []),
    ('minamoto-odd-square-scope', 'literature_result',
     'Minamoto odd-square subclass: g6=132 g7=304 g8=682',
     'The v5 paper proves these optima for edge sets meeting every square in one or three edges. It does not prove unrestricted f(7)=304 or f(8)=682. Any 305-edge Q7 or 683-edge Q8 improvement must leave this subclass. The bound values have historical priority in earlier physics work, as explicitly acknowledged by the author. The complete upper-bound proofs have not been independently audited in this project.',
     f'{PACK}/minamoto-2603.29127v5.html; https://arxiv.org/html/2603.29127v5#S6', []),
    ('minamoto-catalogue-scope', 'literature_result',
     'Q7 catalogue: 19866 samples, 389 odd-square, 180 cube-symmetry orbits',
     'These numbers describe the released catalogue. They do not establish completeness among all 304-edge Q7 subgraphs. No full orbit computation was rerun here. The original Q6 ILP optimality and Q8=680 claims were withdrawn/corrected in v5; the repository README warning that arXiv is still v4 is stale.',
     f'{PACK}/minamoto/README.md; https://github.com/minamominamoto/c4free-hypercube/tree/b94577fd5e06e62e1c6895b7e4d2b0abeaea411b', []),
    ('q7-q8-certified-baselines', 'certificate_result',
     'Independent edge-list checks: Q7 304 and Q8 682 are C4-free',
     'The existing independent standard-library verifier checks every listed edge, uniqueness, every cube square, and common-neighbor pairs. Both published witnesses pass. The Q7 seed is not odd-square; the Q8 witness is odd-square. This verifies finite lower-bound witnesses, not optimality, novelty, or the original search process.',
     'references/baselines/86-verify.py; references/baselines/verification.json', []),
    ('finite-averaging-intervals', 'derived_result',
     'Finite averaging: 304<=f7<=308 and 682<=f8<=704',
     'Each edge belongs to n-1 of the 2n codimension-one subcubes, so (n-1)f(n)<=2nf(n-1). Conditional only on the cited established historical value f(6)=132, this yields f(7)<=308 and f(8)<=704. The counting argument is checked directly in docs/existing-research.md; the historical f(6) upper-bound proof was not rerun. The observation is already in forum post 8612 and is not new.',
     'docs/existing-research.md; https://www.erdosproblems.com/forum/thread/86#post-8612',
     ['q7-q8-certified-baselines']),
    ('wrona-product-lift', 'literature_method',
     'Wrona product lift via independent sets, followed by local ILP repair',
     'Place G and an automorphic copy gG in two slices. Cross-edge endpoints must form an independent set of G intersection gG; the optimal lift in this fixed setup has 2|E(G)|+alpha(G intersection gG) edges. Local C4-incidence ILP repair may leave the lift family. Published lift parameters are not a complete rerunnable search pipeline; a higher-edge parent need not give the best lift.',
     f'{PACK}/wrona/PAPER_V2.md; {PACK}/wrona/lift_params.json; https://github.com/rafalwronapl/erdos86-hypercube-c4/tree/7b8554bf3e7562a4bc1fb217757e709ba63c3e26', []),
    ('wrona-q9-q15-certified', 'certificate_result',
     'Independent Q9-Q15 audit: 1505 3304 7164 15372 32856 69909 148126',
     'All seven downloaded edge lists pass raw SHA-256 checks and an independently written integer-only checker using both exhaustive cube-face enumeration and common-neighbor pairs. Total faces checked: 1504512; no C4 found. This establishes those finite lower-bound witnesses. Only Q9-Q11 exceed the particular general BHN formula compared in the repository; no exhaustive novelty or optimality claim is made. This new audit supersedes the earlier local note that these seven files had not been rerun.',
     f'scripts/verify_wrona_certificates.py; {ART}/wrona-independent-verification.json; {PACK}/wrona/SHA256SUMS', []),
    ('forum-status-20260912', 'source_observation',
     'Forum snapshot 2026-09-12: OPEN, 3 comments, 0 proof claims',
     'Direct Chrome observation found OPEN, Comments(3), Proof claims(0), Proof expositions(0). Posts 1622,6595,8612 concern the Baber bound, Wrona certificates, and averaging. Post 8612 still uses Q8 lower bound 680; use 682 from v5 in current records. This is a dated site observation, not endorsement of comment correctness.',
     f'{PACK}/forum-86-observation.md; https://www.erdosproblems.com/forum/thread/86', []),
    ('lecture-wagner-cem', 'literature_method',
     'Lecture 5.2 pages 103-110: Wagner deep cross-entropy method',
     'Sequentially encode a graph as binary edge decisions, sample constructions from a policy network, keep elite scored trajectories, and train the network on those decisions. The primary paper is Wagner 2104.14516v1. The matching/spectral example gives a 19-vertex tree with two eight-leaf centers connected through an extra vertex; the conjecture had already been disproved before this smaller example. No CEM training was rerun here.',
     f'{PACK}/wagner-2104.14516.pdf; {PACK}/lecture-selected-pages.txt; docs/ml-methods-from-lectures.md; https://arxiv.org/abs/2104.14516', []),
    ('lecture-patternboost', 'literature_method',
     'Lecture 5.3 pages 110-116: PatternBoost global learning and local search',
     'PatternBoost alternates local improvement, training a Transformer on good constructions, sampling new candidates, and renewed local improvement. Its general 33-vertex C4-free example eventually attains 96 edges after about 116.5 million local searches in the reported experiment. Its Q6 81-edge counterexample preserves diameter 6 and addresses a different conjecture from Erdos86. We read sources; no model training or benchmark was reproduced.',
     f'{PACK}/patternboost-2411.00566.html; {PACK}/lecture-selected-pages.txt; https://arxiv.org/html/2411.00566#S3', []),
    ('patternboost-q7-proposal', 'research_proposal',
     'Proposed Q7 PatternBoost experiment with 448 edge decisions',
     'Proposed, not implemented: train/generate using only the 448 possible Q7 edges, apply C4 repair and local improvement, and compare against local search alone under equal total compute and evaluation budgets. Use independent exact verification for candidates and avoid restricting all samples to odd-square. Track diversity and deduplicate cube-symmetry copies. The 19866 sample catalogue has not yet been imported as a training set.',
     'docs/ml-methods-from-lectures.md',
     ['minamoto-odd-square-scope', 'minamoto-catalogue-scope', 'lecture-patternboost']),
]


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: record_existing_research.py /path/to/source-pack')
    pack = Path(sys.argv[1]).resolve()
    imported = import_references(ROOT, [pack])
    write_json(ROOT / ART / 'reference-import.json', imported)
    upsert_pool_task(ROOT, task_id=TASK, mode='foundation', status='done', priority=100,
                    objective='Record the five requested sources, identify ML graph methods in the lecture, and independently audit existing certificates.',
                    inputs=[f'{PACK}/DOWNLOAD_MANIFEST.json'],
                    expected_outputs=['docs/existing-research.md','docs/ml-methods-from-lectures.md',f'{ART}/wrona-independent-verification.json'],
                    notes=['Completed source intake and certificate checking; no new discovery claim and no research agents launched.'])
    results = []
    for slug, fact_type, summary, statement, evidence, predecessors in FACTS:
        fact_id = 'fact:erdos-86:' + slug
        command = [str(ROOT / 'scripts/iteris'), 'tool', 'memory', 'add-fact', str(ROOT),
                   '--source-task', TASK, '--fact-id', fact_id, '--fact-type', fact_type,
                   '--status', 'reviewed', '--claim-summary', summary, '--statement', statement,
                   '--notes', 'Evidence: ' + evidence + '\nReview scope: source audit by the assistant; for certificate results, independently executed integer checks. Not an Iteris agent-panel verified fact. No new result claimed.',
                   '--no-reindex', '--json']
        for predecessor in predecessors:
            command += ['--predecessor', 'fact:erdos-86:' + predecessor]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
        results.append(json.loads(result.stdout))
    subprocess.run([str(ROOT/'scripts/iteris'),'tool','memory','reindex',str(ROOT)],check=True)
    followups = [
        ('task-baber-certificate-audit','foundation','Obtain the original arXiv source attachment and assess/reproduce PartialB.txt with its exact checker.',
         [f'{PACK}/baber-1201.3587v2.html'],'artifacts/proofs/baber-certificate-audit.md'),
        ('task-q7-training-corpus-audit','foundation','Import the Q7 catalogue and orbit evidence; verify provenance and design a diverse training split without duplicate symmetry copies.',
         [f'{PACK}/minamoto/README.md','docs/existing-research.md'],'artifacts/experiments/q7-corpus-audit.md'),
        ('task-patternboost-q7-design','algorithm','Specify a bounded Q7 pilot with 448-edge encoding, fixed verifier, local-search baseline, and explicit compute accounting before training.',
         ['docs/ml-methods-from-lectures.md'],'artifacts/experiments/patternboost-pilot-design.md'),
    ]
    for task_id, mode, objective, inputs, output in followups:
        upsert_pool_task(ROOT, task_id=task_id, mode=mode, status='ready', priority=10,
                        objective=objective, dependencies=[TASK], inputs=inputs,
                        expected_outputs=[output], notes=['Recorded next task; not executed during the intake.'])
    record_event(ROOT,'literature_intake_completed',{'task_id':TASK,'facts_added':len(results),'source_manifest':'references/MANIFEST.json'})
    write_json(ROOT/ART/'fact-import.json',{'recorded_at':now_iso(),'facts':results})
    print(json.dumps({'imported_files':imported['total_files'],'facts_added':len(results),'followup_tasks':len(followups)}))


if __name__ == '__main__':
    main()
