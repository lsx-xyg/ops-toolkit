# OpsToolkit

一个**可扩展**的多平台运维工具箱。清理只是开始——未来会持续扩展更多平台、更多功能。

## 当前支持

| 平台 | 功能 | 状态 |
|------|------|------|
| Vercel | 清理旧部署（每个项目保留最新 N 个） | ✅ |
| GitHub | 清理旧 Release（可选同时删 Git tag） | ✅ |
| GitHub | 清理 Actions 运行记录 | 🚧 计划中 |
| GitHub | 清理 GitHub Packages | 🚧 计划中 |
| Cloudflare | Pages / Workers 清理 | 📋 规划 |

## 下载即用（Windows）

去 [Releases](https://github.com/你的用户名/ops-toolkit/releases) 页面下载 `OpsToolkit-windows.exe`，双击即可运行，**无需安装 Python**。

## 使用方法

1. 打开程序，进入对应平台的 Tab（Vercel / GitHub）
2. 填入 Token
   - Vercel Token：https://vercel.com/account/tokens
   - GitHub Token：https://github.com/settings/tokens（勾选 `repo`，如需删 Release 的 tag 还需 `workflow`）
3. 点击 **「连接并拉取」**，下拉框会自动填充项目 / 仓库列表
4. 在下拉框里选择**单个项目/仓库**，或保持 `[全部]` 处理全部
5. 设置「保留最新 N 个」和「并发线程数」
6. 点击 **「执行」**，日志区会实时显示进度

## 本地开发

需要 [uv](https://docs.astral.sh/uv/)。

``` bash
git clone https://github.com/你的用户名/ops-toolkit.git
cd ops-toolkit
```

**Windows PowerShell：**
``` powershell
./scripts/dev.ps1
```

**macOS / Linux / Git Bash：**
``` bash
./scripts/dev.sh
```

或者手动：

``` bash
uv venv
uv pip install -e .
uv run python -m ops_toolkit.app
```

## 本地打包（Windows）

``` powershell
./scripts/build.ps1
```

产物在 `dist/OpsToolkit.exe`。

## 发布新版本

``` bash
./scripts/bump.sh 0.1.1
```

自动完成：

1. 更新 `pyproject.toml` 版本号
2. commit + tag `v0.1.1`
3. push，触发 GitHub Actions
4. CI 编译 Windows exe 并挂到 Releases

## Token 环境变量（可选）

不想每次粘贴 Token，可以先设置环境变量，程序启动时会自动填入。

**Windows PowerShell：**
``` powershell
$env: VERCEL_TOKEN = " xxx "
$env: GITHUB_TOKEN = " ghp_xxx "
```

**macOS / Linux：**
``` bash
export VERCEL_TOKEN = "xxx"
export GITHUB_TOKEN = "ghp_xxx"
```

## 项目结构

```
src/ops_toolkit/
├── app.py                    # 主窗口，注册各平台 Tab
├── core/                     # 平台无关的通用能力
│   ├── http.py               # HTTP 封装
│   └── logger.py             # 日志总线
├── ui/
│   └── platform_tab.py       # Tab 基类（Token + 目标选择 + 日志）
└── platforms/                # 每平台一个包
    ├── vercel/
    │   ├── client.py         # Vercel REST API 封装
    │   ├── models.py
    │   ├── actions/          # 每个功能一个文件
    │   │   └── prune_deployments.py
    │   └── gui_tab.py
    └── github/
        ├── client.py         # 基于 PyGithub
        ├── actions/
        │   └── prune_releases.py
        └── gui_tab.py
```

## 如何扩展

### 加一个新功能（例如"清理 GitHub Actions 运行记录"）

**不需要改任何已有文件**，只加新文件：

1. 在 `platforms/github/client.py` 里加 API 方法（PyGithub 已提供）：
   ``` python
   def list_workflow_runs(self, full_name):
       return list(self.get_repo(full_name).get_workflow_runs())
   
   def delete_workflow_run(self, run_obj):
       run_obj.delete()
   ```

2. 新建 `platforms/github/actions/prune_workflow_runs.py`，仿照
   `prune_releases.py` 写逻辑。

3. 在 `platforms/github/gui_tab.py` 的 `build_actions` 里加一个
   `self._build_prune_workflow_runs(parent)`，再加一个方法画出这个
   功能区。

### 加一个新平台（例如 Cloudflare）

1. 复制 `platforms/github/` 整个目录为 `platforms/cloudflare/`
2. 改 `client.py`（认证方式、base URL）
3. 改 `actions/` 下的功能
4. 改 `gui_tab.py` 里的 `title` / `token_label` / `token_env` /
   `group_label`，实现 `list_groups()`
5. 在 `app.py` 里加一行：
   ``` python
   nb.add(CloudflareTab(nb), text = "Cloudflare")
   ```

完成。任何平台都会自动获得下拉框、日志面板、连接流程。

## 依赖

- [requests](https://requests.readthedocs.io/) — Vercel REST API
- [PyGithub](https://pygithub.readthedocs.io/) — GitHub API 封装
- [uv](https://docs.astral.sh/uv/) — 环境管理

## License

MIT
