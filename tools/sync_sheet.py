#!/usr/bin/env python3
"""Google スプレッドシートの内容を data/*.json に書き出す。

使いかた:
    python3 tools/sync_sheet.py            # ネットからシートを取ってくる
    python3 tools/sync_sheet.py --local t  # t/ の中の CSV から読む（テスト用）

シートIDは tools/sheet.config.json か、環境変数 SHEET_ID で指定します。
おかしな入力があったら、何も書かずにエラーで止まります（壊れた内容が公開されない）。
"""
import csv, io, json, os, re, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONF = json.loads((ROOT / "tools" / "sheet.config.json").read_text(encoding="utf-8"))
SHEET_ID = os.environ.get("SHEET_ID") or CONF.get("sheet_id", "")

TAB_EVENTS, TAB_NEWS, TAB_HERO = "イベント", "お知らせ", "トップのスライド"

errors, warnings = [], []


def err(tab, row, msg):
    where = f"{tab} {row}行目" if row else tab
    errors.append(f"{where}：{msg}")


# ---------------------------------------------------------------- 取得
def fetch(tab):
    """シート1枚を取ってきて、見出し行をキーにした辞書の配列にする。"""
    if LOCAL:
        text = (LOCAL / f"{tab}.csv").read_text(encoding="utf-8")
    else:
        url = ("https://docs.google.com/spreadsheets/d/" + SHEET_ID +
               "/gviz/tq?tqx=out:csv&sheet=" + urllib.parse.quote(tab))
        with urllib.request.urlopen(url, timeout=60) as r:
            if "text/csv" not in r.headers.get("Content-Type", ""):
                sys.exit(f"[失敗] シート「{tab}」を読めませんでした。"
                         "シート名が違うか、共有設定が「リンクを知っている全員が閲覧可」に"
                         "なっていない可能性があります。")
            text = r.read().decode("utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        sys.exit(f"[失敗] シート「{tab}」が空です。")
    head = [c.strip() for c in rows[0]]
    out = []
    for i, r in enumerate(rows[1:], start=2):          # 2行目＝最初のデータ行
        rec = {head[j]: (r[j].strip() if j < len(r) else "") for j in range(len(head))}
        if any(rec.values()):
            rec["_row"] = i
            out.append(rec)
    return out


# ---------------------------------------------------------------- 整形
def on(v):
    """公開チェックが入っているか。チェックボックス・○・はい などを受け付ける。"""
    return v.strip().lower() in ("true", "○", "〇", "o", "yes", "y", "1", "公開", "表示", "はい", "✓")


GVIZ_DATE = re.compile(r"Date\((\d+),(\d+),(\d+)")


def date(v, tab, row, field, required=True):
    """いろいろな書き方の日付を YYYY-MM-DD にそろえる。"""
    v = v.strip()
    if not v:
        if required:
            err(tab, row, f"{field}が空です")
        return ""
    m = GVIZ_DATE.match(v)                              # Date(2026,9,26) 形式
    if m:
        y, mo, d = int(m[1]), int(m[2]) + 1, int(m[3])
        return f"{y:04d}-{mo:02d}-{d:02d}"
    m = re.fullmatch(r"(\d{4})[-/年.](\d{1,2})[-/月.](\d{1,2})日?", v)
    if m:
        return f"{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}"
    err(tab, row, f"{field}「{v}」が日付として読めません。2026-11-03 の形で書いてください")
    return ""


def paras(v):
    """セルの改行を段落の配列にする。空行はまとめて1つの区切りとして扱う。"""
    return [p.strip() for p in re.split(r"\n\s*\n|\n", v.replace("\r\n", "\n")) if p.strip()]


SLUG_OK = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def slug(v, fallback, tab, row, used):
    v = v.strip().lower()
    if not v:
        v = fallback
    if not SLUG_OK.fullmatch(v):
        err(tab, row, f"URL名「{v}」は使えません。半角の小文字・数字・ハイフンだけにしてください")
        return v
    if v in used:
        err(tab, row, f"URL名「{v}」が他の行と重なっています")
    used.add(v)
    return v


def put(d, key, val):
    if val:
        d[key] = val


# ---------------------------------------------------------------- 各シート
def build_events(rows):
    out, used = [], set()
    for r in rows:
        if not on(r.get("公開", "")):
            continue
        n, t = r["_row"], TAB_EVENTS
        d = date(r.get("日付", ""), t, n, "日付")
        title = r.get("タイトル", "").strip()
        if not title:
            err(t, n, "タイトルが空です")
        ev = {"slug": slug(r.get("URL名", ""), f"event-{d}", t, n, used),
              "date": d, "title": title}
        for key, col in (("time", "時間"), ("place", "場所"), ("tag", "タグ"),
                         ("target", "対象"), ("fee", "参加費"), ("bring", "持ちもの"),
                         ("apply", "申込フォーム"), ("pic", "写真"),
                         ("body", "一覧に出る文章")):
            put(ev, key, r.get(col, "").strip())
        dl = r.get("申込締切", "").strip()
        if dl:
            put(ev, "deadline", date(dl, t, n, "申込締切", required=False))
        p = paras(r.get("詳細ページの本文", ""))
        if p:
            ev["detail"] = p
        if not ev.get("body"):
            warnings.append(f"{t} {n}行目：一覧に出る文章が空です（一覧でさみしく見えます）")
        out.append(ev)
    out.sort(key=lambda x: x["date"])                   # 日付の早い順
    return out


def build_news(rows):
    out, used = [], set()
    for r in rows:
        if not on(r.get("公開", "")):
            continue
        n, t = r["_row"], TAB_NEWS
        d = date(r.get("日付", ""), t, n, "日付")
        title = r.get("タイトル", "").strip()
        if not title:
            err(t, n, "タイトルが空です")
        it = {"slug": slug(r.get("URL名", ""), f"news-{d}", t, n, used),
              "date": d, "title": title}
        put(it, "cat", r.get("分類", "").strip())
        put(it, "body", r.get("一覧に出る文章", "").strip())
        p = paras(r.get("詳細ページの本文", ""))
        if p:
            it["detail"] = p
        out.append(it)
    out.sort(key=lambda x: x["date"], reverse=True)     # 新しい順
    return out


def build_hero(rows, events):
    """空欄のところは、つないだイベントの内容をそのまま使う。"""
    by_slug = {e["slug"]: e for e in events}
    label = json.loads((DATA / "hero.json").read_text(encoding="utf-8")).get("label", "注目のイベント")
    slides = []
    for i, r in enumerate(rows):
        if not on(r.get("表示", "")):
            continue
        n, t = r["_row"], TAB_HERO
        ref = r.get("つなぐイベントのURL名", "").strip().lower()
        src = {}
        if ref:
            src = by_slug.get(ref, {})
            if not src:
                err(t, n, f"「{ref}」というURL名のイベントが、公開中のイベントにありません")
        s = {}
        s["title"] = r.get("タイトル", "").strip() or src.get("title", "")
        raw_date = r.get("日付", "").strip()
        s["date"] = date(raw_date, t, n, "日付", required=False) if raw_date else src.get("date", "")
        s["time"] = r.get("時間", "").strip() or src.get("time", "")
        s["place"] = r.get("場所", "").strip() or src.get("place", "")
        s["body"] = r.get("文章", "").strip() or src.get("body", "")
        s["cta_label"] = r.get("ボタンの文字", "").strip() or "このイベントのくわしい内容"
        s["pic"] = r.get("写真", "").strip() or f"hero{len(slides) + 1}"
        if ref:
            s["event"] = ref
        if not s["title"]:
            err(t, n, "タイトルが空で、つなぐイベントも指定されていません")
        slides.append({k: v for k, v in s.items() if v})
    if not slides:
        err(TAB_HERO, 0, "表示する行が1つもありません（トップのスライドが消えてしまいます）")
    return {"label": label, "slides": slides}


# ---------------------------------------------------------------- 本体
LOCAL = None
if "--local" in sys.argv:
    LOCAL = Path(sys.argv[sys.argv.index("--local") + 1])
elif not SHEET_ID:
    # まだスプレッドシートをつないでいない状態。何もせずに正常終了する。
    print("tools/sheet.config.json に sheet_id がまだ入っていません。"
          "スプレッドシートからの更新は行いません。")
    sys.exit(0)

ev_rows, nw_rows, hr_rows = fetch(TAB_EVENTS), fetch(TAB_NEWS), fetch(TAB_HERO)
events = build_events(ev_rows)
news = build_news(nw_rows)
hero = build_hero(hr_rows, events)

if not events:
    err(TAB_EVENTS, 0, "公開にチェックの入った行が1つもありません")
if not news:
    err(TAB_NEWS, 0, "公開にチェックの入った行が1つもありません")

if errors:
    print("スプレッドシートの内容に問題があったので、サイトは更新していません。\n")
    for m in errors:
        print("  ✗ " + m)
    print("\n直してから、もう一度実行してください。")
    sys.exit(1)

for name, obj in (("events", events), ("news", news), ("hero", hero)):
    (DATA / f"{name}.json").write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for m in warnings:
    print("  ! " + m)
print(f"読み込みました：イベント {len(events)}件 / お知らせ {len(news)}件 / スライド {len(hero['slides'])}枚")
