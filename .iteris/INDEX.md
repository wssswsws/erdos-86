---json
{
  "schema_version": "iteris.project_index.v0",
  "updated_at": "2026-09-12T22:24:05.366652Z",
  "project_id": "erdos-86",
  "project_path": "/Users/wsss/Documents/Math-other/Mathathon/project/erdos-86",
  "title": "erdos-86",
  "role": "single",
  "family_root": null,
  "node_id": "erdos-86",
  "source_file": "sources/erdos-86.tex",
  "target_artifact": "results/erdos-86/answer.md",
  "evolve": {
    "initialized": false,
    "state_file": "generalize/EVOLVE.json",
    "goal": null,
    "supervisor_session": "iteris-evolve-erdos-86"
  },
  "pointers": {
    "status": "STATUS.md",
    "operator": "docs/OPERATOR.md",
    "task_pool": "tasks/TASK_POOL.json",
    "facts_index": "memory/facts/FACT_INDEX.jsonl",
    "reports": "reports",
    "report_index": "reports/REPORT_INDEX.jsonl",
    "rolling_report": ".iteris/supervision/REPORT.md",
    "family_memory": "memory/family/FAMILY_INDEX.jsonl"
  },
  "commands": {
    "start_worker": "iteris run",
    "start_evolve": "iteris evolve run",
    "check_status": "iteris status --json",
    "check_family": "iteris evolve status --json",
    "observe_ui": "iteris dashboard",
    "recover": "iteris recover",
    "monitor": "iteris monitor",
    "report_status": "iteris report status",
    "report_new": "iteris report new --layout iteris-report --profile theory",
    "worker_session": "iteris-erdos-86"
  }
}
---
