# EmbodiedLab Git 工作流

本文档是本项目在当前 Windows 电脑上的标准 Git/GitHub 操作流程。`AGENTS.md` 要求 Codex 在进行 Git 操作前先阅读本文档。

## 当前连接方式

本机网络不能访问普通的 `github.com:443` Git HTTPS 服务，因此仓库使用 GitHub 官方支持的 SSH over 443：

```text
origin = ssh://git@ssh.github.com:443/FigureNeverOut/EmbodiedLab.git
```

仓库级 Git 配置已经指定专用密钥：

```text
C:\Users\2216113152\.ssh\embodiedlab_github
```

该密钥是只绑定 `FigureNeverOut/EmbodiedLab` 的可写 deploy key。不要把私钥复制到项目目录、GitHub、聊天内容或其他电脑。

不要执行以下操作：

```powershell
git remote set-url origin https://github.com/FigureNeverOut/EmbodiedLab.git
git config --unset core.sshCommand
```

它们会破坏当前可用的 SSH 443 连接。

## 每次开始工作

在项目根目录打开 PowerShell：

```powershell
cd F:\AI\codex_project\project1
git status --short --branch
git pull --ff-only
```

预期状态类似：

```text
## main...origin/main
Already up to date.
```

如果工作区已有不认识的改动，不要覆盖、删除或重置，先检查来源。

## 开发与验证

修改代码后运行：

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
```

查看修改文件：

```powershell
git status --short
git diff
```

提交前必须确认：

- 没有个人电话、邮箱、证件或账号信息；
- 没有 API key、token、密码、SSH 私钥或 `.env`；
- 没有公司私有代码、日志、数据和服务器信息；
- 没有模型权重、checkpoint、视频或大规模 episode 数据；
- 测试已通过。

## 创建提交

优先明确选择需要提交的文件：

```powershell
git add README.md docs src tests examples pyproject.toml
git diff --cached
git commit -m "feat: describe the change"
```

确定工作区只有本次任务内容时，也可以使用：

```powershell
git add .
```

常用提交类型：

- `feat:` 新功能；
- `fix:` 修复问题；
- `test:` 测试；
- `docs:` 文档；
- `refactor:` 不改变功能的代码整理；
- `chore:` 工具或配置维护。

每个提交只表达一个清晰目的，不使用“update”“修改一下”等模糊信息。

## 推送到 GitHub

```powershell
git push
git status --short --branch
```

成功时通常显示：

```text
Everything up-to-date
## main...origin/main
```

远程仓库地址：

```text
https://github.com/FigureNeverOut/EmbodiedLab
```

## 常见问题

### `Host key verification failed`

不要关闭主机验证。先检查 GitHub 官方主机指纹，再检查：

```powershell
ssh-keygen -F "[ssh.github.com]:443" -f C:\Users\2216113152\.ssh\known_hosts
```

### `Permission denied (publickey)`

检查仓库级 SSH 命令和密钥文件：

```powershell
git config --get core.sshCommand
Test-Path C:\Users\2216113152\.ssh\embodiedlab_github
```

不要重新生成或覆盖现有密钥。需要更换时，先在 GitHub 仓库 Settings - Deploy keys 中删除旧 key，再配置新 key。

### 本地和远端都有新提交

不要直接使用 `git push --force`、`git reset --hard` 或删除分支。先运行：

```powershell
git fetch origin
git log --oneline --graph --decorate --all -20
```

确认分叉原因后再决定合并或变基。
