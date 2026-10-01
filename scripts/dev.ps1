# 本地开发：启动 GUI
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".venv")) {
    Write-Host "==> 首次创建虚拟环境"
    uv venv
}

Write-Host "==> 安装/同步依赖"
uv pip install -e . | Out-Null

Write-Host "==> 启动 OpsToolkit GUI"
uv run python -m ops_toolkit.app
