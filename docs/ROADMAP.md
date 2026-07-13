# EmbodiedLab 项目状态与路线图

## 当前结论

项目还没有全部完成。目前它是一个有真实核心功能、测试和公开仓库的早期可用原型，不再是只有想法或空目录，但还不能称为完整的实验诊断平台。

已经完成的是“工程基础 + 第一条可展示纵向功能”；尚未完成的是实验日志、episode、token 诊断和学习闭环。

## 已完成

### 工程基础

- Python `src/` 项目结构和 `pyproject.toml`；
- 根目录 `AGENTS.md` 项目规则；
- 项目文件越界保护 Hook；
- `.gitignore`、隐私规则和大文件排除；
- pytest 自动化测试；
- Public GitHub 仓库；
- 适应当前网络的 SSH over 443 拉取和推送；
- Git 日常工作流文档。

### 配置比较 MVP

- 读取 JSON、YAML 和 YML；
- 比较嵌套配置字段；
- 标记 `added`、`removed`、`changed` 和可选的 `unchanged`；
- 生成 Markdown 和 JSON 报告；
- 强制报告输出位于项目根目录内；
- 提供具身智能风格的合成 baseline/candidate 配置；
- 覆盖配置比较和路径边界的测试。

### 配置比较 Web UI

- 一键载入公开 baseline/candidate 示例；
- 上传 JSON、YAML 和 YML 配置；
- 展示 changed、added、removed 和 unchanged 指标卡；
- 按状态筛选字段差异；
- 下载 Markdown 和 JSON 报告；
- UI smoke test、真实浏览器交互验证和 README 截图；
- GitHub Actions 自动运行测试。

## 当前不能做什么

- 不能导入 TensorBoard、CSV 或 JSONL 训练日志；
- 不能绘制 loss、success rate 和 episode 长度曲线；
- 不能回放或筛选机器人 episode；
- 不能检查 tokenizer 对 action/world token 的拆分；
- 不能管理论文阅读和实验任务；
- 没有演示视频和 Release。

## 阶段判断

| 阶段 | 状态 | 完成标准 |
|---|---|---|
| 项目基础设施 | 已完成 | 规则、Git、测试、公开仓库可用 |
| 配置比较核心 | 已完成 | CLI 可运行，示例和测试通过 |
| 可展示的 v0.1 | 基本完成 | Web UI、截图、使用演示、CI 已完成，待 Release |
| 实验诊断 v0.2 | 未开始 | 日志导入、曲线、实验对比 |
| 具身特色 v0.3 | 未开始 | token 检查、episode/轨迹分析 |
| 学习闭环 v0.4 | 未开始 | 任务证据、周报和复盘 |

## 下一步优先级

### 1. 训练日志与指标模块

- 统一读取 CSV、JSONL 和 TensorBoard scalar；
- 绘制 loss、success rate、episode length；
- 对比多次实验并识别缺失或异常指标；
- 使用合成日志数据公开演示。

这一阶段能把项目从“配置 diff 工具”提升为“实验诊断平台”。

### 2. Token 对齐诊断

- 输入 tokenizer 和特殊 token 定义；
- 显示 token 文本、token id 和索引；
- 检查 action/world token 是否被拆分；
- 输出诊断结论和可复用测试。

它与简历中的实际问题直接相关，是最有具身/VLA 辨识度的模块。

### 3. Episode 与轨迹分析

- 定义公开的 episode 数据 schema；
- 按任务和成功/失败筛选；
- 展示状态、动作和关键时间点；
- 加入 KF/UKF 轨迹平滑基线。

### 4. 学习监督闭环

- 论文阅读和实验任务；
- Git commit、笔记和实验报告作为完成证据；
- 自动生成周报和下一周计划。

这个模块有个人使用价值，但对具身智能简历的优先级低于日志、token 和轨迹诊断，因此放在后面。

## v0.1 完成定义

满足以下条件后，可以把项目称为第一个完整可展示版本：

- 配置比较 Web UI 可用；
- CLI 和 UI 共享同一核心逻辑；
- 单元测试和 UI smoke test 通过；
- README 有功能截图和 3 分钟内可完成的快速开始；
- GitHub Actions 自动运行测试；
- 不依赖公司数据或 GPU；
- 从全新环境能按文档启动；
- 发布 `v0.1.0` Release。
