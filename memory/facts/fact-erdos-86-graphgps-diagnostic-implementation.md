---
fact_id: fact:erdos-86:graphgps-diagnostic-implementation
problem_id: erdos-86
source_project: erdos-86
source_task: task-graphgps-q7-pilot-diagnostics
predecessors: []
status: reviewed
fact_type: implementation_result
review_level: none
claim_policy: stable_claim
claim_summary: "参考池80%权重、按轨道固定评测和允许暂时退步的搜索已实现；21项测试与两组CPU smoke通过。"
verification: null
---

## statement

GraphGPS局部消息传递与全局注意力架构保持不变。新实验对照reference80与legacy_topk，使用相同144训练轨道和36固定验证轨道；禁止生成304+图回填可防止任何验证轨道的对称副本进入在线训练。每阶段评测独立于训练RNG，并保存未训练及阶段checkpoint、原始/修复/两类基线完整边表。搜索混合随机和共享方形区域扰动，允许按退火概率接受修复后的边数下降，但始终单独保留并验证最好证书。本机21项测试通过，两组CPU smoke各完成3训练步、2个主搜索样本、6个阶段样本；保存的40份边表复验通过，配对初始化权重与固定评测样本哈希一致。

## notes

证据：docs/graphgps-pilot-diagnostic-plan.md；artifacts/experiments/diagnostics-preparation/{tests.xml,validation.json,cpu-smoke-final/}。验证集是本轮模型未训练轨道，先前pilot曾用过全部180轨道，不能称历史盲测。本事实不声称CUDA新路径已实测、学习性能改进、找到305或完成新轨道审核；GPU执行由task-graphgps-q7-diagnostic-suite另行记录。
