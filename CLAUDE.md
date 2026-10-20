# キズナ ポータル — 運用メモ（Claude 向け）

子どもと保護者のための、キズナクラブのポータルサイトです。
**内容は `data/*.json` だけに入っています。** 書き出された HTML を直接編集しないでください。

## いまあるページ

| URL | ファイル | 元データ |
|---|---|---|
| `/` | `index.html` | 全部 |
| `/events/` | `events/index.html` | `data/events.json` |
| `/events/<slug>/` | `events/<slug>/index.html` | `data/events.json` の1件 |
| `/news/` | `news/index.html` | `data/news.json` |
| `/news/<slug>/` | `news/<slug>/index.html` | `data/news.json` の1件 |

`events/` と `news/` のフォルダは **ビルドのたびに作り直されます**（消して再生成）。
中に手で置いたファイルは消えるので注意してください。

## データの原本はどこか（重要）

`data/events.json` `data/news.json` `data/hero.json` の3つは
**Google スプレッドシートが原本**です。これらを手で編集しても、
次の同期（30分おき）で上書きされて消えます。

| 直したいもの | 直す場所 |
|---|---|
| イベント・お知らせ・トップのスライド | スプレッドシート（`tools/sheet.config.json` にIDあり） |
| それ以外ぜんぶ | `data/*.json` を直接編集 → `python3 build.py` |

仕組みのくわしい説明は `docs/spreadsheet.md` にあります。

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
| `data/hero.json` | 一番上のスライド（注目イベント・複数可） | 「トップのスライドに文化祭を足して」 |
| `data/about.json` | キズナの紹介と3つの特徴 | 「紹介文を書き直して」 |
| `data/events.json` | イベントの予定（トップには先頭3件） | 「来月の行事を追加して」「終わった行事を消して」 |
| `data/news.json` | お知らせ（トップには新しい順に5件） | 「お知らせを書いて」 |
| `data/juku.json` | キズナ塾の紹介 | 「塾の説明を直して」 |
| `data/member.json` | 会員メニューのタイル | 「ポイント確認のリンク先を入れて」 |
| `data/faq.json` | よくある質問 | 「この質問を足して」 |
| `data/faq_intro.json` | 質問の上のキャラクターのセリフ | 「セリフを変えて」 |
| `data/photos.json` | 写真・イラストの差し込み口 | 「ヒーローの写真を差し替えて」 |
| `data/site.json` | 連絡先・各リンクのURL・準備中バナー | 「申込フォームのURLを入れて」 |
| `assets/style.css` | 見た目（色・余白・角丸） | 「色を変えて」 |

※ `events.json` `news.json` `hero.json` はスプレッドシートが原本です（上を参照）。

## 気をつけること

- **日付は `YYYY-MM-DD`**。曜日は `build.py` が自動で計算します。手で書かないこと。
- **過ぎたイベントは `events.json` から消す**。`hero.json` の各スライドも、
  日付が過ぎると「あと◯日」が自動的に消えます（スライド自体は残るので差し替えてください）。
- **`hero.json` の `slides` は配列**。1件だけにするとスライドの矢印とドットは出ません。
- **`site.json` の `draft` を `false` にすると、上の「準備中」バナーが消えます。**
  行事の日程が正式に決まるまでは `true` のままにしてください。
- **リンク先は `site.json` の `links` にまとめる。** 各データの `link` には
  そのキー名（`join` `present` など）を書きます。URL を直接書くこともできます。
- `faq.json` の `example` だけは HTML タグが使えます。それ以外は文字として扱われます。
- `member.json` の `tone` は `blue` / `green` / `purple` のどれか。アイコンの背景色です。
- **`slug` は URL になります。** 半角小文字・数字・ハイフンのみ。一度公開したら変えないこと
  （変えると前のURLが消え、共有済みのリンクが切れます）。
- イベントの `detail` とお知らせの `detail` は**段落の配列**です。詳細ページの本文になります。
  省略すると `body` が1段落として使われます。
- イベントの `apply` は申し込みフォームのキー名（`site.json` の `links`）。
  過ぎたイベントでは申し込みボタンが自動的に消え、「終了しました」の案内に変わります。

## ページを増やすとき

`build.py` の下のほうに `build_xxx()` という関数が並んでいます。
新しいページは「`build_xxx()` を書く」→「最後の `write(...)` に1行足す」の2手順です。

```python
made.append(write("club", 1, build_club))   # → club/index.html
```

`write(パス, 深さ, 関数)` の**深さ**は `../` をいくつ付けるかです。
`club/` なら 1、`events/<slug>/` なら 2。ここを間違えると CSS と画像が読めなくなります。
ページ内のリンクは必ず `u("events/")` のように `u()` を通してください。

## 写真の差し替え

写真は `data/photos.json` の `url` を書き換えるだけで入れ替わります。
HTML も `build.py` も触る必要はありません。

| キー | 使われている場所 | 向き |
|---|---|---|
| `hero1` `hero2` `hero3` | 一番上のスライド（全幅） | 横長 |
| `about` | キズナとは（左端まで断ち落とし） | 縦長 |
| `ev1` | イベントの大きい1件 | 横長 |
| `ev2` `ev3` | イベントの行（小さいサムネイル） | 正方形 |
| `juku` | キズナ塾の帯（全幅） | 横長 |
| `contact` | お問い合わせの背景（全幅・暗くかぶせる） | 横長 |
| `illust.faq` | よくある質問のキャラクター | 正方形 |

**優先順位**：`assets/img/<キー>.jpg`（または .png / .webp）があればそれを使い、
無ければ `photos.json` の `url` を使い、それも空なら下地のグラデーションが出ます。
**ファイルをリポジトリに置くのが一番確実です**（外部サービスに依存しなくなります）。

いまは Higgsfield で生成した仮の写真を、生成元のURLから読み込んでいます。
顔が写らない構図で統一してあるので、本物の写真に差し替えるときも同じ方針だと崩れません。

Unsplash の写真を使う場合は、写真ページの画像URL（`https://images.unsplash.com/photo-...`）を
`url` に貼ってください。Unsplash License は商用利用可・許諾不要・クレジット表記は任意です。

## メニューの出し分け

- 画面幅 900px 以上：ヘッダーのナビだけを表示（ハンバーガーは隠す）
- 900px 未満：ハンバーガーだけを表示（押すと全画面メニュー）

切り替えの境目は `assets/style.css` の `@media (min-width:900px)` です。

## 文字の大きさ

`assets/style.css` の `:root` に階段をまとめています。ここを変えると全体の印象が変わります。

| 変数 | 使いどころ | PCでの大きさ |
|---|---|---|
| `--t-cap` | 一番小さいラベル | 約 11px |
| `--t-body` | 本文 | 約 15px |
| `--t-h2` | セクション見出し | 約 43px |
| `--t-hero` | ヒーローの見出し | 約 82px |
| `--t-num` | 大きな連番（01 / 02 / 03） | 約 106px |

**一番小さい文字と一番大きい文字で約10倍の差**をつけています。
ここを縮めると、のっぺりした印象に戻るので注意してください。

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
