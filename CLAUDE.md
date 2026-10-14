# キズナ ポータル — 運用メモ（Claude 向け）

子どもと保護者のための、キズナクラブのトップページです。
**内容は `data/*.json` だけに入っています。** `index.html` を直接編集しないでください。

## 更新のしかた（必ずこの順番）

```bash
# 1. data/ の JSON を編集する
# 2. ビルドする
python3 build.py
# 3. コミットして push する（main に push すると公開されます）
git add -A && git commit -m "..." && git push
```

`index.html` は `build.py` の出力です。手で直しても次のビルドで消えます。

## どのファイルに何が入っているか

| ファイル | 中身 | よくある依頼 |
|---|---|---|
| `data/hero.json` | 一番上の大きい枠（注目イベント） | 「トップの告知を文化祭に差し替えて」 |
| `data/about.json` | キズナの紹介と3つの特徴 | 「紹介文を書き直して」 |
| `data/events.json` | イベントの予定（トップには先頭3件） | 「来月の行事を追加して」「終わった行事を消して」 |
| `data/news.json` | お知らせ（トップには新しい順に5件） | 「お知らせを書いて」 |
| `data/juku.json` | キズナ塾の紹介 | 「塾の説明を直して」 |
| `data/member.json` | 会員メニューのタイル | 「ポイント確認のリンク先を入れて」 |
| `data/faq.json` | よくある質問 | 「この質問を足して」 |
| `data/site.json` | 連絡先・各リンクのURL・準備中バナー | 「申込フォームのURLを入れて」 |
| `assets/style.css` | 見た目（色・余白・角丸） | 「色を変えて」 |

## 気をつけること

- **日付は `YYYY-MM-DD`**。曜日は `build.py` が自動で計算します。手で書かないこと。
- **過ぎたイベントは `events.json` から消す**。`hero.json` の日付が過ぎると、
  トップの「あと◯日」は自動的に消えます（告知自体は残るので差し替えてください）。
- **`site.json` の `draft` を `false` にすると、上の「準備中」バナーが消えます。**
  行事の日程が正式に決まるまでは `true` のままにしてください。
- **リンク先は `site.json` の `links` にまとめる。** 各データの `link` には
  そのキー名（`join` `present` など）を書きます。URL を直接書くこともできます。
- `faq.json` の `example` だけは HTML タグが使えます。それ以外は文字として扱われます。
- `member.json` の `tone` は `blue` / `green` / `purple` のどれか。アイコンの背景色です。

## 写真について

いまは写真を入れず、**枠だけ**を置いています（`build.py` の `ph()` が作っています）。
写真を入れるときは、`ph(...)` の呼び出しを `<img>` に差し替えてください。
枠は全部で6か所：注目イベント1・キズナとは1・イベントカード3・キズナ塾1。

## 配色

| 役割 | 色 | CSS変数 |
|---|---|---|
| 地 | ベージュ `#F5EFE4` | `--beige` |
| 基調 | パステルブルー `#A8C9E5` / 濃い青 `#44739E` | `--blue` / `--blue-d` |
| 差し色 | ライトグリーン `#BFE3C4` | `--green` |
| 差し色 | パープル `#C5B4E2` | `--purple` |

色を変えるときは `assets/style.css` の先頭 `:root` だけを直せば全体に効きます。

## 確認のしかた

```bash
python3 -c "import json;[json.load(open(f'data/{n}.json',encoding='utf-8')) for n in ['site','hero','about','juku','member','events','news','faq']];print('JSON OK')"
python3 build.py
```

## 公開先

- GitHub Pages: https://oceanhermit.github.io/kizuna/
- `main` ブランチにあるものがそのまま公開されます（ビルド工程はありません）
