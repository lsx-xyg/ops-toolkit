# 打包当前平台的可执行文件到 dist/
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$NAME = "OpsToolkit"

Write-Host "==> 确保依赖"
uv venv 2>$null | Out-Null
uv pip install -e . | Out-Null
uv pip install pyinstaller | Out-Null

Write-Host "==> 清理旧产物"
Remove-Item -Recurse -Force build, dist, "$NAME.spec" -ErrorAction SilentlyContinue

Write-Host "==> 打包"
uv run pyinstaller --onefile --windowed --name $NAME src/ops_toolkit/app.py

Write-Host ""
Write-Host "==> 完成，产物在: dist/"
Get-ChildItem dist
