# 用 Modal 运行 Erdős #86 路线 4

核查日期：2026-09-12。结论：**如果每月 30 美元计算额度尚未使用，预计足以完成首次校准及一次路线 4 pilot，并支持少量重复实验。它不保证足以找到 305 边构造。** 当前 2–4 小时是预算预留，尚无任何 GPU 实测。

Modal 把 Python 函数放到云端机器上执行。你继续在 Mac 上编辑代码、用 Iteris 保存研究记录；Modal 负责运行 PyTorch 和 GPU；完成后下载报告、边表和模型检查点。它本身不提出数学猜想，也不代替候选验证器。参见 [Modal 入门](https://modal.com/docs/guide)。

入口已经准备在 [scripts/modal_graphgps.py](../scripts/modal_graphgps.py)。本地 SDK 1.5.3 的定义、命令行解析和语法检查通过；按上传清单复制到隔离临时目录后，15 项原有测试全部通过。这验证了本地打包文件的完整性，云端镜像构建和 CUDA 路径仍待验证。本次没有登录账户、创建云端资源或启动 GPU 作业，路线 4 继续暂停。

## 免费额度与成本

Starter 无月订阅费，每月提供 30 美元计算额度。GPU、CPU、内存分别计费。以下采用标准 **Functions** 价格，申请 2 个物理 CPU 核及 8 GiB 系统内存；CPU 和内存合计约 0.1583 美元/小时。24 GiB 是 L4/A10 的显存，不是这 8 GiB 系统内存。价格与显存来源：[当前定价](https://modal.com/pricing)、[GPU 对比](https://modal.com/blog/gpu-types)；对比文章中的旧价格不用于计算。

| GPU | 显存 | GPU 美元/小时 | 加 CPU、内存后美元/小时 | 30 美元理论计算时长 | 预留 2–4 小时的计算费 |
| --- | ---: | ---: | ---: | ---: | ---: |
| L4 | 24 GiB | 0.7992 | 0.9575 | 31.3 小时 | 1.91–3.83 美元 |
| A10 | 24 GiB | 1.1016 | 1.2599 | 23.8 小时 | 2.52–5.04 美元 |
| L40S | 48 GiB | 1.9512 | 2.1095 | 14.2 小时 | 4.22–8.44 美元 |
| A100 40GB | 40 GiB | 2.0988 | 2.2571 | 13.3 小时 | 4.51–9.03 美元 |

这是相同时长的费用比较，不是各卡完成试验所需时间的预测。公式为：

```text
小时费率 = GPU 每秒价格 × 3600
         + 2 × 0.0000131 × 3600
         + 8 × 0.00000222 × 3600
```

CPU/内存按申请量与实际使用量的较大值收费；本入口同时设置了资源限制。建镜像、启动、结束、存储等费用未包含在表中，应保留余量。Volume 标价为 0.09 美元/GiB/月；计算赠额是否覆盖某项非计算费用，以账户实际规则为准。Notebook/Sandbox 的 CPU/内存费率也不同，不能照搬本表。[资源计费规则](https://modal.com/docs/guide/resources)、[定价](https://modal.com/pricing)。

对本项目的建议：

- 先用默认 **L4** 校准；若速度不理想，再用 **A10** 跑同一校准，以“预计完整试验小时数 × 小时费率”比较。
- 首次 pilot 暂预留 **5 美元**，足以覆盖 L4 的 4 小时运行额度并留出一些余量；这不是保证完整轮次在时限内结束。
- 三个随机种子的 pilot，若每次确实占用 2–4 小时，L4 计算费约 5.7–11.5 美元。
- 若扩展成 4 种架构 × 3 个随机种子，预计 24–48 单卡小时，L4 计算费约 23–46 美元，免费额度便不一定够。这里仅估价，入口不会自动执行这些实验。

目前 [pilot.json](../configs/graphgps/pilot.json) 计划 11,000 个训练步、12,288 张候选图。模型约 132 万参数，但每张图要逐边作出 448 次决定，每次都运行完整网络，因此小模型也可能有较高采样成本。详细假设见 [路线 4 说明](graphgps-route4.md)。

## 1. 注册，并限制自费支出

打开 [Modal 注册页](https://modal.com/signup)，选择 Starter。当前官方文档要求有支付方式才能使用；免费账户不意味着额度耗尽后自动停止收费。[账单说明](https://modal.com/docs/guide/billing)。

在 Settings → Usage & Billing 检查实际余额和本周期额度，然后区分两项设置：

- **Workspace budget / usage limit**：抵扣赠额前的总使用额。若你本周期总额度为 30 美元，可设置为 30 美元。
- **Spend limit**：抵扣赠额后需要自费的金额。若只想使用赠额，设置为 **0 美元**，并确认页面保存成功。达到该限制后，仍可由适用赠额覆盖的任务可以继续；需要新增自费的任务会被停止。

不要把第二项设成 30 美元：那代表允许额外自费 30 美元。官方举例中，100 美元 usage limit 配合 30 美元赠额，默认 spend limit 可达 70 美元。Starter 用 Workspace 层级即可；Environment budgets 是付费计划功能。[预算与支出限制](https://modal.com/docs/guide/budgets)。

## 2. 在 Mac 上登录

当前本机 `python3` 已有 Modal SDK **1.5.3**，无需重复安装。进入项目并启动浏览器认证：

```bash
cd /Users/wsss/Documents/Math-other/Mathathon/project/erdos-86
python3 -m modal setup
```

如果换了一个没有 Modal 的 Python 环境，先执行 `python3 -m pip install modal==1.5.3`。认证留在你的电脑上，无需把 token 粘贴到聊天或放进 Git 仓库。[官方安装与认证步骤](https://modal.com/docs/guide)。

可先进行完全离线的入口检查：

```bash
python3 scripts/modal_graphgps.py
```

看到 `Offline definition check passed` 只表示 Python 和 SDK 接口正常，不表示云端镜像或 CUDA 已验证。不要把 `modal run` 当成离线检查：它可能构建镜像并使用云端资源。

## 3. 先启动一次 L4 校准

**下面这条命令开始使用云端额度。** 它执行已有测试、20 次正式配置的计时训练步，以及一整批 32 张图的完整采样，并根据实测计算 pilot 耗时。它不启动完整 pilot。

```bash
python3 -m modal run scripts/modal_graphgps.py \
  --mode benchmark --run-id l4-calibration-001 --execute
```

首次镜像会安装 Python 3.13、PyTorch 2.10.0 CUDA 12.8、pytest。固定 CUDA wheel 来源是 [PyTorch 官方版本安装表](https://pytorch.org/get-started/previous-versions/)。本机不需要 NVIDIA 显卡或 CUDA Toolkit。

结果写入 `erdos86-graphgps-results` Volume 的 `l4-calibration-001/`。每次使用新的 `run-id`，已有目录会被拒绝覆盖。下载：

```bash
python3 -m modal volume get erdos86-graphgps-results l4-calibration-001 \
  artifacts/experiments/modal-l4-calibration-001
```

检查 `benchmark.json` 和 `estimate.json`：

- `hardware`：实际显卡；`peak_cuda_allocated_bytes`：PyTorch 已分配显存峰值，不是整个进程全部显存。
- `train_step_seconds`：一次训练步时间。
- `sample_batch_seconds`：完整生成 32 张图的时间。
- `estimated_allocated_hours_with_paired_baseline`：包含串行局部修补与配对对照的预计占用时长，但不包含启动等全部开销。

若超出 4 小时，需要先缩小试验或优化采样；时限只控制运行预算，不保证完成计划。若内存不足，调整 batch/资源后重新校准；不能继续使用旧估算。

如果要比较 A10，用新的运行名：

```bash
ERDOS86_MODAL_GPU=A10 python3 -m modal run scripts/modal_graphgps.py \
  --mode benchmark --run-id a10-calibration-001 --execute
```

## 4. 查看校准后，再启动正式试验

确认测试通过、CUDA 正常、预计成本合适后，L4 pilot 命令为：

```bash
python3 -m modal run --detach scripts/modal_graphgps.py \
  --mode pilot --run-id l4-pilot-001 --execute
```

`--detach` 允许本地断线后云端任务继续，关掉 Mac 不会停止这个任务。保存命令输出中的 App 链接和 App ID，在 Modal Dashboard 查看运行状态。[CLI 说明](https://modal.com/docs/cli/latest/run)。

入口默认单卡、无计划任务、无自动超参数扫描。训练程序有 4 小时软时限；Modal 函数有 4 小时 5 分钟执行时限，为退出和保存留出余量。镜像构建等不在该训练软时限内。一次启动不要同时再开别的 pilot；`max_containers=1` 不能替你限制所有独立 App 的总用量。

提前停止可在 Dashboard 的对应 App 操作，或运行：

```bash
python3 -m modal app stop YOUR_APP_ID
```

强制停止不保证最后一步检查点已保存。云端 GPU 函数也可能被平台抢占；现入口先在 Volume 提交运行标记，遇到同名目录会失败退出，避免已标记的运行被重放后从头再耗完整预算。它尚不是自动恢复训练系统。发生中断时，先查看已保存文件，再单独安排恢复。[抢占行为](https://modal.com/docs/guide/preemption)。

## 5. 下载结果，回到 Iteris 记录

```bash
python3 -m modal volume get erdos86-graphgps-results l4-pilot-001 \
  artifacts/experiments/modal-l4-pilot-001
```

目录里的 `training/report.json`、`training/best.json`、`training/candidates.jsonl`、`training/checkpoint.pt` 分别对应报告、最佳边表、候选记录和模型状态。Volume 可以在容器结束后保留文件；普通临时容器文件不能这样依赖。[Volume 文档](https://modal.com/docs/guide/volumes)、[下载命令](https://modal.com/docs/cli/latest/volume)。

在本机已有 PyTorch 的环境再次独立验图：

```bash
python3 -m erdos86_gps verify \
  --candidate artifacts/experiments/modal-l4-pilot-001/training/best.json
```

把校准报告、试验报告、Usage & Billing 中的实际用量，以及验图结果交回当前研究任务，即可继续用 Iteris 记录；在远端不必安装 Iteris。这个入口只上传模型代码、配置、相关测试和公开 304 边种子，不依赖 GitHub 推送。没有上传 `.git`，所以远端 `git_head` 可能为空，报告中的源码 SHA256 仍能用于核对。

当前模型启动池仍是原有种子及其派生图；这份云端入口没有完成更大数据集的轨道审核。一次试验的成功标准先是：完整流程可复现、得到真实 GPU 成本、判断生成与修补质量。最好结果仍为 304 时，不应把训练完成写成数学进展；找到 305 时也要保留完整边表并独立验证。
