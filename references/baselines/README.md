# 已知构造基准

这些文件从本地 2026-09-12 研究核查材料导入，属于已知构造的复现证据。

上游仓库：<https://github.com/minamominamoto/c4free-hypercube>。
数据核查时的固定提交：`b94577fd5e06e62e1c6895b7e4d2b0abeaea411b`。
论文：<https://arxiv.org/html/2603.29127v5>。

| 本地文件 | 内容 | 原始字节 SHA-256 |
| --- | --- | --- |
| `86-selected_edges_best.json` | Q7，304 边；不属于 odd-square 类 | `8e3c8d23643d2d34c493acd95013faea6f98c0a0f9db20ae77eee1a698d0980c` |
| `86-q8_odd_square_682.json` | Q8，682 边；属于 odd-square 类 | `7243042c407dbf2e389bc13d0320a7d2fa1ae94db83caf5068a0d77bdb082258` |

`86-ODDSQUARE_BRIDGE_SHA256SUMS.txt` 是上游清单。
`86-verify.py` 是前期核查时独立编写的标准库验证器；两个构造依次通过公共邻居检查及所有方形枚举。不要用 `python -O` 运行。

在仓库根目录复核：

```bash
python3 references/baselines/86-verify.py
```

`verification.json` 记录本次初始化时的复核输出。它证明这些边表有效，不证明一般 Q7 / Q8 最优，也不是新下界。
