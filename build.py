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

import datetime
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
WD = "日月火水木金土"


def load(name):
    with open(DATA / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def e(s):
    """テキストとして安全に埋め込む（HTMLを書きたい箇所では使わない）"""
    return html.escape(str(s), quote=True)


site = load("site")
hero = load("hero")
about = load("about")
juku = load("juku")
member = load("member")
events = load("events")
news = load("news")
faq = load("faq")
faq_intro = load("faq_intro")

L = site["links"]


def link(key):
    """data の link はキー名。site.json の links に無ければそのまま URL として扱う"""
    if not key:
        return "#"
    return L.get(key, key)


def ph(ratio, cls=""):
    """写真が入る枠。写真を入れるときは、この関数の出力を <img> に差し替える"""
    c = f" {cls}" if cls else ""
    # 比率は CSS 変数で渡す。こうするとセクションごとに CSS 側で上書きできる
    return (f'<div class="ph{c}" style="--ar:{ratio}">'
            f'<p class="ph__t"><b>📷</b>写真が入ります<br>{e(ratio.replace("/", " : "))}</p></div>')


def ill(ratio, cls=""):
    """イラストが入る枠。写真の枠とは見た目を分けている"""
    c = f" {cls}" if cls else ""
    return (f'<div class="ill{c}" style="--ar:{ratio}">'
            f'<p class="ph__t"><b>🎨</b>イラストが入ります</p></div>')


def jp_date(ymd):
    y, m, d = (int(v) for v in ymd.split("-"))
    return f"{m}月{d}日（{WD[datetime.date(y, m, d).weekday() - 6]}）"


# ---------------------------------------------------------------- 部品
NAV = [
    ("キズナとは", "#about", "ABOUT"),
    ("イベント", "#event", "EVENT"),
    ("お知らせ", "#news", "NEWS"),
    ("キズナ塾", "#juku", "STUDY"),
    ("会員メニュー", "#member", "MEMBER"),
    ("よくある質問", "#faq", "Q & A"),
    ("お問い合わせ", "#contact", "CONTACT"),
]


def nav_bar():
    return "".join(f'<a href="{h}">{e(t)}</a>' for t, h, _ in NAV[:6])


def nav_overlay():
    return "\n".join(
        f'        <a href="{h}"><span>{e(t)}<small>{e(en)}</small></span><i aria-hidden="true">→</i></a>'
        for t, h, en in NAV)


def section_head(en, title, text="", more=None, row=False):
    cls = "sh sh--row" if row else "sh"
    m = f'<a class="link" href="{e(more[1])}">{e(more[0])} <span aria-hidden="true">→</span></a>' if more else ""
    x = f'<p class="sh__x">{e(text)}</p>' if text else ""
    return f"""      <div class="{cls}">
        <div>
          <span class="sh__en">{en}</span>
          <h2 class="sh__t">{e(title)}</h2>
          {x}
        </div>{m}
      </div>"""


def hero_slide(h):
    chips = []
    if h.get("date"):
        chips.append(f'<span class="chip chip--blue">🗓 {e(jp_date(h["date"]))}</span>')
    if h.get("time"):
        chips.append(f'<span class="chip chip--green">🕐 {e(h["time"])}</span>')
    if h.get("place"):
        chips.append(f'<span class="chip chip--purple">📍 {e(h["place"])}</span>')
    count = f'<span class="hero__count" data-count="{e(h["date"])}" hidden></span>' if h.get("date") else ""
    return f"""          <div class="hero__slide">
            <div class="hero__card">
              {ph(h.get('photo', '16/9'), 'hero__ph')}
              <div class="hero__b">
                <span class="hero__label">{e(hero['label'])}</span>
                <h2 class="hero__t">{e(h['title'])}</h2>
                <div class="hero__meta">{''.join(chips)}</div>
                <p class="hero__x">{e(h['body'])}</p>
                <div class="hero__btns">
                  <a class="btn btn--primary" href="{e(link(h.get('cta_link')))}">{e(h['cta_label'])}</a>
                  {count}
                </div>
              </div>
            </div>
          </div>"""


def hero_block():
    slides = hero["slides"]
    body = "\n".join(hero_slide(h) for h in slides)
    if len(slides) == 1:
        return f'      <div class="hero__car hero__car--one">\n        <div class="hero__track">\n{body}\n        </div>\n      </div>'
    dot_parts = []
    for i in range(len(slides)):
        cur = ' aria-current="true"' if i == 0 else ''
        dot_parts.append(f'<button type="button" class="hero__dot" data-go="{i}"'
                         f' aria-label="{i + 1}枚目を表示"{cur}></button>')
    dots = "".join(dot_parts)
    return f"""      <div class="hero__car">
        <div class="hero__track" data-track tabindex="0" aria-label="注目のイベント">
{body}
        </div>
        <div class="hero__ctrl">
          <button class="hero__arw" type="button" data-go="prev" aria-label="前のイベント">
            <svg width="15" height="12" viewBox="0 0 15 12" fill="none" aria-hidden="true"><path d="M6 1L1 6l5 5M1 6h14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="hero__dots" data-dots>{dots}</div>
          <button class="hero__arw" type="button" data-go="next" aria-label="次のイベント">
            <svg width="15" height="12" viewBox="0 0 15 12" fill="none" aria-hidden="true"><path d="M9 1l5 5-5 5M14 6H0" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
      </div>"""


def about_block():
    body = "\n          ".join(f'<p class="about__p">{e(p)}</p>' for p in about["body"])
    pts = "\n            ".join(
        f'<div class="pt"><span class="pt__i" aria-hidden="true">{p["icon"]}</span>'
        f'<div><p class="pt__t">{e(p["title"])}</p><p class="pt__x">{e(p["text"])}</p></div></div>'
        for p in about["points"])
    return f"""      <div class="about__grid">
        {ph(about.get('photo', '4/5'), 'about__ph')}
        <div>
          <h3 class="about__t">{about['title']}</h3>
          {body}
          <div class="pts">
            {pts}
          </div>
        </div>
      </div>"""


def event_cards():
    out = []
    for ev in sorted(events, key=lambda x: x["date"])[:3]:   # トップは3件まで
        meta = "　".join(x for x in (ev.get("time", ""), ev.get("place", "")) if x)
        out.append(f"""        <a class="ev" href="{e(ev.get('link', '#'))}" data-ev-date="{e(ev['date'])}">
          {ph('4/3', 'ev__ph')}
          <div class="ev__b">
            <div class="ev__top">
              <span class="ev__date">{e(jp_date(ev['date']))}</span>
              <span class="chip chip--purple" data-soon hidden></span>
            </div>
            <h3 class="ev__t">{e(ev['title'])}</h3>
            <p class="ev__x">{e(ev.get('body', ''))}</p>
            <p class="ev__meta">{e(meta)}</p>
          </div>
        </a>""")
    return "\n".join(out)


def news_list():
    out = []
    for n in sorted(news, key=lambda x: x["date"], reverse=True)[:5]:
        y, m, d = n["date"].split("-")
        out.append(f"""        <a class="news__i" href="{e(n.get('link', '#'))}">
          <span class="news__m">
            <time class="news__d" datetime="{e(n['date'])}">{y}.{m}.{d}</time>
            <span class="chip chip--blue">{e(n.get('cat', 'お知らせ'))}</span>
          </span>
          <span class="news__t">{e(n['title'])}</span>
          <span class="news__x">{e(n.get('body', ''))}</span>
        </a>""")
    return "\n".join(out)


def juku_block():
    lis = "\n            ".join(f"<li>{e(p)}</li>" for p in juku["points"])
    btns = "\n            ".join(
        f'<a class="btn btn--{"primary" if b.get("style") == "primary" else "ghost"}" '
        f'href="{e(link(b.get("link")))}">{e(b["label"])}</a>'
        for b in juku["buttons"])
    return f"""      <div class="juku__grid">
        <div>
          <p class="juku__sub">{e(juku['sub'])}</p>
          <h2 class="juku__t">{e(juku['title'])}</h2>
          <p class="juku__x">{e(juku['body'])}</p>
          <ul class="juku__list">
            {lis}
          </ul>
          <div class="juku__btns">
            {btns}
          </div>
        </div>
        {ph(juku.get('photo', '3/2'), 'juku__ph')}
      </div>"""


def member_tiles():
    return "\n".join(
        f"""        <a class="mi mi--{e(m.get('tone', 'blue'))}" href="{e(link(m.get('link')))}">
          <span class="mi__i" aria-hidden="true">{m['icon']}</span>
          <span class="mi__t">{e(m['title'])}</span>
          <span class="mi__x">{e(m['text'])}</span>
        </a>""" for m in member["items"])


def faq_items():
    out = []
    for q in faq:
        body = [f"<p>{e(q['a'])}</p>"]
        if q.get("example"):
            body.append(f'<p class="q__ex">{q["example"]}</p>')   # 例文だけ HTML を許可
        if q.get("link_label"):
            body.append(f'<a class="link q__link" href="{e(link(q.get("link")))}">'
                        f'{e(q["link_label"])} <span aria-hidden="true">→</span></a>')
        out.append(f"""        <details class="q">
          <summary>
            <span class="q__q mr" aria-hidden="true">Q</span>
            <span>{e(q['q'])}</span>
            <span class="q__mk" aria-hidden="true"></span>
          </summary>
          <div class="q__a"><span class="mr" aria-hidden="true">A</span><div>{''.join(body)}</div></div>
        </details>""")
    return "\n".join(out)


# ---------------------------------------------------------------- 組み立て
draft = f'<p class="draft">{e(site["draft_note"])}</p>\n' if site.get("draft") else ""

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
<meta name="theme-color" content="#A8C9E5">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='15' fill='%23A8C9E5'/><circle cx='16' cy='16' r='5' fill='%23FFFCF6'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
{draft}
<header class="hd">
  <div class="wrap hd__in">
    <a class="logo mr" href="#top">
      <span class="logo__mark" aria-hidden="true"><span></span></span>
      <span>{e(site['name'])}</span>
    </a>
    <nav class="hd__nav" aria-label="メインメニュー">{nav_bar()}</nav>
    <a class="btn btn--primary btn--sm hd__cta" href="{e(L['join'])}">入会のご案内</a>
    <button class="burger" type="button" aria-expanded="false" aria-controls="kzn-menu"
            aria-label="メニューを開閉する"><i></i><i></i><i></i></button>
  </div>
</header>

<div class="ovl" id="kzn-menu" aria-hidden="true">
  <div class="ovl__in">
    <nav class="ovl__nav" aria-label="メニュー">
{nav_overlay()}
    </nav>
    <div class="ovl__foot">
      <a class="btn btn--primary" href="{e(L['join'])}">入会のご案内</a>
      <a class="btn btn--ghost" href="{e(site['tel_href'])}">電話する</a>
    </div>
  </div>
</div>

<main id="top">

  <!-- ============ 大カラム：注目のイベント ============ -->
  <section class="hero" id="hero">
    <div class="wrap hero__in">
{hero_block()}
    </div>
  </section>

  <!-- ============ キズナとは ============ -->
  <section class="sec" id="about">
    <div class="wrap">
{section_head('ABOUT', 'キズナとは')}
{about_block()}
    </div>
  </section>

  <!-- ============ 直近のイベント ============ -->
  <section class="sec" id="event">
    <div class="wrap">
{section_head('EVENT', '直近のイベント', '', ('すべて見る', '#'), row=True)}
      <div class="evs">
{event_cards()}
      </div>
    </div>
  </section>

  <!-- ============ お知らせ ============ -->
  <section class="sec" id="news">
    <div class="wrap wrap--n">
{section_head('NEWS', 'お知らせ', '', ('すべて見る', '#'), row=True)}
      <div class="news">
{news_list()}
      </div>
    </div>
  </section>

  <!-- ============ キズナ塾 ============ -->
  <section class="sec juku" id="juku">
    <div class="wrap">
{juku_block()}
    </div>
  </section>

  <!-- ============ 会員メニュー ============ -->
  <section class="sec mem" id="member">
    <div class="wrap">
{section_head('MEMBER', member['title'], member['sub'])}
      <div class="mem__grid">
{member_tiles()}
      </div>
      <p class="mem__note">会員証やポイントのことでお困りのときは、キズナ担当までご連絡ください。</p>
    </div>
  </section>

  <!-- ============ よくある質問 ============ -->
  <section class="sec" id="faq">
    <div class="wrap wrap--n">
{section_head('Q &amp; A', 'よくある質問')}
      <div class="faq__ch">
        {ill(faq_intro.get('illust', '1/1'), 'faq__ill')}
        <p class="faq__bub">{faq_intro['bubble']}</p>
      </div>
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
            <a class="btn btn--primary" href="{e(L['consult'])}">相談フォームを開く</a>
            <a class="btn btn--ghost" href="{e(L['join'])}">入会のご案内</a>
          </div>
          <div class="ct__tel">
            <a class="ct__num" href="{e(site['tel_href'])}">{e(site['tel'])}</a>
            <span class="ct__s">タップで電話がかけられます</span>
            <span class="ct__s" style="margin-top:8px">主催：{e(site['organizer'])} ／ 担当：{e(site['staff'])}</span>
          </div>
        </div>
      </div>
    </div>
  </section>

</main>

<footer class="ft">
  <div class="wrap">
    <div class="ft__top">
      <div>
        <p class="ft__logo mr"><span class="logo__mark" aria-hidden="true"><span></span></span>{e(site['name'])}</p>
        <p class="ft__x">{e(site['lead'])}</p>
      </div>
      <nav class="ft__nav" aria-label="フッターメニュー">
        {''.join(f'<a href="{h}">{e(t)}</a>' for t, h, _ in NAV)}
        <a href="{e(L['gakuto'])}">学徒サイトに戻る</a>
      </nav>
    </div>
    <div class="ft__btm">
      <span>&copy; {e(site['organizer'])}</span>
      <span>{e(site['name_en'])}</span>
    </div>
  </div>
</footer>

<div class="fx">
  <a class="btn btn--ghost" href="{e(site['tel_href'])}">電話する</a>
  <a class="btn btn--primary" href="{e(L['consult'])}">相談する</a>
</div>

<script src="assets/app.js" defer></script>
</body>
</html>
"""

out = ROOT / "index.html"
out.write_text(doc, encoding="utf-8")
print(f"書き出しました: {out}  ({len(doc.encode()):,} bytes)")
print(f"  イベント {len(events)} 件 / お知らせ {len(news)} 件 / "
      f"質問 {len(faq)} 件 / 会員メニュー {len(member['items'])} 件")
ph_count = doc.count('<div class="ph')
print(f"  写真の枠 {ph_count} か所（まだ画像は入っていません）")
