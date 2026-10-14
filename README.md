# キズナ ポータル

子どもと保護者のための、キズナクラブのポータルサイトです。

**公開先 → https://oceanhermit.github.io/kizuna/**

## このサイトの考え方

「定期的に見に来たくなる」ことを設計の軸にしています。

- **きょうのことば** — 日付で自動的に入れ替わります。毎日ちがう言葉が出ます
- **つぎの行事まで あと◯日** — いちばん近い行事までの日数を自動で数えます
- **こども／おとな の切り替え** — 右上のボタンで、見える内容が変わります。
  子どもには行事とポイントとやさしい質問、保護者には会費と相談と手続きの案内を出します
- 2週間以内の行事には「もうすぐ」の印が自動でつきます

## 更新のしかた

内容はすべて `data/*.json` に入っています。JSON を直してビルドするだけです。

```bash
python3 build.py        # data/*.json → index.html
```

`index.html` は自動生成されるファイルです。手で編集しないでください。

Claude に頼むときは、たとえばこう言えば通じます。

- 「12月の行事を events.json に追加して、ビルドして push して」
- 「お知らせを1件書いて。内容は〜」
- 「申し込みフォームのURLが決まったので site.json に入れて」
- 「準備中バナーを外して」

くわしい運用ルールは [CLAUDE.md](CLAUDE.md) にあります。

## ファイル構成

```
index.html          ← build.py の出力（手で編集しない）
build.py            ← data/*.json から index.html を作る
data/
  site.json         連絡先、各リンクのURL、準備中バナーの出し分け
  events.json       行事の予定
  news.json         お知らせ
  words.json        きょうのことば（22件、日替わり）
  faq.json          よくある質問（こども向け/おとな向け）
  menu.json         できること6枚のカード
  images.json       イラストの場所
assets/
  style.css         見た目（色・余白・角丸はここに集約）
  app.js            切り替え・日替わり・カウントダウンだけ（約130行）
  img/              イラストを取り込んだ置き場
tools/
  fetch-images.sh   イラストをリポジトリに取り込む
```

## イラストについて

Higgsfield（`z_image`）で生成した絵本調のイラスト10点を使っています。
いまは生成元のURLを直接読み込んでいるので、リポジトリに取り込んでおくと安心です。

```bash
bash tools/fetch-images.sh
python3 build.py
git add -A && git commit -m "イラストをリポジトリに取り込み" && git push
```

本物の行事写真に差し替える場合は、`assets/img/` に同じ名前（`hero.png` など）で
置けば、自動的にそちらが使われます。

| ファイル名 | 使われている場所 |
|---|---|
| `hero.png` | キズナのこと |
| `mascot.png` | ロゴ、きょうのことば |
| `club.png` / `juku.png` / `shindan.png` / `point.png` / `festival.png` / `staff.png` | できることの6枚 |
| `parent.png` | 保護者の方へ（おとなモード） |
| `landscape.png` | 全幅の帯 |

## 技術的なこと

- 素の HTML / CSS / JavaScript のみ。ビルドツールもフレームワークもありません
- JavaScript が動かなくても、内容はすべて読めます（こども用・おとな用の両方が出ます）
- `prefers-reduced-motion` に対応しています
- 外部から読み込むのは Google Fonts（Zen Maru Gothic / Zen Kaku Gothic New）とイラストだけです
