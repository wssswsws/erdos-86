# erdos-86

**实验室 A100 / Slurm 运行入口：** [从 GitHub 获取代码、准备环境、提交校准和试验](docs/slurm-guide.md)。已配置 `gpuq` 分区与单卡/四卡作业脚本；四卡方案是四个独立随机种子。先运行校准，真实 GPU 性能尚未验证。

路线 4 的 [GraphGPS 架构与 CPU smoke 证据](docs/graphgps-route4.md) 和 [Modal 备选操作指南](docs/modal-guide.md) 也已提供。

Erdős #86 的研究工作区，使用 Iteris 组织研究材料、任务和验证记录，使用现有 Lean 项目保存将来的形式化工作。

当前阶段：**路线 4 的 GraphGPS 风格生成器已实现，CPU smoke 与 15 项测试通过；已提供实验室 Slurm 提交脚本，尚未启动 GPU 试验，没有新的数学结果。**

## 现有研究入口

- [现有研究综述](docs/existing-research.md)：用户指定的五个来源、版本冲突、结论范围与复核结果。
- [讲义中的机器学习图论方法](docs/ml-methods-from-lectures.md)：Wagner 深度交叉熵法与 PatternBoost，含准确页码和 Q7 应用方案。
- `references/MANIFEST.json`：本次导入的 37 个资料文件；其中 32 个来自公开网络下载，另有论坛观察、讲义相关页文本等补充记录。
- `memory/facts/`：11 条新增持久记录，加上原有题目记录共 12 条。
- `tasks/TASK_POOL.json`：已完成的资料入库任务及 3 个待开展任务。

新增事实状态为 `reviewed`，具体证据范围见正文；不等同于独立人工审稿或 Iteris 的 `verified` 认证。

## 研究目标

原题研究超立方体中无四圈子图的渐近最大边数。初期聚焦七维情形：理解已知的 304 边构造，尝试找到至少 305 条边的合法构造，或取得范围明确的结构性结论。

题目与结论边界见 [sources/erdos-86.tex](sources/erdos-86.tex)，运行约定见 [docs/OPERATOR.md](docs/OPERATOR.md)。

## 本机使用

Iteris 系统放在本仓库之外的 `../../tools/iteris`，虚拟环境位于该目录的 `.venv`。在本仓库根目录执行：

```bash
./scripts/iteris doctor
./scripts/iteris status
python3 references/baselines/86-verify.py
python3 scripts/verify_wrona_certificates.py
./scripts/iteris tool memory search --query 'PatternBoost'
```

前两条检查环境和项目状态；随后两条分别复核 Q7/Q8 和 Q9–Q15 的已知构造；最后一条检索 Iteris 记忆。
初始化自带的 `accepted` 记录仅表示题目材料通过结构预检，不是数学证明认证。

准备开始研究时，可执行 `./scripts/iteris run --foreground`。这会启动并消耗底层模型额度，当前初始化没有执行它。本机尚未安装 `tmux`，因此先使用前台模式；图形面板尚未安装或启动。

Iteris 官方默认执行配置使用较宽权限。开始研究前应在合适的受限环境中检查执行配置；本仓库不保存登录信息或密钥。

## 版本与证据

- Iteris：`0.2.0`，官方提交 `a82213ef6247b551ddd19b413b06266e841d2375`。
- 官方仓库：<https://github.com/frenzymath/iteris>。
- 已知构造及来源：[references/baselines/README.md](references/baselines/README.md)。
- Lean 的版本和依赖保持现有 `lean-toolchain`、`lakefile.toml` 与 `lake-manifest.json` 配置。本次初始化未执行 Lean 构建。
- 首次上传使用 `[skip ci]`，未运行现有 Lean / Pages / release 工作流。下面保留原模板的 GitHub 配置说明。

## GitHub configuration

To set up your new GitHub repository, follow these steps:

* Under your repository name, click **Settings**.
* In the **Actions** section of the sidebar, click "General".
* Check the box **Allow GitHub Actions to create and approve pull requests**.
* Click the **Pages** section of the settings sidebar.
* In the **Source** dropdown menu, select "GitHub Actions".

After following the steps above, you can remove this section from the README file.
