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
IMGDIR = ROOT / "assets" / "img"
WD = "日月火水木金土"
EN_WD = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def load(name):
    with open(DATA / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def e(s):
    """テキストとして安全に埋め込む（HTMLを書きたい箇所では使わない）"""
    return html.escape(str(s), quote=True)


site, hero, about, juku = load("site"), load("hero"), load("about"), load("juku")
member, events, news = load("member"), load("events"), load("news")
faq, faq_intro, photos = load("faq"), load("faq_intro"), load("photos")

L = site["links"]


def link(key):
    """data の link はキー名。site.json の links に無ければそのまま URL として扱う"""
    return L.get(key, key) if key else "#"


def pic(key, cls="", ratio=None, kind="photos"):
    """写真（またはイラスト）の枠。
    assets/img/<key>.(jpg|png|webp) があれば最優先。
    無ければ photos.json の url。それも空なら下地のグラデーションを出す。"""
    meta = photos.get(kind, {}).get(key, {})
    url = ""
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if (IMGDIR / f"{key}{ext}").exists():
            url = f"assets/img/{key}{ext}"
            break
    if not url:
        url = meta.get("url", "")
    style = f' style="aspect-ratio:{ratio}"' if ratio else ""
    if url:
        inner = (f'<img src="{e(url)}" alt="{e(meta.get("alt", ""))}" '
                 f'loading="lazy" decoding="async">')
    else:
        label = "イラストが入ります" if kind == "illust" else "写真が入ります"
        icon = "🎨" if kind == "illust" else "📷"
        inner = f'<div class="pic__none"><b>{icon}</b><span>{label}</span></div>'
    c = f" {cls}" if cls else ""
    return f'<div class="pic{c}"{style}>{inner}</div>'


def ymd(s):
    return (int(v) for v in s.split("-"))


def jp_date(s):
    y, m, d = ymd(s)
    return f"{m}月{d}日（{WD[datetime.date(y, m, d).weekday() - 6]}）"


def md(s):
    y, m, d = ymd(s)
    return f"{m:02d}.{d:02d}"


def en_wd(s):
    y, m, d = ymd(s)
    return EN_WD[datetime.date(y, m, d).weekday()]


NAV = [("キズナとは", "#about", "ABOUT"), ("イベント", "#event", "EVENT"),
       ("お知らせ", "#news", "NEWS"), ("キズナ塾", "#juku", "STUDY"),
       ("会員メニュー", "#member", "MEMBER"), ("よくある質問", "#faq", "Q&A"),
       ("お問い合わせ", "#contact", "CONTACT")]


# ---------------------------------------------------------------- 部品
def stage_slides():
    out = []
    for h in hero["slides"]:
        meta = []
        if h.get("date"):
            meta.append(f'<span>{e(jp_date(h["date"]))}</span>')
        if h.get("time"):
            meta.append(f'<span>{e(h["time"])}</span>')
        if h.get("place"):
            meta.append(f'<span>{e(h["place"])}</span>')
        count = (f'<span class="stage__count" data-count="{e(h["date"])}" hidden></span>'
                 if h.get("date") else "")
        out.append(f"""      <div class="stage__slide">
        {pic(h['pic'], 'stage__pic')}
        <div class="stage__b">
          <span class="cap cap--light">{e(hero['label'])}</span>
          <h2 class="stage__ttl">{e(h['title'])}</h2>
          <div class="stage__meta">{''.join(meta)}</div>
          <p class="stage__x">{e(h['body'])}</p>
          <div class="stage__btns">
            <a class="btn btn--ghost" href="{e(link(h.get('cta_link')))}">{e(h['cta_label'])}</a>
            {count}
          </div>
        </div>
      </div>""")
    return "\n".join(out)


def stage_nav():
    n = len(hero["slides"])
    if n < 2:
        return ""
    dots = []
    for i in range(n):
        cur = ' aria-current="true"' if i == 0 else ""
        dots.append(f'<button type="button" class="stage__dot" data-go="{i}" '
                    f'aria-label="{i + 1}枚目を表示"{cur}></button>')
    return f"""    <div class="stage__nav">
      {''.join(dots)}
      <button class="stage__arw" type="button" data-go="next" aria-label="次のイベント">
        <svg width="15" height="12" viewBox="0 0 15 12" fill="none" aria-hidden="true"><path d="M9 1l5 5-5 5M14 6H0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
    </div>"""


def about_points():
    out = []
    for i, p in enumerate(about["points"], 1):
        out.append(f"""        <div class="pt">
          <span class="pt__n">0{i}</span>
          <div>
            <h3 class="pt__t">{e(p['title'])}</h3>
            <p class="pt__x">{e(p['text'])}</p>
          </div>
        </div>""")
    return "\n".join(out)


def event_blocks():
    evs = sorted(events, key=lambda x: x["date"])[:3]
    if not evs:
        return ""
    f = evs[0]
    meta = "".join(f"<span>{e(x)}</span>" for x in (f.get("time", ""), f.get("place", "")) if x)
    big = f"""      <a class="big" href="{e(f.get('link', '#'))}" data-ev-date="{e(f['date'])}">
        {pic('ev1', 'big__pic')}
        <div class="big__b">
          <p><span class="big__d">{md(f['date'])}</span><span class="big__w">{en_wd(f['date'])}</span><span class="tag tag--p" data-soon hidden></span></p>
          <h3 class="big__t">{e(f['title'])}</h3>
          <p class="big__x">{e(f.get('body', ''))}</p>
          <div class="big__m">{meta}</div>
        </div>
      </a>"""
    rows = []
    for i, ev in enumerate(evs[1:], 2):
        m = "　".join(x for x in (ev.get("time", ""), ev.get("place", "")) if x)
        rows.append(f"""        <a class="row" href="{e(ev.get('link', '#'))}" data-ev-date="{e(ev['date'])}">
          {pic(f'ev{i}', 'row__pic')}
          <div>
            <p class="row__d">{md(ev['date'])}　{en_wd(ev['date'])}<span class="tag tag--g" data-soon hidden></span></p>
            <h3 class="row__t">{e(ev['title'])}</h3>
            <p class="row__m">{e(m)}</p>
          </div>
        </a>""")
    return big + '\n      <div class="rows">\n' + "\n".join(rows) + "\n      </div>"


def news_list():
    out = []
    for n in sorted(news, key=lambda x: x["date"], reverse=True)[:5]:
        y, m, d = n["date"].split("-")
        out.append(f"""        <a class="nw__i" href="{e(n.get('link', '#'))}">
          <span class="nw__m">
            <time class="nw__d" datetime="{e(n['date'])}">{y}.{m}.{d}</time>
            <span class="nw__c">{e(n.get('cat', 'お知らせ'))}</span>
          </span>
          <span class="nw__t">{e(n['title'])}</span>
          <span class="nw__x">{e(n.get('body', ''))}</span>
        </a>""")
    return "\n".join(out)


def juku_block():
    lis = "\n          ".join(f"<li><span>{e(p)}</span></li>" for p in juku["points"])
    btns = "\n          ".join(
        f'<a class="btn btn--{"primary" if b.get("style") == "primary" else "ghost"}" '
        f'href="{e(link(b.get("link")))}">{e(b["label"])}</a>' for b in juku["buttons"])
    return f"""      <div class="jk__panel">
        <span class="num jk__num">03</span>
        <h2 class="jk__t">{e(juku['title'])}</h2>
        <p class="jk__x">{e(juku['body'])}</p>
        <ul class="jk__list">
          {lis}
        </ul>
        <div class="jk__btns">
          {btns}
        </div>
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
    for i, q in enumerate(faq, 1):
        body = [f"<p>{e(q['a'])}</p>"]
        if q.get("example"):
            body.append(f'<p class="q__ex">{q["example"]}</p>')   # 例文だけ HTML を許可
        if q.get("link_label"):
            body.append(f'<a class="link q__link" href="{e(link(q.get("link")))}">'
                        f'{e(q["link_label"])} <span aria-hidden="true">→</span></a>')
        out.append(f"""        <details class="q">
          <summary>
            <span class="q__q" aria-hidden="true">Q{i:02d}</span>
            <span>{e(q['q'])}</span>
            <span class="q__mk" aria-hidden="true"></span>
          </summary>
          <div class="q__a"><span aria-hidden="true">A</span><div>{''.join(body)}</div></div>
        </details>""")
    return "\n".join(out)


# ---------------------------------------------------------------- 組み立て
draft = f'<p class="draft">{e(site["draft_note"])}</p>\n' if site.get("draft") else ""
nav_bar = "".join(f'<a href="{h}">{e(t)}</a>' for t, h, _ in NAV[:6])
nav_ovl = "\n".join(
    f'        <a href="{h}"><b>{e(t)}</b><small>{e(en)}</small></a>' for t, h, en in NAV)
ft_nav = "".join(f'<a href="{h}">{e(t)}</a>' for t, h, _ in NAV)

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
<meta name="theme-color" content="#1E2430">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='15' fill='%23A8C9E5'/><circle cx='16' cy='16' r='5' fill='%23FFFCF6'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="hd">
{draft}  <div class="wrap hd__in">
    <a class="logo" href="#top">
      <span class="logo__mark" aria-hidden="true"><span></span></span>
      <span>{e(site['name'])}</span>
    </a>
    <nav class="hd__nav" aria-label="メインメニュー">{nav_bar}</nav>
    <a class="btn btn--primary btn--sm hd__cta" href="{e(L['join'])}">入会のご案内</a>
    <button class="burger" type="button" aria-expanded="false" aria-controls="kzn-menu"
            aria-label="メニューを開閉する"><i></i><i></i><i></i></button>
  </div>
</header>

<div class="ovl" id="kzn-menu" aria-hidden="true">
  <div class="ovl__in">
    <nav class="ovl__nav" aria-label="メニュー">
{nav_ovl}
    </nav>
    <div class="ovl__foot">
      <a class="btn btn--ghost" href="{e(L['join'])}">入会のご案内</a>
      <a class="btn btn--light" href="{e(site['tel_href'])}">電話する</a>
    </div>
  </div>
</div>

<main id="top">

  <!-- ============ 注目のイベント（全幅写真） ============ -->
  <section class="stage" id="hero">
    <div class="stage__track" data-track tabindex="0" aria-label="注目のイベント">
{stage_slides()}
    </div>
{stage_nav()}
  </section>

  <!-- ============ 導入 ============ -->
  <section class="intro">
    <div class="wrap">
      <span class="cap">{e(site['name_en'])}</span>
      <h2 class="intro__t">{about['statement']}</h2>
      <p class="intro__x">{e(about['statement_x'])}</p>
    </div>
  </section>

  <!-- ============ キズナとは ============ -->
  <section class="sec ab" id="about">
    <div class="wrap">
      <div class="ab__grid">
        <div style="position:relative">
          {pic('about', 'ab__pic')}
          <span class="num ab__num">01</span>
        </div>
        <div class="ab__b">
          <span class="cap">About</span>
          <h2 class="ab__t">{e(about['title'])}</h2>
          <p class="ab__p">{e(about['body'][0])}</p>
          <p class="ab__p">{e(about['body'][1])}</p>
          <div class="pts">
{about_points()}
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ============ イベント ============ -->
  <section class="sec" id="event">
    <div class="wrap">
      <div class="ev__head">
        <div class="ev__hl">
          <span class="num">02</span>
          <div>
            <span class="cap">Event</span>
            <h2 class="ev__ttl">直近のイベント</h2>
          </div>
        </div>
        <a class="link" href="#">すべて見る <span aria-hidden="true">→</span></a>
      </div>
{event_blocks()}
    </div>
  </section>

  <!-- ============ お知らせ ============ -->
  <section class="sec" id="news">
    <div class="wrap wrap--n">
      <div class="ev__head">
        <div>
          <span class="cap">News</span>
          <h2 class="ev__ttl">お知らせ</h2>
        </div>
        <a class="link" href="#">すべて見る <span aria-hidden="true">→</span></a>
      </div>
      <div class="nw">
{news_list()}
      </div>
    </div>
  </section>

  <!-- ============ キズナ塾 ============ -->
  <section class="jk" id="juku">
    {pic('juku', 'jk__pic')}
    <div class="wrap" style="position:relative">
{juku_block()}
    </div>
  </section>

  <!-- ============ 会員メニュー ============ -->
  <section class="sec mem" id="member">
    <div class="wrap">
      <span class="cap">Member</span>
      <h2 class="mem__t">{e(member['title'])}</h2>
      <p class="mem__x">{e(member['sub'])}</p>
      <div class="mem__grid">
{member_tiles()}
      </div>
      <p class="mem__note">会員証やポイントのことでお困りのときは、キズナ担当までご連絡ください。</p>
    </div>
  </section>

  <!-- ============ よくある質問 ============ -->
  <section class="sec" id="faq">
    <div class="wrap wrap--n">
      <div class="ev__head">
        <div>
          <span class="cap">Q &amp; A</span>
          <h2 class="ev__ttl">よくある質問</h2>
        </div>
      </div>
      <div class="ch">
        {pic('faq', 'ch__ill ill', kind='illust')}
        <p class="ch__bub">{faq_intro['bubble']}</p>
      </div>
{faq_items()}
    </div>
  </section>

  <!-- ============ お問い合わせ ============ -->
  <section class="ct" id="contact">
    {pic('contact', 'ct__pic')}
    <div class="wrap wrap--n ct__in">
      <span class="cap cap--light">Contact</span>
      <h2 class="ct__t">まずは、お話を<br>聞かせてください。</h2>
      <p class="ct__x">キズナ担当へのご紹介、打ち合わせ、個別コース登録、無料体験のご相談を承っています。どんな小さなことでも、お気軽にご連絡ください。</p>
      <div class="ct__btns">
        <a class="btn btn--ghost" href="{e(L['consult'])}">相談フォームを開く</a>
        <a class="btn btn--light" href="{e(L['join'])}">入会のご案内</a>
      </div>
      <div class="ct__tel">
        <a class="ct__num" href="{e(site['tel_href'])}">{e(site['tel'])}</a>
        <span class="ct__s">タップで電話がかけられます</span>
        <span class="ct__s">主催：{e(site['organizer'])} ／ 担当：{e(site['staff'])}</span>
      </div>
    </div>
  </section>

</main>

<footer class="ft">
  <div class="wrap">
    <div class="ft__top">
      <div>
        <p class="ft__logo"><span class="logo__mark" aria-hidden="true"><span></span></span>{e(site['name'])}</p>
        <p class="ft__x">{e(site['lead'])}</p>
      </div>
      <nav class="ft__nav" aria-label="フッターメニュー">
        {ft_nav}<a href="{e(L['gakuto'])}">学徒サイトに戻る</a>
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
have = sum(1 for v in photos["photos"].values() if v.get("url"))
print(f"書き出しました: {out}  ({len(doc.encode()):,} bytes)")
print(f"  イベント {len(events)} 件 / お知らせ {len(news)} 件 / "
      f"質問 {len(faq)} 件 / 会員メニュー {len(member['items'])} 件")
print(f"  写真 {have}/{len(photos['photos'])} 枚が設定済み"
      f"（未設定のところは下地のグラデーションが出ます）")
