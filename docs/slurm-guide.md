# 实验室 Slurm：从 GitHub 获取路线 4 并提交 A100 作业

准备日期：2026-09-12。以下集群参数来自用户授权查看的 Horizon 远程终端：项目目录 `/home/wangs18/erdos-86`、分区 `gpuq`、账号 `hpcusers`、GPU 资源类型 `gpu:a100`。`sinfo` 也列出了 `a100-40g`，本入口使用已经出现的 `a100` 类型，不混用两者。

提交脚本已经包含这些参数。它们是 **Slurm 作业**，在登录节点执行 `sbatch` 后由计算节点运行；不要在登录节点直接启动训练。当前没有替用户提交任何 GPU 作业。GPU 速度、显存和驱动兼容性均要通过首次校准确认。

## 1. 将代码放进已经创建的目录

在 Horizon 的登录节点终端执行：

```bash
cd /home/wangs18/erdos-86
git clone https://github.com/wssswsws/erdos-86.git .
git log -1 --oneline
mkdir -p logs
```

最后的 `.` 表示克隆到当前目录，不会再生成一层 `erdos-86/`。该命令适用于新建的空目录。如果它已经是本仓库，改用 `git pull --ff-only`；若目录含有其他文件，先检查，不要删除文件来强行克隆。

仓库是私有的，远端也需要自己的 GitHub 认证。若 HTTPS 提示输入密码，应使用 GitHub 支持的令牌认证或你已有的凭据管理器，不能用网站登录密码。已配置 GitHub SSH 的环境可改用 `git@github.com:wssswsws/erdos-86.git`。不要将令牌放进命令 URL、配置文件、聊天或提交记录。参见 [GitHub 命令行认证](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github#authenticating-with-the-command-line)。

本次在远端实际运行仓库读取检查时，GitHub 返回了 `Invalid username or token` / `Authentication failed`；`gh` 命令也未找到。因此，克隆前还需要你在远端完成有效的 GitHub 认证。代码可以正常从本机上传；本次没有复制本机令牌到实验室电脑，也没有改动远端已有凭据。

## 2. 准备独立 Python 环境

已观察到登录节点 base 环境为 Python 3.13.13，未安装 PyTorch。可在项目中建立 `.venv`，避免改动实验室已有环境：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cu126
python -m pip install 'pytest>=8,<10'
python -c "import torch; print(torch.__version__, torch.version.cuda)"
```

这里使用 [PyTorch 官方提供的 2.10.0 CUDA 12.6 wheel](https://pytorch.org/get-started/previous-versions/)，目标是减少对较新驱动的要求；计算节点驱动是否支持仍需校准确认。登录节点上 `torch.cuda.is_available()` 为 False 可以是正常现象，不能据此判断计算节点没有 GPU。

安装命令需要访问 Python 包仓库。如果登录节点不能访问，使用实验室提供的 PyTorch 2.10.0 环境或内部 wheel 镜像，并设置其 Python **绝对路径**：

```bash
export ERDOS86_PYTHON=/实际环境路径/bin/python
```

该路径也必须能在计算节点访问；没有设置时，脚本默认使用 `/home/wangs18/erdos-86/.venv/bin/python`。如果环境依赖 `module load`，需要在提交前加载实验室规定的模块。脚本会检查 PyTorch 版本，不会在计算节点联网安装依赖。这里无需安装 Modal、Iteris、PyG 或 Lean。

## 3. 首先提交单张 A100 校准

始终从仓库根目录提交。可先让 Slurm 检查申请是否可接受；`--test-only` 不真正提交作业，也不预留 GPU：

```bash
sbatch --test-only scripts/slurm/graphgps.sbatch benchmark
```

真正启动校准：

```bash
sbatch scripts/slurm/graphgps.sbatch benchmark
```

资源：1 张 A100、4 个 Slurm CPU、16 GiB 系统内存、20 分钟上限。脚本依次运行硬件检查、已有 15 项测试、20 步正式规模训练计时、一整批 32 张图的完整逐边采样，以及根据实测计算耗时。它不会继续启动 pilot。

Slurm 返回 `Submitted batch job JOB_ID` 后，用实际数字替换下文 `JOB_ID`：

```bash
squeue -u "$USER"
tail -f logs/erdos86-calibrate-JOB_ID.out
```

按 Ctrl+C 只是退出 `tail`，不会取消任务。错误日志是 `logs/erdos86-calibrate-JOB_ID.err`。结束后查看：

```bash
sacct -j JOB_ID --format=JobID,JobName,State,Elapsed,AllocTRES,MaxRSS,ExitCode
cat artifacts/experiments/slurm-JOB_ID/benchmark-seed-8601/exit-code.txt
cat artifacts/experiments/slurm-JOB_ID/benchmark-seed-8601/hardware.json
cat artifacts/experiments/slurm-JOB_ID/benchmark-seed-8601/estimate.json
```

`exit-code.txt` 为 0、Slurm 状态为 COMPLETED，且报告没有错误，才表示流程正常结束。`estimated_allocated_hours_with_paired_baseline` 是含 CPU 修补与配对对照的估计，不包含所有启动/保存成本。先据此判断现有 4 小时预算能否覆盖计划。`sbatch` 返回 Job ID 只表示已受理，可能仍在排队。[Slurm 官方说明](https://slurm.schedmd.com/sbatch.html)。

## 4. 校准通过后选择正式试验

单卡、一个随机种子：

```bash
sbatch --job-name=erdos86-pilot --time=04:15:00 \
  scripts/slurm/graphgps.sbatch pilot 8601
```

**必须保留 `--time=04:15:00`**，否则会继承校准脚本的 20 分钟上限。模型循环自身有 4 小时软时限，额外 15 分钟给启动和保存。完整配置为 11,000 步训练、12,288 张候选；到时可能尚未完成全部轮次。

如果要使用一整个四 A100 节点，执行下面这一条即可，不要同时再提交上面的单卡 pilot：

```bash
sbatch scripts/slurm/four-pilots.sbatch
```

它申请 1 个节点、4 张 A100、16 个 Slurm CPU、64 GiB 系统内存，启动四个独立进程。种子分别为 8601、8602、8603、8604，分别使用 Slurm 分配后可见的逻辑 `cuda:0` 至 `cuda:3`。没有修改 Slurm 的 `CUDA_VISIBLE_DEVICES`，也没有假设它们就是整台服务器的物理 GPU 0–3。[GPU 分配规则](https://slurm.schedmd.com/gres.html)。

**这是四次独立实验，不是四卡共同训练一个模型。** 每个实验有独立目录和日志：

```text
artifacts/experiments/slurm-JOB_ID/pilot-seed-8601/
artifacts/experiments/slurm-JOB_ID/pilot-seed-8602/
artifacts/experiments/slurm-JOB_ID/pilot-seed-8603/
artifacts/experiments/slurm-JOB_ID/pilot-seed-8604/
logs/slurm-JOB_ID/seed-8601.log
...
```

四卡占用约 4 小时相当于约 16 GPU 小时，还要加启动/保存的分配时间。先校准单卡，避免把环境问题放大成四份。四个实验互不共享精英池；其中一个找到 305 不会自动停止其他三个。需要人工查看报告并决定是否停止剩余计算。

## 5. 取消、排错和保存

```bash
scancel JOB_ID
```

取消或平台强制终止可能来不及保存最后状态。程序会在阶段边界和正常超时时保存检查点；不承诺精确恢复中断的采样位置。作业配置为 `--no-requeue`，且同一输出目录不允许覆盖；恢复需要先检查已有成果并明确新的运行预算。

常见问题：

- **找不到 logs 文件**：先执行 `mkdir -p logs`，再提交；作业仍在等待时也可能尚未生成日志。
- **Python not found**：先建立 `.venv`，或设置能在计算节点访问的 `ERDOS86_PYTHON`。
- **CUDA unavailable / driver insufficient**：查看 `.err` 和 `hardware.json`；核对 PyTorch wheel 与计算节点驱动，不要转到登录节点尝试 GPU 训练。
- **Invalid account / partition / GRES**：运行 `sinfo -o '%P %G %l %a'` 和 `sacctmgr -nP show assoc where user="$USER" format=Account,Partition,QOS` 核对配置。管理员可能会调整这些名称。
- **OUT_OF_MEMORY / CUDA out of memory**：区分系统内存与显存；调整申请或 batch 后重新校准。

## 6. 通过 GitHub 把结果带回来

作业完成后，在登录节点把小体积 JSON 报告、边表与测试记录提交到单独结果分支。先查看实际输出；**不要使用 `git add .`**：

```bash
git switch -c results/slurm-JOB_ID
git add artifacts/experiments/slurm-JOB_ID
git diff --cached --stat
git commit -m "Record Slurm JOB_ID GraphGPS results [skip ci]"
git push -u origin HEAD
```

把 `JOB_ID` 替换成真实作业编号。同一个节点的四个实验保存在同一作业目录，可以一次回传。`.pt` 检查点、终端日志及虚拟环境已被忽略，默认不上传。`report.json` 包含源码哈希、最佳候选来源与验证统计；`best.json` 保存完整边表。结果分支创建后，后续代码更新先切回 `main` 并执行 `git pull --ff-only`；运行中的任务不要更换工作目录里的代码版本。

本地收到结果后再复核最佳边表，并把实际卡时和研究结论写回 Iteris。训练完成、最好边数仍为 304，不表示得到新数学结果。找到 305 时要保留原始边表与独立验证证据。

## 当前验证范围

在旧提交的临时克隆中加入准备提交的核心文件后，15 项 Python 测试再次通过。4 份 shell 文件通过 Bash 语法检查和登录节点误启动拦截检查；四进程的设备编号、种子与输出目录隔离通过假 Python 执行器的编排检查，同名输出目录会拒绝覆盖。证据见 [validation.json](../artifacts/experiments/slurm-preparation/validation.json)。这些不属于真实 GPU 测试；未执行云端 GPU 校准，不能声称 CUDA、Slurm 调度和四 GPU 并发已验证。
