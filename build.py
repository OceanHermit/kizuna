#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キズナ ポータル ビルダー
========================
data/*.json を読んで index.html を書き出します。

    python3 build.py

内容を直すときは data/ の JSON を編集して、このスクリプトを実行し、
git にコミットするだけです。見た目は assets/style.css が持っています。
"""

import html
import json
import os
import pathlib
import datetime

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
WD = "日月火水木金土"


def load(name):
    with open(DATA / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def e(s):
    """テキストとして安全に埋め込む（HTMLタグを書きたい箇所では使わない）"""
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- 読み込み
site = load("site")
words = load("words")
events = load("events")
news = load("news")
faq = load("faq")
menu = load("menu")
images = load("images")

L = site["links"]


def link(key):
    """menu.json / faq.json の link はキー名。site.json のURLに解決する"""
    return L.get(key, key if key else "#")


def img(key):
    """assets/img/<key>.png があればそれを、無ければ生成元のURLを返す"""
    for ext in (".png", ".jpg", ".webp"):
        if (ROOT / "assets" / "img" / f"{key}{ext}").exists():
            return f"assets/img/{key}{ext}"
    f = images["files"].get(key)
    return images["base"] + f if f else ""


def alt(key):
    return images["alt"].get(key, "")


def picture(key, cls="", decorative=False):
    """decorative=True のときは alt="" にする。
    （文字が隣にある飾りの絵。読み上げでも読み込み失敗時でも邪魔にならない）"""
    src = img(key)
    if not src:
        return ""
    c = f' class="{cls}"' if cls else ""
    a = "" if decorative else alt(key)
    return f'<img{c} src="{e(src)}" alt="{e(a)}" loading="lazy" decoding="async">'


# ---------------------------------------------------------------- 部品
def section_head(icon, title, en, more=None):
    m = ""
    if more:
        m = f'<a class="sh__more" href="{e(more[1])}">{e(more[0])}</a>'
    return f"""      <div class="sh">
        <span class="sh__ic" aria-hidden="true">{icon}</span>
        <div>
          <h2 class="sh__t">{e(title)}</h2>
          <p class="sh__en">{e(en)}</p>
        </div>{m}
      </div>"""


def event_items():
    out = []
    for ev in sorted(events, key=lambda x: x["date"]):
        y, m, d = (int(v) for v in ev["date"].split("-"))
        w = WD[datetime.date(y, m, d).weekday() - 6]  # 月曜=0 → 日曜起点に寄せる
        meta = "　".join(x for x in (ev.get("time", ""), ev.get("place", "")) if x)
        out.append(f"""        <a class="ev__item" href="{e(ev.get('link', '#'))}" data-ev-date="{e(ev['date'])}">
          <span class="ev__date">
            <span class="ev__m">{m}月</span>
            <span class="ev__d">{d}</span>
            <span class="ev__w">{w}</span>
          </span>
          <span>
            <span class="ev__tag">{e(ev.get('tag', '行事'))}</span>
            <span class="ev__ttl mr">{e(ev['title'])}</span>
            <span class="ev__meta">{e(meta)}</span>
            <span class="ev__body">{e(ev.get('body', ''))}</span>
          </span>
        </a>""")
    return "\n".join(out)


def news_items():
    out = []
    for n in sorted(news, key=lambda x: x["date"], reverse=True):
        y, m, d = n["date"].split("-")
        out.append(f"""        <a class="news__item" href="{e(n.get('link', '#'))}">
          <span class="news__meta">
            <time class="news__date" datetime="{e(n['date'])}">{y}.{m}.{d}</time>
            <span class="news__cat">{e(n.get('cat', 'お知らせ'))}</span>
          </span>
          <span class="news__ttl mr">{e(n['title'])}</span>
          <span class="news__body">{e(n.get('body', ''))}</span>
        </a>""")
    return "\n".join(out)


def menu_items():
    out = []
    for mi in menu:
        attr = f' data-for="{mi["for"]}"' if mi.get("for") in ("kid", "adult") else ""
        out.append(f"""        <a class="mi"{attr} href="{e(link(mi.get('link')))}">
          <span class="mi__img">{picture(mi['img'])}</span>
          <span class="mi__b">
            <span class="mi__en">{e(mi['no'])}　{e(mi['en'])}</span>
            <span class="mi__t mr">{e(mi['title'])}</span>
            <span class="mi__x">{e(mi['text'])}</span>
          </span>
        </a>""")
    return "\n".join(out)


def faq_items():
    out = []
    for q in faq:
        attr = f' data-for="{q["for"]}"' if q.get("for") in ("kid", "adult") else ""
        body = [f"<p>{e(q['a'])}</p>"]
        if q.get("example"):
            body.append(f'<p class="q__ex">{q["example"]}</p>')   # 例文はHTMLを許可
        if q.get("link_label"):
            body.append(f'<a class="q__link" href="{e(link(q.get("link")))}">'
                        f'{e(q["link_label"])} <span aria-hidden="true">→</span></a>')
        out.append(f"""        <details class="q"{attr}>
          <summary><span class="q__q" aria-hidden="true">Q</span><span>{e(q['q'])}</span></summary>
          <div class="q__a"><b aria-hidden="true">A</b><div>{''.join(body)}</div></div>
        </details>""")
    return "\n".join(out)


# JSON は f-string の外で用意する（f-string 内の {} と衝突するため）
WORDS_JSON = json.dumps(words, ensure_ascii=False)
EVENTS_JSON = json.dumps(
    [{"date": x["date"], "title": x["title"], "time": x.get("time", ""),
      "place": x.get("place", ""), "link": x.get("link", "#")} for x in events],
    ensure_ascii=False)


NAV = [("つぎの行事", "#event"), ("できること", "#menu"), ("お知らせ", "#news"),
       ("キズナのこと", "#about"), ("よくある質問", "#faq"), ("お問い合わせ", "#contact")]

# 画像が全部そろっているかの確認に使う
ALL_IMG = ("hero", "mascot", "club", "juku", "shindan", "point",
           "festival", "staff", "parent", "landscape")


def nav_links(cls=""):
    c = f' class="{cls}"' if cls else ""
    return "".join(f'<a{c} href="{h}">{e(t)}</a>\n        ' for t, h in NAV).rstrip()


# ---------------------------------------------------------------- 組み立て
draft = ""
if site.get("draft"):
    draft = f'<p class="draft">{e(site["draft_note"])}</p>\n'

doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(site['title'])}</title>
<meta name="description" content="{e(site['description'])}">
<meta property="og:title" content="{e(site['title'])}">
<meta property="og:description" content="{e(site['description'])}">
<meta property="og:type" content="website">
<meta property="og:image" content="{e(img('hero'))}">
<meta name="theme-color" content="#1F5D4C">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='15' fill='%23FAF6EE'/><path d='M16 7c3.9 0 7 2.9 7 6.5 0 3-2.2 5.5-5.2 6.2V24h-3.6v-4.3C11.2 19 9 16.5 9 13.5 9 9.9 12.1 7 16 7z' fill='%231F5D4C'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
</head>
<body data-mode="kid">
{draft}
<header class="hd">
  <div class="wrap hd__in">
    <a class="logo" href="#top">{picture('mascot', decorative=True)}<span>{e(site['name'])}</span></a>
    <nav class="hd__nav" aria-label="メインメニュー">
        {nav_links()}
    </nav>
    <div class="mode" role="group" aria-label="表示の切り替え">
      <button type="button" data-mode="kid" aria-pressed="true">こども</button>
      <button type="button" data-mode="adult" aria-pressed="false">おとな</button>
    </div>
    <button class="burger" type="button" aria-expanded="false" aria-label="メニューを開閉する"><i></i><i></i><i></i></button>
  </div>
  <div class="wrap">
    <nav class="drawer" aria-label="メニュー">
        {nav_links()}
    </nav>
  </div>
</header>

<main id="top">

  <!-- ============ きょうのキズナ ============ -->
  <section class="dash">
    <div class="wrap dash__in">
      <div class="dash__hello">
        <h1 class="dash__greet mr" data-greet>こんにちは。</h1>
        <p class="dash__date" data-today></p>
      </div>
      <div class="dash__grid">

        <div class="card word">
          <span class="card__label">きょうのことば</span>
          <p class="word__txt" data-word-text>{e(words[0]['text'])}</p>
          <p class="word__note" data-word-note>{e(words[0].get('note', ''))}</p>
          {picture('mascot', 'word__mascot', decorative=True)}
        </div>

        <div class="card next" data-next>
          <div>
            <span class="card__label">つぎの行事まで</span>
            <p class="next__d"><span class="next__num" data-next-num>—</span><span class="next__unit" data-next-unit></span></p>
            <p class="next__ttl" data-next-title></p>
            <p class="next__meta" data-next-meta></p>
          </div>
          <a class="next__link" href="#event" data-next-link>くわしく見る <span aria-hidden="true">→</span></a>
        </div>

      </div>
    </div>
  </section>

  <!-- ============ つぎの行事 ============ -->
  <section class="sec" id="event">
    <div class="wrap">
{section_head('🗓', 'つぎの行事', 'EVENT')}
      <div class="ev">
{event_items()}
      </div>
    </div>
  </section>

  <!-- ============ できること ============ -->
  <section class="sec" id="menu">
    <div class="wrap">
{section_head('🌱', 'キズナでできること', 'SERVICE')}
      <div class="menu">
{menu_items()}
      </div>
    </div>
  </section>

  <!-- ============ お知らせ ============ -->
  <section class="sec" id="news">
    <div class="wrap wrap--n">
{section_head('📣', 'お知らせ', 'NEWS', ('すべて見る', '#'))}
      <div class="news">
{news_items()}
      </div>
    </div>
  </section>

  <!-- ============ キズナのこと ============ -->
  <section class="sec about" id="about">
    <div class="wrap">
{section_head('🌳', 'キズナのこと', 'ABOUT')}
      <div class="about__grid">
        <div class="about__img">{picture('hero')}</div>
        <div>
          <h3 class="about__t">{site['tagline']}</h3>
          <p class="about__p">{e(site['lead'])}</p>
          <p class="about__p">学校のこと、進路のこと、毎日のこと。子どもたち一人ひとりの状況に合わせて、無理のないかたちで参加できます。保護者の方のご相談も、いつでもお受けしています。</p>
          <div class="pts">
            <div class="pt"><span class="pt__i" aria-hidden="true">🍃</span><div>
              <p class="pt__t">仏教の教えをもとに</p>
              <p class="pt__x">毎日をステキに過ごすための考え方を、子どもたちの言葉で伝えています。</p></div></div>
            <div class="pt"><span class="pt__i" aria-hidden="true">🧭</span><div>
              <p class="pt__t">一人ひとりに合わせて</p>
              <p class="pt__x">年齢や状況に応じたコースをご用意。無料体験からはじめられます。</p></div></div>
            <div class="pt"><span class="pt__i" aria-hidden="true">🤝</span><div>
              <p class="pt__t">全国に、仲間がいる</p>
              <p class="pt__x">行事や文化祭を通じて、同じ年ごろの仲間と出会うことができます。</p></div></div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ============ 全幅の帯 ============ -->
  <div class="band">{picture('landscape', decorative=True)}</div>

  <!-- ============ モード別パネル ============ -->
  <section class="sec" id="for-you" style="padding-top:0">
    <div class="wrap">

      <div class="panel" data-for="kid">
        <div class="panel__img">{picture('festival')}</div>
        <div class="panel__b">
          <h2 class="panel__t">はじめての子へ</h2>
          <p class="panel__x">ひとりで来ても大丈夫。はじめての子には、かならずスタッフが声をかけます。ずっといなくてもいいし、見ているだけでもかまいません。</p>
          <ul class="panel__list">
            <li>とちゅうで帰ってもいいよ</li>
            <li>話したくないときは、話さなくていいよ</li>
            <li>行事に出ると、キズナポイントがたまるよ</li>
            <li>こまったことは、スタッフに言ってね</li>
          </ul>
          <div class="panel__btns">
            <a class="btn btn--f" href="#event">つぎの行事を見る</a>
          </div>
        </div>
      </div>

      <div class="panel" data-for="adult">
        <div class="panel__img">{picture('parent')}</div>
        <div class="panel__b">
          <h2 class="panel__t">保護者の方へ</h2>
          <p class="panel__x">お子さんの年齢や状況に合わせて、無理のないかたちで参加していただけます。ご不明な点は、キズナ担当がお話をうかがいます。</p>
          <ul class="panel__list">
            <li>会費はキズナクラブが月200円、オンラインコースが月2000円です</li>
            <li>自動引き落としは行っておりません。規定の納め方でご納入ください</li>
            <li>個別コースのご案内は、キズナ担当との打ち合わせ後を推奨しております</li>
            <li>無料体験からはじめていただけます</li>
          </ul>
          <div class="panel__btns">
            <a class="btn btn--f" href="{e(L['consult'])}">相談フォームを開く</a>
            <a class="btn" style="border:1.5px solid var(--line)" href="{e(L['fee'])}">会費の納め方</a>
          </div>
        </div>
      </div>

    </div>
  </section>

  <!-- ============ よくある質問 ============ -->
  <section class="sec" id="faq">
    <div class="wrap wrap--n">
{section_head('💬', 'よくある質問', 'Q & A')}
{faq_items()}
    </div>
  </section>

  <!-- ============ お問い合わせ ============ -->
  <section class="sec" id="contact">
    <div class="wrap wrap--n">
      <div class="ct">
        <div class="ct__in">
          <h2 class="ct__t">まずは、お話を<br>聞かせてください。</h2>
          <p class="ct__x">キズナ担当へのご紹介、打ち合わせ、個別コース登録、無料体験のご相談を承っています。どんな小さなことでも、お気軽にご連絡ください。</p>
          <div class="ct__btns">
            <a class="btn btn--w" href="{e(L['consult'])}">相談フォームを開く</a>
            <a class="btn btn--o" href="{e(L['join'])}">キズナクラブに申し込む</a>
          </div>
          <div class="ct__tel">
            <a class="ct__num" href="{e(site['tel_href'])}">{e(site['tel'])}</a>
            <span class="ct__sub">タップで電話がかけられます</span>
            <p class="ct__sub" style="margin-top:10px">主催：{e(site['organizer'])} ／ 担当：{e(site['staff'])}</p>
          </div>
          <p class="ct__note"><b>お返事について</b><br>フォーム入力後のお返事は、目安として3日後です。お急ぎの場合は、キズナ担当に直接ご連絡ください。お子さんへの個別コースのご案内は、打ち合わせ後を推奨しております。</p>
        </div>
      </div>
    </div>
  </section>

</main>

<footer class="ft">
  <div class="wrap">
    <div class="ft__top">
      <div>
        <p class="ft__logo">{e(site['name'])}</p>
        <p class="ft__x">{e(site['lead'])}</p>
        <a class="ft__back" href="{e(L['gakuto'])}">学徒サイトに戻る →</a>
      </div>
      <nav class="ft__nav" aria-label="フッターメニュー">
        {nav_links()}
      </nav>
    </div>
    <div class="ft__btm">
      <span>&copy; {e(site['organizer'])}</span>
      <span>{e(site['name_en'])}</span>
    </div>
  </div>
</footer>

<div class="fx">
  <a href="{e(site['tel_href'])}">電話する</a>
  <a href="{e(L['consult'])}">相談・申し込み</a>
</div>

<script type="application/json" id="kizuna-words">{WORDS_JSON}</script>
<script type="application/json" id="kizuna-events">{EVENTS_JSON}</script>
<script src="assets/app.js" defer></script>
</body>
</html>
"""

out = ROOT / "index.html"
out.write_text(doc, encoding="utf-8")
print(f"書き出しました: {out}  ({len(doc.encode()):,} bytes)")
print(f"  行事 {len(events)} 件 / お知らせ {len(news)} 件 / "
      f"質問 {len(faq)} 件 / ことば {len(words)} 件")
missing = [k for k in ALL_IMG if not img(k)]
if missing:
    print("  画像が未設定:", ", ".join(missing))
