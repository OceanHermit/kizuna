#!/usr/bin/env python3
"""index.html の <!-- WP-BLOCK-START --> 〜 END を抜き出して
wordpress/kizuna-top.html（WordPress カスタムHTMLブロック貼り付け用）を生成する。
使い方: python3 build-wp.py
"""
import pathlib

ROOT = pathlib.Path(__file__).parent
FONT = ('@import url("https://fonts.googleapis.com/css2?'
        'family=Zen+Maru+Gothic:wght@500;700;900&'
        'family=Noto+Sans+JP:wght@400;500;700&display=swap");')
HEADER = """<!--
  キズナ トップページ / WordPress 貼り付け用
  ------------------------------------------------------------------
  使い方：固定ページを新規作成 →「カスタムHTML」ブロックを1つ置いて
  このファイルの中身を丸ごと貼り付け →「設定 > 表示設定」でその固定
  ページをホームページに指定してください。
  CSS はすべて .kzn 配下にスコープしているのでテーマと衝突しません。
  JavaScript は使っていません（メニュー開閉もCSSのみ）。
-->
"""

src = (ROOT / "index.html").read_text(encoding="utf-8")
block = src.split("<!-- ===== WP-BLOCK-START ===== -->")[1] \
           .split("<!-- ===== WP-BLOCK-END ===== -->")[0].strip()
block = block.replace("<style>\n", f"<style>\n{FONT}\n", 1)
out = ROOT / "wordpress" / "kizuna-top.html"
out.write_text(HEADER + block + "\n", encoding="utf-8")
print(f"generated: {out} ({len(block)} bytes)")
