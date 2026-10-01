#!/usr/bin/env bash
# 本地开发：启动 GUI。支持自动重装依赖。
set -e
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo "==> 首次创建虚拟环境"
  uv venv
fi

echo "==> 安装/同步依赖"
uv pip install -e . >/dev/null

echo "==> 启动 OpsToolkit GUI"
uv run python -m ops_toolkit.app
