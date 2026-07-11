# EmbodiedLab

EmbodiedLab 是一个面向 VLA、WAM 和机器人动态物体操作实验的本地诊断与学习闭环平台。它的目标不是在个人电脑上训练大模型，而是帮助研究者把“读论文、配置实验、检查日志、分析失败、安排下一步”连成一套可复现流程。

当前仓库已经完成第一条可运行功能：比较两份 JSON/YAML 实验配置，并生成 Markdown 或 JSON 差异报告。

## 快速体验

在项目根目录运行：

```powershell
$env:PYTHONPATH = "src"
python -m embodiedlab.config_diff examples/configs/baseline.yaml examples/configs/candidate.yaml
```

生成项目内的 Markdown 报告：

```powershell
$env:PYTHONPATH = "src"
python -m embodiedlab.config_diff `
  examples/configs/baseline.yaml `
  examples/configs/candidate.yaml `
  --output outputs/config-diff.md
```

运行测试：

```powershell
$env:PYTHONPATH = "src"
python -m pytest
```

更详细的 MVP 边界见 [`docs/MVP.md`](docs/MVP.md)。

## 为什么做这个项目

具身智能实验常见的问题并不只来自模型本身，还可能来自：

- 两次实验的配置不一致；
- 仿真资源或路径缺失；
- tokenizer 拆分特殊 token，导致 hidden state 取错位置；
- episode 数量很多，但失败案例难以快速定位；
- 论文阅读、代码修改和实验结果没有形成可追踪的闭环。

EmbodiedLab 将这些问题集中到一个本地工具中。项目强调低算力、可公开演示和独立完成，适合作为具身智能方向的求职作品。

## 计划中的主要功能

### 1. 实验登记与配置比较

- 导入 YAML、JSON 等实验配置；
- 对比两次实验的任务数、batch size、loss weight、模型 backend 等字段；
- 保存实验目的、假设、代码版本和结论。

### 2. 日志与指标诊断

- 读取 CSV、JSONL 和 TensorBoard 指标；
- 展示 loss、success rate、episode 长度等曲线；
- 标记异常中断、缺失指标和不同实验之间的差异。

### 3. Episode 与轨迹分析

- 按任务、成功/失败、时长等条件筛选 episode；
- 展示机器人动作、物体状态和关键时间点；
- 使用合成数据提供公开演示，不依赖公司的私有数据。

### 4. Token 对齐检查

- 检查 action/world 特殊 token 是否被 tokenizer 拆分；
- 展示 token id、文本位置和 hidden state 索引的对应关系；
- 将检查逻辑做成可复用测试，避免训练完成后才发现表征提取错误。

### 5. 轻量状态估计基线

- 对轨迹提供 KF/UKF 等 CPU 可运行的平滑基线；
- 对比原始观测与滤波结果；
- 展示状态估计能力与机器人任务分析的结合，而不是单独堆算法名词。

### 6. 学习闭环

- 管理论文阅读、代码任务和实验计划；
- 用笔记、Git 提交和实验结果作为完成证据；
- 自动整理每周完成事项、失败原因和下一周计划。

## 预期使用流程

```text
阅读论文并提出实验假设
          ↓
登记配置、代码版本和预期指标
          ↓
导入训练或评测日志
          ↓
比较配置、指标、token 和失败 episode
          ↓
记录结论并生成下一步任务
          ↓
形成可用于复盘和简历展示的实验报告
```

## 技术路线

- Python 3.11+
- Streamlit：快速构建本地交互页面
- pandas / Plotly：数据处理和可视化
- Pydantic：定义实验与 episode 数据结构
- pytest：测试配置比较、token 对齐和路径处理
- 可选 PyTorch/Transformers：只用于轻量 tokenizer 与张量分析，不训练大模型

所有核心功能应能在普通个人电脑上运行。需要示例模型时，优先使用小模型、mock tokenizer 或预先生成的数据。

## 初步目录规划

```text
project1/
├── AGENTS.md                 # Codex 项目规则
├── README.md                 # 项目介绍和使用方法
├── .codex/                   # 项目级 Codex Hook
├── src/embodiedlab/          # 核心业务代码
├── tests/                    # 自动化测试
├── data/                     # 本地数据，默认不进入 Git
├── outputs/                  # 生成的报告和图表
├── examples/                 # 可公开的合成示例
└── docs/                     # 设计、截图和项目说明
```

二级、三级目录可以按开发需要创建，但所有文件都必须位于本仓库根目录之下。

## Git 与隐私

- Git 是本地版本管理工具；GitHub 是存放远程 Git 仓库的网站，两者不是二选一。
- 本仓库会先使用 Git 保存本地版本，再在用户确认仓库可见性后连接 GitHub。
- 不提交个人证件与联系方式、公司私有代码和数据、服务器信息、模型权重或密钥。
- 第一次上传 GitHub 前必须进行一次隐私和大文件检查。

## 当前状态

- [x] 明确项目方向
- [x] 建立项目级 `AGENTS.md`
- [x] 添加工作区边界 Hook
- [x] 准备 Git 忽略规则
- [x] 确认 MVP 功能范围
- [x] 建立 Python 项目骨架
- [x] 实现配置比较核心逻辑和命令行入口
- [x] 添加合成实验配置和自动化测试
- [ ] 实现第一个配置比较页面
- [ ] 添加日志指标解析
