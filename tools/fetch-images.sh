#!/usr/bin/env bash
# data/images.json のイラストを assets/img/ に取り込みます。
# 取り込むと build.py が自動でローカルのファイルを使うようになり、
# 外部サービスに依存しなくなります。
#
#   bash tools/fetch-images.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p assets/img

python3 - <<'PY' > /tmp/kizuna-images.txt
import json
d = json.load(open('data/images.json', encoding='utf-8'))
for key, name in d['files'].items():
    print(key, d['base'] + name)
PY

while read -r key url; do
  out="assets/img/${key}.png"
  if [ -f "$out" ]; then
    echo "すでにあります: $out"
    continue
  fi
  echo "取得中: $key"
  if curl -fsS --max-time 60 -o "$out" "$url"; then
    echo "  → $out"
  else
    rm -f "$out"
    echo "  × 取得できませんでした（ネットワーク制限の可能性があります）" >&2
  fi
done < /tmp/kizuna-images.txt

rm -f /tmp/kizuna-images.txt
echo
echo "取り込みが終わったら、ビルドし直してください:"
echo "  python3 build.py"
