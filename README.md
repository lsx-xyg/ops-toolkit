

一个**可扩展**的多平台运维工具箱。清理只是开始——未来会持续扩展更多平台、更多功能。

| 平台 | 功能 | 状态 |
|------|------|------|
| Vercel | 清理旧部署（每个项目保留最新 N 个） | ✅ |
| GitHub | 清理旧 Release（可选同时删 Git tag） | ✅ |
| GitHub | 清理 Actions 运行记录 | 🚧 计划中 |
| GitHub | 清理 GitHub Packages | 🚧 计划中 |
| Cloudflare | Pages / Workers 清理 | 📋 规划 |

去 [Releases](https://github.com/你的用户名/ops-toolkit/releases) 页面下载对应平台的可执行文件：

- `OpsToolkit-windows.exe`
- `OpsToolkit-macos`
- `OpsToolkit-linux`

双击运行，**无需安装 Python**。

macOS 首次打开如被 Gatekeeper 拦截，可执行：

```bash
xattr -d com.apple.quarantine OpsToolkit-macos
````

## 本地开发

需要 [uv](https://docs.astral.sh/uv/)。

```
git clone https://github.com/lsx-xyg/ops-toolkit.git
cd ops-toolkit

./scripts/dev.sh          
./scripts/dev.ps1         
```

或者手动：

```
uv venv
uv pip install -e .
uv run python -m ops_toolkit.app
```

## 本地打包

```
./scripts/build.sh        
./scripts/build.ps1       
```

产物在 `dist/` 下。

## 发布新版本

```
./scripts/bump.sh 0.1.1
```

脚本会自动：

1.  更新 `pyproject.toml` 版本号
    
2.  `git commit` + 打 tag `v0.1.1`
    
3.  推送，触发 GitHub Actions
    
4.  CI 编译三平台可执行文件并挂到 Releases
    

## Token 环境变量（可选）

不想每次粘贴 Token，可以先设置环境变量：

```
export VERCEL_TOKEN="xxx"      
export GITHUB_TOKEN="ghp_xxx"
```

```
$env:VERCEL_TOKEN = "xxx"      
$env:GITHUB_TOKEN = "ghp_xxx"
```

程序启动时会自动填入。

## 项目结构

```
src/ops_toolkit/
├── app.py                    # 主窗口，注册各平台 Tab
├── core/                     # 平台无关的通用能力
│   ├── http.py               # HTTP 封装│   ├── logger.py             # 日志总线
│   └── models.py             # 通用数据模型
├── ui/
│   └── platform_tab.py       # Tab 基类
└── platforms/                # 每平台一个包
    ├── vercel/
    │   ├── client.py         # Vercel API 封装
    │   ├── models.py
    │   ├── actions/          # 每个功能一个文件
    │   │   └── prune_deployments.py
    │   └── gui_tab.py
    └── github/
        ├── client.py         # GitHub API 封装（所有 GitHub 功能复用）
        ├── models.py
        ├── actions/
        │   └── prune_releases.py
        └── gui_tab.py
```

## 如何扩展

### 加一个新功能（例如"清理 GitHub Actions 运行记录"）

**不需要改任何已有文件**，只加新文件：

1.  在 `platforms/github/client.py` 里加 API 方法：
    
    ```
    def list_workflow_runs(self, full_name): ...
    def delete_workflow_run(self, full_name, run_id): ...
    ```
    
2.  新建 `platforms/github/actions/prune_workflow_runs.py`，仿照
    
    `prune_releases.py` 写逻辑。
    
3.  在 `platforms/github/gui_tab.py` 的 `build_actions` 里加一个
    
    `self._build_prune_workflow_runs(parent)`，再加一个方法画出这个
    
    功能区。
    

就这样，其他平台、其他功能都不用动。

### 加一个新平台（例如 Cloudflare）

复制 `platforms/github/` 整个目录为 `platforms/cloudflare/`，改

`client.py`（认证方式、base URL），改 `actions/`，然后：

1.  改 `platforms/cloudflare/gui_tab.py` 里的 `title` / `token_label` /
    
    `token_env`
    
2.  在 `app.py` 里加一行 `nb.add(CloudflareTab(nb), text="Cloudflare")`
    

完成。

## License

MIT

