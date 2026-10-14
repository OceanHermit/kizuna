# キズナ ポータル — 運用メモ（Claude 向け）

子どもと保護者が定期的に見に来るためのポータルサイトです。
**内容は `data/*.json` だけに入っています。** HTML を直接編集しないでください。

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
| `data/events.json` | 行事の予定 | 「来月の行事を追加して」「終わった行事を消して」 |
| `data/news.json` | お知らせ | 「お知らせを書いて」 |
| `data/words.json` | きょうのことば（日替わり） | 「ことばを増やして」 |
| `data/faq.json` | よくある質問 | 「この質問を足して」 |
| `data/menu.json` | できること6枚のカード | 「カードの文言を変えて」 |
| `data/site.json` | 連絡先・各リンクのURL・準備中バナー | 「申込フォームのURLを入れて」 |
| `data/images.json` | イラストの場所 | 「写真を差し替えて」 |
| `assets/style.css` | 見た目（色・余白・角丸） | 「色を変えて」 |

## 気をつけること

- **日付は `YYYY-MM-DD`**。曜日は `build.py` が自動で計算します。手で書かないこと。
- **過ぎた行事は `events.json` から消す**。トップの「つぎの行事まであと◯日」は、
  今日以降でいちばん近い行事を自動で選びます。過去の行事が残っていても害はありませんが、
  一覧が長くなります。
- **`site.json` の `draft` を `false` にすると、上の黄色い「準備中」バナーが消えます。**
  行事の日程が正式に決まるまでは `true` のままにしてください。
- `faq.json` と `menu.json` の `for` は表示の出し分けです。
  `"kid"` = こどもモードだけ、`"adult"` = おとなモードだけ、無記入 = 両方。
- `faq.json` の `link` と `menu.json` の `link` は **`site.json` の `links` のキー名**を書きます
  （URL を直接書くこともできます）。
- `faq.json` の `example` だけは HTML タグが使えます。それ以外は文字として扱われます。

## 確認のしかた

```bash
python3 -c "import json;[json.load(open(f'data/{n}.json',encoding='utf-8')) for n in ['site','words','events','news','faq','menu','images']];print('JSON OK')"
python3 build.py
```

## 公開先

- GitHub Pages: https://oceanhermit.github.io/kizuna/
- `main` ブランチにあるものがそのまま公開されます（ビルド工程はありません）
