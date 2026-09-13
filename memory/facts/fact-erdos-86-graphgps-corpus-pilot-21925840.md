---
fact_id: fact:erdos-86:graphgps-corpus-pilot-21925840
problem_id: erdos-86
source_project: erdos-86
source_task: task-graphgps-q7-gpu-pilot
predecessors: []
status: reviewed
fact_type: computational_result
review_level: none
claim_policy: stable_claim
claim_summary: "180 轨道语料单 A100 试验完成：原始生成最高 286、修复最高 290，未改进初始 304；全部 12,288 个保存的修复候选复核通过。"
verification: null
---

## statement

作业 21925840 使用代码 46dd29801eef68c54151241805462fe4eb83977e 与经审核的 180 个 Q7 304 边轨道代表，单 A100 80GB、seed 8601。Slurm COMPLETED、ExitCode 0:0，19 分 39 秒（0.3275 GPU 小时）；11,000 训练步与 3×4,096 样本全部完成。原始生成各轮最高 286/285/281，修复后最高 290/288/287；最终 best=304 且属于初始训练池，未找到 305。本地独立验证器复核全部 12,288 个保存的修复后边表与最终 best 均合法，候选的精确标号均不同。初始固定训练池的前/后 500 步平均 loss 为 0.3883/0.1550，非强制位置 BCE 为 0.4585/0.1816。第一轮精英回填后训练池含 180 张 304 边图和 332 张 283–290 边图，均匀采样时 304 占比降至 35.16%；这种变化与 loss 跃升及后续原始生成质量下降同时发生，尚未通过对照实验确定因果。

## notes

证据：docs/corpus-pilot-21925840-results.md；artifacts/experiments/slurm-21925840/pilot-seed-8601/{report.json,candidates.jsonl.gz,sacct.txt,git-revision.txt}；analysis/{analysis.json,best-model-repaired.json,diagnostics.png}。复核入口 scripts/analyze_graphgps_pilot.py；源码、语料与审核文件哈希核对一致。仅保存修复后候选的完整边表，原始生成与配对基线不具备逐图本地复核条件。基线从 304 图出发且只匹配局部扰动次数，不是相同总算力的公平排名。未做新候选轨道去重、独立留出泛化评价、Lean 形式化或 Iteris 代理面板审核；reviewed 表示本次程序复核与来源核对。云端 checkpoint 保留且未回传 GitHub。
