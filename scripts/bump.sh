#!/usr/bin/env bash
# 用法: ./scripts/bump.sh 0.1.1
# 作用: 打 tag 并推送，触发 GitHub Actions 自动打包 Release。
set -e
cd "$(dirname "$0")/.."

if [ -z "$1" ]; then
    echo "用法: $0 <版本号，比如 0.1.1>"
    exit 1
fi

VERSION="$1"
TAG="v$VERSION"

echo "==> 更新 pyproject.toml 里的 version = $VERSION"
python - <<PY
import re, pathlib
p = pathlib.Path("pyproject.toml")
s = p.read_text(encoding="utf-8")
s = re.sub(r'version\s*=\s*"[^"]+"', 'version = "$VERSION"', s, count=1)
p.write_text(s, encoding="utf-8")
print("done")
PY

echo "==> git add / commit"
git add pyproject.toml
git commit -m "chore: bump version to $VERSION" || echo "(没有变化，跳过 commit)"

echo "==> 打 tag $TAG"
git tag "$TAG"

echo "==> 推送"
git push
git push origin "$TAG"

echo ""
echo "==> 完成。去 GitHub Actions 页面看构建进度。"
