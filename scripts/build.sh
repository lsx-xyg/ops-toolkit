#!/usr/bin/env bash
# 打包当前平台的可执行文件到 dist/
set -e
cd "$(dirname "$0")/.."

NAME="OpsToolkit"

echo "==> 确保依赖"
uv venv >/dev/null 2>&1 || true
uv pip install -e . >/dev/null
uv pip install pyinstaller >/dev/null

echo "==> 清理旧产物"
rm -rf build dist "$NAME.spec"

echo "==> 打包"
uv run pyinstaller \
  --onefile \
  --windowed \
  --name "$NAME" \
  src/ops_toolkit/app.py

echo ""
echo "==> 完成，产物在: dist/"
ls -lh dist/
