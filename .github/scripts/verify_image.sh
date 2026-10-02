#!/usr/bin/env bash
# 驗證一個 build 好的 image 能不能上線。PR 的 CI 與發布前各跑一次，兩邊用同一支。
#   1. 執行期套件版本與 poetry.lock 完全一致，也沒有 lock 以外的套件
#   2. 主程式可 import、PyPtt 相容性修補全部套用、打包工具確實已移除
#   3. entrypoint 能啟動，且在缺少必要環境變數時以錯誤碼 1 結束
#
# 用法（在 repo 根目錄執行，需要 docker 與 Python 3.11+）：
#   bash .github/scripts/verify_image.sh <image>
set -euo pipefail

image=${1:?用法：verify_image.sh <image>}

echo "== 1/3 套件版本與 poetry.lock 比對"
installed=$(docker run --rm --entrypoint python "$image" -c '
import importlib.metadata as m, json
print(json.dumps({d.metadata["Name"]: d.version for d in m.distributions()}))
')
INSTALLED_JSON="$installed" python3 - <<'PY'
import json
import os
import re
import sys
import tomllib


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


installed = {norm(k): v for k, v in json.loads(os.environ["INSTALLED_JSON"]).items()}
with open("poetry.lock", "rb") as f:
    lock = tomllib.load(f)
expected = {
    norm(p["name"]): p["version"]
    for p in lock["package"]
    if "main" in p.get("groups", [])
}

problems = [
    f"{name}: lock={version} image={installed.get(name)}"
    for name, version in sorted(expected.items())
    if installed.get(name) != version
]
extra = sorted(set(installed) - set(expected) - {"pttautosign"})
if extra:
    problems.append(f"image 裡有 lock 以外的套件：{', '.join(extra)}")

if problems:
    print("::error::image 內容與 poetry.lock 不一致")
    for problem in problems:
        print(f"  - {problem}")
    sys.exit(1)
print(f"{len(expected)} 個執行期套件全部與 poetry.lock 一致，沒有多餘的套件")
PY

echo "== 2/3 執行期 smoke test"
docker run --rm -i --entrypoint python "$image" - <<'PY'
import importlib.util
import sys

import pttautosign.main  # noqa: F401
from pttautosign.patches.pyptt_patch import apply_patches

# 與 main() 相同的順序：先套修補，再 import 會連帶載入 PyPtt 的模組。
if not apply_patches():
    sys.exit("PyPtt 相容性修補沒有全部套用")
from pttautosign.utils.app_context import AppContext  # noqa: F401

leftover = [
    m
    for m in ("setuptools", "pkg_resources", "packaging", "pip", "wheel")
    if importlib.util.find_spec(m)
]
if leftover:
    sys.exit(f"打包工具沒有清乾淨：{leftover}")
print("主程式可 import、修補全部套用、打包工具已移除")
PY

echo "== 3/3 entrypoint 檢查"
# 不給任何環境變數：docker_runner.sh 應在檢查環境變數時就以錯誤碼 1 結束。
# 用這個確認 bash、腳本權限、entrypoint 設定都正常，而且不會真的連上 PTT。
set +e
output=$(docker run --rm "$image" 2>&1)
status=$?
set -e
echo "$output"
if [ "$status" -ne 1 ] || ! grep -q "缺少必要的環境變數" <<<"$output"; then
    echo "::error::entrypoint 在缺少環境變數時應以錯誤碼 1 結束並提示缺少哪些變數（實際錯誤碼：$status）"
    exit 1
fi
echo "entrypoint 正常：缺少環境變數時拒絕啟動"
