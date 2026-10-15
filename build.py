#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キズナ ポータル ビルダー
========================
data/*.json を読んで、サイトのページを一式書き出します。

    python3 build.py

書き出されるページ
    index.html                      トップ
    events/index.html               イベント一覧
    events/<slug>/index.html        イベント詳細（1件ずつ）
    news/index.html                 お知らせ一覧
    news/<slug>/index.html          お知らせ詳細（1件ずつ）

内容を直すときは data/ の JSON を編集して、このスクリプトを実行し、
git にコミットするだけです。見た目は assets/style.css が持っています。
"""

import datetime
import html
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
IMGDIR = ROOT / "assets" / "img"
WD = "日月火水木金土"
EN_WD = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
TODAY = datetime.date.today()


def load(name):
    with open(DATA / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def e(s):
    """テキストとして安全に埋め込む（HTMLを書きたい箇所では使わない）"""
    return html.escape(str(s), quote=True)


site, hero, about, juku = load("site"), load("hero"), load("about"), load("juku")
member, events, news = load("member"), load("events"), load("news")
faq, faq_intro, photos = load("faq"), load("faq_intro"), load("photos")
club = load("club")
point_d, staff_d, shindan = load("point"), load("staff"), load("shindan")

L = site["links"]

# いま書き出しているページの深さ（../ をいくつ付けるか）
PRE = ""


def u(path=""):
    """サイト内のリンクを、いまのページから見た相対パスにする"""
    if path.startswith(("http://", "https://", "tel:", "mailto:")):
        return path
    return (PRE + path) or "./"


UNSET = set()


def link(key):
    """data の link はキー名。site.json の links に無ければそのまま URL として扱う。
    URL が空のままのものは # にして、押しても別の場所へ飛ばないようにする。"""
    if not key:
        return "#"
    v = L.get(key, key)
    if not v:
        UNSET.add(key)
        return "#"
    # サイト内のページ（club/ など）は相対パスに直す
    if not v.startswith(("http://", "https://", "tel:", "mailto:", "#")):
        return u(v)
    return v


# ---------------------------------------------------------------- 日付
def ymd(s):
    return (int(v) for v in s.split("-"))


def as_date(s):
    y, m, d = ymd(s)
    return datetime.date(y, m, d)


def jp_date(s):
    d = as_date(s)
    return f"{d.month}月{d.day}日（{WD[d.weekday() - 6]}）"


def jp_full(s):
    d = as_date(s)
    return f"{d.year}年{d.month}月{d.day}日（{WD[d.weekday() - 6]}）"


def md(s):
    d = as_date(s)
    return f"{d.month:02d}.{d.day:02d}"


def en_wd(s):
    return EN_WD[as_date(s).weekday()]


def is_past(s):
    return as_date(s) < TODAY


# ---------------------------------------------------------------- 画像
def pic(key, cls="", ratio=None, kind="photos"):
    """写真（またはイラスト）。
    assets/img/<key>.(jpg|png|webp) があれば最優先。
    無ければ photos.json の url。それも空なら下地のグラデーションを出す。"""
    meta = photos.get(kind, {}).get(key, {})
    src = ""
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if (IMGDIR / f"{key}{ext}").exists():
            src = u(f"assets/img/{key}{ext}")
            break
    if not src:
        src = meta.get("url", "")
    style = f' style="aspect-ratio:{ratio}"' if ratio else ""
    if src:
        inner = (f'<img src="{e(src)}" alt="{e(meta.get("alt", ""))}" '
                 f'loading="lazy" decoding="async">')
    else:
        label, icon = {"illust": ("イラストが入ります", "🎨"),
                       "person": ("写真", "👤")}.get(kind, ("写真が入ります", "📷"))
        inner = f'<div class="pic__none"><b>{icon}</b><span>{label}</span></div>'
    c = f" {cls}" if cls else ""
    return f'<div class="pic{c}"{style}>{inner}</div>'


# ---------------------------------------------------------------- 共通の枠
NAV = [("キズナとは", "#about", "ABOUT"), ("イベント", "events/", "EVENT"),
       ("お知らせ", "news/", "NEWS"), ("キズナ塾", "#juku", "STUDY"),
       ("会員メニュー", "#member", "MEMBER"), ("よくある質問", "#faq", "Q&A"),
       ("お問い合わせ", "#contact", "CONTACT")]


def nav_href(h):
    """# で始まるものはトップページ内のアンカー"""
    return u("") + h if h.startswith("#") else u(h)


def shell(title, desc, body, extra_class=""):
    """ヘッダー・フッター・追従ボタンを含む、ページの外側"""
    draft = f'{"  "}<p class="draft">{e(site["draft_note"])}</p>\n' if site.get("draft") else ""
    nav_bar = "".join(f'<a href="{nav_href(h)}">{e(t)}</a>' for t, h, _ in NAV[:6])
    nav_ovl = "\n".join(
        f'        <a href="{nav_href(h)}"><b>{e(t)}</b><small>{e(en)}</small></a>'
        for t, h, en in NAV)
    ft_nav = "".join(f'<a href="{nav_href(h)}">{e(t)}</a>' for t, h, _ in NAV)
    gakuto_link = (f'<a href="{e(L["gakuto"])}">学徒サイトに戻る</a>' if L.get("gakuto") else "")
    cls = f' class="{extra_class}"' if extra_class else ""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#1E2430">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='15' fill='%23A8C9E5'/><circle cx='16' cy='16' r='5' fill='%23FFFCF6'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{u('assets/style.css')}">
</head>
<body{cls}>
<header class="hd">
{draft}  <div class="wrap hd__in">
    <a class="logo" href="{u('')}">
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

{body}

<footer class="ft">
  <div class="wrap">
    <div class="ft__top">
      <div>
        <p class="ft__logo"><span class="logo__mark" aria-hidden="true"><span></span></span>{e(site['name'])}</p>
        <p class="ft__x">{e(site['lead'])}</p>
      </div>
      <nav class="ft__nav" aria-label="フッターメニュー">
        {ft_nav}{gakuto_link}
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

<script src="{u('assets/app.js')}" defer></script>
</body>
</html>
"""


def crumb(*parts):
    """パンくず。parts は (表示名, リンク or None)"""
    out = [f'<a href="{u("")}">ホーム</a>']
    for label, href in parts:
        out.append('<span aria-hidden="true">/</span>')
        out.append(f'<a href="{href}">{e(label)}</a>' if href else f"<span>{e(label)}</span>")
    return f'<nav class="crumb" aria-label="現在位置">{"".join(out)}</nav>'


def page_head(cap, title, lead=""):
    x = f'<p class="phead__x">{e(lead)}</p>' if lead else ""
    return f"""      <div class="phead">
        <span class="cap">{cap}</span>
        <h1 class="phead__t">{e(title)}</h1>
        {x}
      </div>"""


# ================================================================ トップページ
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
            <a class="btn btn--ghost" href="{u("events/" + h["event"] + "/") if h.get("event") else e(link(h.get("cta_link")))}">{e(h['cta_label'])}</a>
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
    return "\n".join(f"""        <div class="pt">
          <span class="pt__n">0{i}</span>
          <div>
            <h3 class="pt__t">{e(p['title'])}</h3>
            <p class="pt__x">{e(p['text'])}</p>
          </div>
        </div>""" for i, p in enumerate(about["points"], 1))


def ev_url(ev):
    return u(f"events/{ev['slug']}/")


def nw_url(n):
    return u(f"news/{n['slug']}/")


def event_blocks():
    evs = [x for x in sorted(events, key=lambda x: x["date"]) if not is_past(x["date"])][:3]
    if not evs:
        evs = sorted(events, key=lambda x: x["date"], reverse=True)[:3]
    f = evs[0]
    meta = "".join(f"<span>{e(x)}</span>" for x in (f.get("time", ""), f.get("place", "")) if x)
    big = f"""      <a class="big" href="{ev_url(f)}" data-ev-date="{e(f['date'])}">
        {pic(f.get('pic', 'ev1'), 'big__pic')}
        <div class="big__b">
          <p><span class="big__d">{md(f['date'])}</span><span class="big__w">{en_wd(f['date'])}</span><span class="tag tag--p" data-soon hidden></span></p>
          <h3 class="big__t">{e(f['title'])}</h3>
          <p class="big__x">{e(f.get('body', ''))}</p>
          <div class="big__m">{meta}</div>
        </div>
      </a>"""
    rows = []
    for ev in evs[1:]:
        m = "　".join(x for x in (ev.get("time", ""), ev.get("place", "")) if x)
        rows.append(f"""        <a class="row" href="{ev_url(ev)}" data-ev-date="{e(ev['date'])}">
          {pic(ev.get('pic', 'ev2'), 'row__pic')}
          <div>
            <p class="row__d">{md(ev['date'])}　{en_wd(ev['date'])}<span class="tag tag--g" data-soon hidden></span></p>
            <h3 class="row__t">{e(ev['title'])}</h3>
            <p class="row__m">{e(m)}</p>
          </div>
        </a>""")
    if not rows:
        return big
    return big + '\n      <div class="rows">\n' + "\n".join(rows) + "\n      </div>"


def news_items(limit=5):
    out = []
    for n in sorted(news, key=lambda x: x["date"], reverse=True)[:limit]:
        y, m, d = n["date"].split("-")
        out.append(f"""        <a class="nw__i" href="{nw_url(n)}">
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
        f'href="{e(link(b.get("link")))}"'
        f'{" target=_blank rel=noopener" if b.get("external") else ""}>{e(b["label"])}'
        f'{" ↗" if b.get("external") else ""}</a>' for b in juku["buttons"])
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


def contact_section():
    return f"""  <section class="ct" id="contact">
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
        <span class="ct__s">ご意見・ご要望は <a href="mailto:{e(site['email'])}">{e(site['email'])}</a> へ</span>
        <span class="ct__s">主催：{e(site['organizer'])} ／ 担当：{e(site['staff'])}</span>
      </div>
    </div>
  </section>"""


def build_index():
    body = f"""<main id="top">

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
        <a class="link" href="{u('events/')}">すべて見る <span aria-hidden="true">→</span></a>
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
        <a class="link" href="{u('news/')}">すべて見る <span aria-hidden="true">→</span></a>
      </div>
      <div class="nw">
{news_items(5)}
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

{contact_section()}

</main>"""
    return shell(site["title"], site["description"], body)


# ================================================================ イベント
def ev_card(ev, past=False):
    m = "　".join(x for x in (ev.get("time", ""), ev.get("place", "")) if x)
    soon = '' if past else '<span class="tag tag--g" data-soon hidden></span>'
    cls = " el--past" if past else ""
    return f"""        <a class="el{cls}" href="{ev_url(ev)}" data-ev-date="{e(ev['date'])}">
          {pic(ev.get('pic', 'ev1'), 'el__pic')}
          <div class="el__b">
            <p class="el__d"><b>{md(ev['date'])}</b><span>{as_date(ev['date']).year}　{en_wd(ev['date'])}</span>{soon}</p>
            <h2 class="el__t">{e(ev['title'])}</h2>
            <p class="el__x">{e(ev.get('body', ''))}</p>
            <p class="el__m">{e(m)}</p>
          </div>
        </a>"""


def build_events():
    upcoming = [x for x in sorted(events, key=lambda x: x["date"]) if not is_past(x["date"])]
    past = [x for x in sorted(events, key=lambda x: x["date"], reverse=True) if is_past(x["date"])]
    blocks = []
    if upcoming:
        blocks.append('      <h2 class="group">これからのイベント</h2>\n'
                      '      <div class="els">\n' +
                      "\n".join(ev_card(x) for x in upcoming) + "\n      </div>")
    else:
        blocks.append('      <p class="empty">いま予定しているイベントはありません。'
                      '決まりしだい、このページでお知らせします。</p>')
    if past:
        blocks.append('      <h2 class="group group--past">終わったイベント</h2>\n'
                      '      <div class="els">\n' +
                      "\n".join(ev_card(x, past=True) for x in past) + "\n      </div>")
    body = f"""<main class="page">
  <div class="wrap wrap--n">
{crumb(("イベント", None))}
{page_head('Event', 'イベント', '参加したいものが見つかったら、申し込みのご案内をご覧ください。')}
{chr(10).join(blocks)}
  </div>
</main>"""
    return shell(f"イベント｜{site['name']}",
                 "キズナのイベント一覧です。これからの予定と、終わったイベントの記録をご覧いただけます。",
                 body, "sub")


def build_event(ev):
    rows = [("日時", f"{jp_full(ev['date'])}　{ev.get('time', '')}".strip()),
            ("場所", ev.get("place", "")),
            ("対象", ev.get("target", "")),
            ("参加費", ev.get("fee", "")),
            ("持ちもの", ev.get("bring", ""))]
    if ev.get("deadline"):
        rows.append(("申込しめきり", jp_full(ev["deadline"])))
    spec = "\n".join(
        f'          <div class="spec__r"><dt>{e(k)}</dt><dd>{e(v)}</dd></div>'
        for k, v in rows if v)
    paras = "\n".join(f'        <p>{e(p)}</p>' for p in ev.get("detail", [ev.get("body", "")]))
    past = is_past(ev["date"])
    cta = ("" if past else f"""      <div class="detail__cta">
        <a class="btn btn--primary" href="{e(link(ev.get('apply')))}">このイベントに申し込む</a>
        <a class="btn btn--ghost" href="{e(L['consult'])}">まず相談する</a>
      </div>""")
    note = ('      <p class="detail__past">このイベントは終了しました。'
            '次の予定は<a href="' + u("events/") + '">イベント一覧</a>をご覧ください。</p>'
            if past else "")
    tag = f'<span class="tag tag--p">{e(ev["tag"])}</span>' if ev.get("tag") else ""
    body = f"""<main class="page">
  <div class="wrap wrap--n">
{crumb(("イベント", u("events/")), (ev["title"], None))}
  </div>
  <div class="wrap">
    {pic(ev.get('pic', 'ev1'), 'detail__pic')}
  </div>
  <div class="wrap wrap--n">
    <article class="detail">
      <p class="detail__d"><b>{md(ev['date'])}</b><span>{as_date(ev['date']).year}　{en_wd(ev['date'])}</span>{tag}</p>
      <h1 class="detail__t">{e(ev['title'])}</h1>
{note}
      <dl class="spec">
{spec}
      </dl>
      <div class="detail__b">
{paras}
      </div>
{cta}
      <p class="detail__back"><a class="link" href="{u('events/')}">
        <span aria-hidden="true">←</span> イベント一覧にもどる</a></p>
    </article>
  </div>
</main>"""
    return shell(f"{ev['title']}｜{site['name']}", ev.get("body", ""), body, "sub")


# ================================================================ お知らせ
def build_news():
    body = f"""<main class="page">
  <div class="wrap wrap--n">
{crumb(("お知らせ", None))}
{page_head('News', 'お知らせ', 'キズナからのご案内です。')}
    <div class="nw">
{news_items(100)}
    </div>
  </div>
</main>"""
    return shell(f"お知らせ｜{site['name']}",
                 "キズナからのお知らせ一覧です。", body, "sub")


def build_news_item(n):
    paras = "\n".join(f'        <p>{e(p)}</p>' for p in n.get("detail", [n.get("body", "")]))
    y, m, d = n["date"].split("-")
    body = f"""<main class="page">
  <div class="wrap wrap--n">
{crumb(("お知らせ", u("news/")), (n["title"], None))}
    <article class="detail detail--news">
      <p class="detail__d"><time datetime="{e(n['date'])}">{y}.{m}.{d}</time>
        <span class="tag tag--g">{e(n.get('cat', 'お知らせ'))}</span></p>
      <h1 class="detail__t">{e(n['title'])}</h1>
      <div class="detail__b">
{paras}
      </div>
      <div class="detail__cta">
        <a class="btn btn--ghost" href="{e(L['consult'])}">このことについて相談する</a>
      </div>
      <p class="detail__back"><a class="link" href="{u('news/')}">
        <span aria-hidden="true">←</span> お知らせ一覧にもどる</a></p>
    </article>
  </div>
</main>"""
    return shell(f"{n['title']}｜{site['name']}", n.get("body", ""), body, "sub")


# ================================================================ キズナクラブ
def club_cards():
    out = []
    for c in club["courses"]:
        gifts = "".join(f"<li>{e(g)}</li>" for g in c["gifts"])
        note = f'<span class="cc__note">{e(c["fee_note"])}</span>' if c.get("fee_note") else ""
        out.append(f"""        <div class="cc cc--{e(c['tone'])}">
          <h3 class="cc__n">{e(c['name'])}</h3>
          <dl class="cc__dl">
            <div><dt>個別レッスン</dt><dd><b>{e(c['lesson'])}</b></dd></div>
            <div><dt>対象</dt><dd>{e(c['target'])}</dd></div>
            <div><dt>会費</dt><dd><b>{e(c['fee'])}</b>{note}</dd></div>
            <div><dt>配付物</dt><dd><ul class="cc__g">{gifts}</ul></dd></div>
          </dl>
        </div>""")
    return "\n".join(out)


def club_can():
    return "\n".join(f"""        <div class="pt">
          <span class="pt__n">0{i}</span>
          <div>
            <h3 class="pt__t">{e(c['title'])}</h3>
            <p class="pt__x">{e(c['text'])}</p>
          </div>
        </div>""" for i, c in enumerate(club["can"], 1))


def fee_ways():
    out = []
    for i, w in enumerate(club["fee"]["ways"], 1):
        steps = "".join(f"<li>{e(x)}</li>" for x in w["steps"])
        acc = ""
        if w.get("account"):
            a = w["account"]
            acc = f"""      <dl class="acc">
        <div><dt>金融機関</dt><dd>{e(a['bank'])}</dd></div>
        <div><dt>記号番号</dt><dd><b>{e(a['no'])}</b></dd></div>
        <div><dt>加入者名</dt><dd>{e(a['name'])}</dd></div>
      </dl>"""
        notes = ""
        if w.get("notes"):
            notes = ('<ul class="warn">'
                     + "".join(f"<li>{e(n)}</li>" for n in w["notes"]) + "</ul>")
        out.append(f"""      <div class="way">
        <h3 class="way__t"><span class="way__n">{i}</span>{e(w['title'])}</h3>
        <ul class="ticks">{steps}</ul>
{acc}
        {notes}
      </div>""")
    return "\n".join(out)


def build_club():
    form_can = "".join(f"<li>{e(x)}</li>" for x in club["form_can"])
    benefits = "".join(
        f'<span class="chipb">{e(b["name"])}'
        + (f'<small>{e(b["note"])}</small>' if b.get("note") else "")
        + "</span>" for b in club["benefits"])
    body = f"""<main class="page">
  <div class="wrap wrap--n">
{crumb(("キズナクラブ", None))}
{page_head('Club', 'キズナクラブ', club['lead'])}
  </div>

  <div class="wrap">
    <div class="ccs">
{club_cards()}
    </div>
  </div>

  <div class="wrap wrap--n">
    <h2 class="group">クラブでできること</h2>
    <div class="pts">
{club_can()}
    </div>

    <h2 class="group" id="benefits">会員特典</h2>
    <p class="sect__x">キズナクラブの会員の方は、次の特典を受けられます。</p>
    <div class="chips">{benefits}</div>
    <p class="sect__note">{e(club['benefits_note'])}</p>

    <h2 class="group">申し込み・変更・退会</h2>
    <p class="sect__x">次の手続きは、すべて「キズナ申し込み窓口」からできます。</p>
    <ul class="ticks">{form_can}</ul>
    <div class="detail__cta">
      <a class="btn btn--primary" href="{e(L['join'])}">キズナ申し込み窓口をひらく</a>
      <a class="btn btn--ghost" href="{e(L['consult'])}">まず担当に相談する</a>
    </div>

    <h2 class="group" id="fee">会費の納め方</h2>
    <p class="sect__x">{e(club['fee']['lead'])}</p>
{fee_ways()}

    <p class="detail__back"><a class="link" href="{u('')}">
      <span aria-hidden="true">←</span> ホームにもどる</a></p>
  </div>
</main>"""
    return shell(f"キズナクラブ｜{site['name']}",
                 "キズナクラブは0歳から24歳までどなたでも入れます。会費・コースのちがい・申し込み方法をご案内します。",
                 body, "sub")


# ================================================================ キズナカード・ポイント
def pt_table():
    out = []
    for g in point_d["table"]:
        rows = "".join(
            f'<div class="ptt__r"><dt>{e(k)}</dt><dd><b>{e(v)}</b>pt</dd></div>' for k, v in g["rows"])
        note = f'<p class="ptt__n">{e(g["note"])}</p>' if g.get("note") else ""
        body = f'<dl class="ptt__dl">{rows}</dl>' if rows else ""
        out.append(f"""        <div class="ptt">
          <h3 class="ptt__t">{e(g['name'])}</h3>
          {body}{note}
        </div>""")
    return "\n".join(out)


def build_point():
    ways = "\n".join(f"""          <div class="pt">
            <span class="pt__n">0{i}</span>
            <div><h3 class="pt__t">{e(w['title'])}</h3><p class="pt__x">{e(w['text'])}</p></div>
          </div>""" for i, w in enumerate(point_d["make"]["ways"], 1))
    notes = "".join(f"<li>{e(n)}</li>" for n in point_d["make"]["notes"])
    uses = "\n".join(f"""          <div class="pt">
            <span class="pt__n">0{i}</span>
            <div><h3 class="pt__t">{e(w['title'])}</h3><p class="pt__x">{e(w['text'])}</p></div>
          </div>""" for i, w in enumerate(point_d["use"], 1))
    about = "".join(f'<p class="sect__x">{e(x)}</p>' for x in point_d["about"])
    present = "".join(f'<p class="sect__x">{e(x)}</p>' for x in point_d["present"])
    donate = "".join(f'<p class="sect__x">{e(x)}</p>' for x in point_d["donate"])
    body = f"""<main class="page">
  <div class="wrap wrap--n">
{crumb(("キズナカード・キズナポイント", None))}
{page_head('Point', 'キズナカード・キズナポイント', point_d['lead'])}

    <h2 class="group">キズナカードとは</h2>
    {about}

    <h2 class="group">カードの作り方</h2>
    <p class="sect__x">作り方は2通りあります。</p>
    <div class="pts">
{ways}
    </div>
    <div class="detail__cta">
      <a class="btn btn--primary" href="{e(L['card_apply'])}" target="_blank" rel="noopener">キズナカードを申し込む ↗</a>
    </div>
    <ul class="ticks" style="margin-top:26px">{notes}</ul>

    <h2 class="group">カードの使い方</h2>
    <div class="pts">
{uses}
    </div>
    <div class="detail__cta">
      <a class="btn btn--primary" href="{e(L['point'])}" target="_blank" rel="noopener">いまのポイントを見る ↗</a>
      <a class="btn btn--ghost" href="{e(L['point_apply'])}" target="_blank" rel="noopener">ポイントを申請する ↗</a>
    </div>

    <h2 class="group">キズナポイント表</h2>
    <div class="ptts">
{pt_table()}
    </div>

    <h2 class="group">プレゼントについて</h2>
    {present}
    <div class="detail__cta">
      <a class="btn btn--primary" href="{e(L['present'])}" target="_blank" rel="noopener">プレゼント一覧を見る ↗</a>
    </div>

    <h2 class="group">プレゼントのご寄付について</h2>
    {donate}

    <p class="detail__back"><a class="link" href="{u('')}">
      <span aria-hidden="true">←</span> ホームにもどる</a></p>
  </div>
</main>"""
    return shell(f"キズナカード・キズナポイント｜{site['name']}",
                 "キズナカードの作り方・使い方と、キズナポイント表、プレゼントの交換についてご案内します。",
                 body, "sub")


# ================================================================ スタッフ紹介
def build_staff():
    st = staff_d["staff"]
    sp = staff_d["supporter"]
    people = "\n".join(f"""          <div class="pr">
            {pic('person', 'pr__ph', kind='person')}
            <div><p class="pr__nick">{e(p['nick'])}</p><p class="pr__name">{e(p['name'])}</p></div>
          </div>""" for p in st["people"])
    areas = []
    for a in sp["areas"]:
        lis = "".join(f'<li><b>{e(x["nick"])}</b><span>{e(x["job"])}</span></li>' for x in a["people"])
        areas.append(f"""          <div class="area">
            <h3 class="area__t">{e(a['area'])}</h3>
            <ul class="area__l">{lis}</ul>
          </div>""")
    body = f"""<main class="page">
  <div class="wrap wrap--n">
{crumb(("スタッフ・サポーター紹介", None))}
{page_head('Member', 'スタッフ・サポーター紹介', staff_d['lead'])}

    <h2 class="group">{e(st['title'])}</h2>
    <p class="sect__x">{e(st['text'])}</p>
  </div>
  <div class="wrap">
    <div class="prs">
{people}
    </div>
  </div>
  <div class="wrap wrap--n">
    <h2 class="group">{e(sp['title'])}</h2>
    <p class="sect__x">{e(sp['text'])}</p>
    <div class="areas">
{chr(10).join(areas)}
    </div>

    <div class="detail__cta">
      <a class="btn btn--ghost" href="{e(L['consult'])}" target="_blank" rel="noopener">スタッフに相談する ↗</a>
    </div>
    <p class="detail__back"><a class="link" href="{u('')}">
      <span aria-hidden="true">←</span> ホームにもどる</a></p>
  </div>
</main>"""
    return shell(f"スタッフ・サポーター紹介｜{site['name']}",
                 "キズナクラブのお子さんたちを支えている、キズナスタッフとキズナサポーターをご紹介します。",
                 body, "sub")


# ================================================================ 才能診断
def build_shindan():
    spec = "".join(f'<div class="spec__r"><dt>{e(k)}</dt><dd>{e(v)}</dd></div>'
                   for k, v in shindan["spec"])
    g = shindan["gifts"]
    gifts = "".join(f"""          <div class="gift gift--{e(x['tone'])}">
            <span class="gift__m">{e(x['mark'])}</span>
            <p class="gift__n">{e(x['name'])}</p>
          </div>""" for x in g["items"])
    lt = shindan["letter"]
    body = f"""<main class="page">
  <div class="wrap wrap--n">
{crumb(("キズナ式 才能診断", None))}
    <span class="cap">{e(shindan['label'])}</span>
    <h1 class="phead__t" style="margin-top:10px">{e(shindan['title'])}</h1>
    <p class="shin__sub">{e(shindan['sub'])}</p>
    <p class="phead__x" style="max-width:38em">{e(shindan['lead'])}</p>

    <dl class="spec" style="margin-top:clamp(28px,4vw,44px)">{spec}</dl>

    <div class="detail__cta" style="border-top:0;padding-top:0">
      <a class="btn btn--primary" href="{e(L['shindan'])}" target="_blank" rel="noopener">診断をはじめる ↗</a>
      <a class="btn btn--ghost" href="#letter">家族に送る文章を見る</a>
    </div>

    <h2 class="group">{e(g['title'])}</h2>
    <p class="sect__x">{e(g['text'])}</p>
    <div class="gifts">
{gifts}
    </div>

    <h2 class="group" id="letter">{e(lt['title'])}</h2>
    <p class="sect__x">{e(lt['text'])}</p>
    <p class="sect__x"><b>{e(lt['step'])}</b></p>

    <div class="copy">
      <div class="copy__h">
        <span>1. {e(lt['flyer_label'])}</span>
        <button class="copy__b" type="button" data-copy="kzn-flyer">コピー</button>
      </div>
      <pre class="copy__t" id="kzn-flyer">{e(lt['flyer'])}</pre>
    </div>

    <div class="copy">
      <div class="copy__h">
        <span>2. 本文</span>
        <button class="copy__b" type="button" data-copy="kzn-letter">コピー</button>
      </div>
      <pre class="copy__t" id="kzn-letter">{e(lt['body'])}</pre>
    </div>

    <div class="detail__cta">
      <a class="btn btn--primary" href="{e(L['shindan'])}" target="_blank" rel="noopener">診断をはじめる ↗</a>
      <a class="btn btn--ghost" href="{e(L['consult'])}" target="_blank" rel="noopener">担当に相談する ↗</a>
    </div>
    <p class="detail__back"><a class="link" href="{u('')}">
      <span aria-hidden="true">←</span> ホームにもどる</a></p>
  </div>
</main>"""
    return shell(f"キズナ式 才能診断｜{site['name']}", shindan["lead"][:110], body, "sub")


# ================================================================ 書き出し
def write(rel_path, depth, fn):
    """rel_path: '' なら index.html、'events' なら events/index.html"""
    global PRE
    PRE = "../" * depth
    out = ROOT / rel_path / "index.html" if rel_path else ROOT / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fn(), encoding="utf-8")
    return out


# 前回のビルドで作った詳細ページを掃除する（slug を変えたときの残骸を残さない）
for d in ("events", "news", "club", "point", "staff", "shindan"):
    if (ROOT / d).exists():
        shutil.rmtree(ROOT / d)

made = [write("", 0, build_index),
        write("events", 1, build_events),
        write("news", 1, build_news),
        write("club", 1, build_club),
        write("point", 1, build_point),
        write("staff", 1, build_staff),
        write("shindan", 1, build_shindan)]
for ev in events:
    made.append(write(f"events/{ev['slug']}", 2, lambda ev=ev: build_event(ev)))
for n in news:
    made.append(write(f"news/{n['slug']}", 2, lambda n=n: build_news_item(n)))

total = sum(len(p.read_bytes()) for p in made)
print(f"{len(made)} ページを書き出しました（合計 {total:,} bytes）")
for p in made:
    print(f"  {p.relative_to(ROOT)}")
have = sum(1 for v in photos["photos"].values() if v.get("url"))
print(f"写真 {have}/{len(photos['photos'])} 枚が設定済み")
empty = sorted(k for k, v in L.items() if not v)
if empty:
    print("URL が未設定のリンク:", ", ".join(empty), "（押しても何も起きません）")
