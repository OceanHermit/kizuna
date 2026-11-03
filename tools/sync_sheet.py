#!/usr/bin/env python3
"""Google スプレッドシートの内容を data/*.json に書き出す。

使いかた:
    python3 tools/sync_sheet.py            # ネットからシートを取ってくる
    python3 tools/sync_sheet.py --local t  # t/ の中の CSV から読む（テスト用）

シートIDは tools/sheet.config.json か、環境変数 SHEET_ID で指定します。
おかしな入力があったら、何も書かずにエラーで止まります（壊れた内容が公開されない）。
"""
import csv, hashlib, io, json, os, re, sys, tempfile, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONF = json.loads((ROOT / "tools" / "sheet.config.json").read_text(encoding="utf-8"))
SHEET_ID = os.environ.get("SHEET_ID") or CONF.get("sheet_id", "")

TAB_EVENTS, TAB_NEWS, TAB_HERO = "イベント", "お知らせ", "トップのスライド"
LINKS = json.loads((DATA / "site.json").read_text(encoding="utf-8")).get("links", {})
PHOTO_KEYS = set(json.loads((DATA / "photos.json").read_text(encoding="utf-8"))
                 .get("photos", {}))
IMGDIR = ROOT / "assets" / "img"
HEADERS = {}          # タブ名 → 見出しの並び
CELL_IMAGES = {}      # (タブ名, 行, 列) → (画像のバイト列, 拡張子)
PHOTO_URLS = {}       # photos.json に書き戻す { キー: URL }
SAVED_IMAGES = []     # assets/img に保存したファイル
LEGACY_SLUGS = {}     # 旧シートの URL名 → イベント（移行中のみ使う）

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
    # 見出しの「（リンクを貼る）」のような補足は、取り除いてから名前として使う
    head = [re.sub(r"[（(].*?[)）]", "", c).strip() for c in rows[0]]
    HEADERS[tab] = head
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


def auto_slug(prefix, d, title, used):
    """ページのURL（slug）を日付から自動で決める。

    同じ日に2件以上あるときだけ、タイトルから作った短い記号を足す。
    日付とタイトルが同じなら、いつ作り直しても同じURLになる。
    ※日付を直すとURLも変わります。
    """
    base = f"{prefix}-{d}"
    cand = base
    if cand in used:
        tag = hashlib.sha1(title.encode("utf-8")).hexdigest()[:4]
        cand = f"{base}-{tag}"
        i = 2
        while cand in used:
            cand = f"{base}-{tag}-{i}"
            i += 1
    used.add(cand)
    return cand


def form_url(v, tab, row):
    """申込フォームの欄。URLをそのまま受ける（昔の合言葉も一応受ける）。"""
    v = v.strip()
    if not v:
        return ""
    if v.startswith(("http://", "https://")):
        return v
    if v in LINKS:                                      # join / shindan などの旧表記
        return v
    err(tab, row, f"申込フォーム「{v}」が、フォームのURLとして読めません。"
                  "https:// から始まるURLを貼るか、空にしてください")
    return ""


def photo(cell, key, tab, row):
    """写真の欄。セルに貼られた画像、または画像のURLを受ける。

    ・セルに写真が貼られていれば assets/img/<key>.<拡張子> に保存する
      （build.py は assets/img を photos.json より優先して使う）
    ・URLが書かれていれば photos.json に書き戻す
    ・空なら "" を返す。呼び出し側はこれまでどおりの既定の写真を使う
    """
    cell = cell.strip()
    head = HEADERS.get(tab, [])
    col = head.index("写真") if "写真" in head else None
    img = CELL_IMAGES.get((tab, row, col)) if col is not None else None

    if img:
        data, ext = img
        IMGDIR.mkdir(parents=True, exist_ok=True)
        for old_ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            stale = IMGDIR / f"{key}{old_ext}"
            if stale.exists() and old_ext != ext:
                stale.unlink()                          # 拡張子が変わったときの置きかえ
        (IMGDIR / f"{key}{ext}").write_bytes(data)
        SAVED_IMAGES.append(f"assets/img/{key}{ext}")
        return key

    if cell.startswith(("http://", "https://")):
        PHOTO_URLS[key] = cell
        return key

    if cell in PHOTO_KEYS:                              # ev1 / hero2 などの差し込み口を直接指定
        return cell

    if cell:
        err(tab, row, f"写真の欄「{cell[:30]}」が読めません。"
                      "セルに写真を貼りつけるか、画像のURL（https://…）を入れるか、"
                      "空にしてください")
    return ""


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
        ev = {"slug": auto_slug("event", d, title, used), "date": d, "title": title}
        for key, col in (("time", "時間"), ("place", "場所"), ("tag", "タグ"),
                         ("target", "対象"), ("fee", "参加費"), ("bring", "持ちもの"),
                         ("body", "一覧に出る文章")):
            put(ev, key, r.get(col, "").strip())
        put(ev, "apply", form_url(r.get("申込フォーム", ""), t, n))
        put(ev, "pic", photo(r.get("写真", ""), f"ev-{ev['slug']}", t, n))
        ev["_pic_unset"] = "pic" not in ev
        legacy = r.get("URL名", "").strip().lower()     # 旧シートの URL名 列（あれば）
        if legacy:
            LEGACY_SLUGS[legacy] = ev
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
    # 写真の欄が空のイベントには、並び順で ev1 / ev2 / ev3 を順番に割り当てる
    for i, e in enumerate(out):
        if e.pop("_pic_unset", False):
            e["pic"] = f"ev{i % 3 + 1}"
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
        it = {"slug": auto_slug("news", d, title, used), "date": d, "title": title}
        put(it, "cat", r.get("分類", "").strip())
        put(it, "body", r.get("一覧に出る文章", "").strip())
        p = paras(r.get("詳細ページの本文", ""))
        if p:
            it["detail"] = p
        out.append(it)
    out.sort(key=lambda x: x["date"], reverse=True)     # 新しい順
    return out


def build_hero(rows, events):
    """イベント名でイベントとつなぐ。空欄のところはそのイベントの内容をそのまま使う。"""
    by_title = {}
    for e in events:
        by_title.setdefault(e["title"], []).append(e)
    label = json.loads((DATA / "hero.json").read_text(encoding="utf-8")).get("label", "注目のイベント")
    slides = []
    for i, r in enumerate(rows):
        if not on(r.get("表示", "")):
            continue
        n, t = r["_row"], TAB_HERO
        ref_title = (r.get("つなぐイベント", "")
                     or r.get("つなぐイベントのURL名", "")).strip()
        src, ref = {}, ""
        if ref_title:
            found = by_title.get(ref_title, [])
            if not found and ref_title.lower() in LEGACY_SLUGS:
                found = [LEGACY_SLUGS[ref_title.lower()]]   # 旧シートの URL名 でも拾う
            if not found:
                err(t, n, f"「{ref_title}」というイベントが、公開中のイベントにありません。"
                          "イベントのシートのタイトルと同じものを選んでください")
            elif len(found) > 1:
                err(t, n, f"「{ref_title}」という名前のイベントが{len(found)}件あります。"
                          "イベントのシートで、どちらかのタイトルを変えてください")
            else:
                src = found[0]
                ref = src["slug"]
        s = {}
        s["title"] = r.get("タイトル", "").strip() or src.get("title", "")
        raw_date = r.get("日付", "").strip()
        s["date"] = date(raw_date, t, n, "日付", required=False) if raw_date else src.get("date", "")
        s["time"] = r.get("時間", "").strip() or src.get("time", "")
        s["place"] = r.get("場所", "").strip() or src.get("place", "")
        s["body"] = r.get("文章", "").strip() or src.get("body", "")
        s["cta_label"] = r.get("ボタンの文字", "").strip() or "このイベントのくわしい内容"
        slot = f"hero{len(slides) + 1}"                 # hero1 / hero2 / hero3
        s["pic"] = photo(r.get("写真", ""), slot, t, n) or slot
        if ref:
            s["event"] = ref
        if not s["title"] and not ref_title:            # つなぐイベント側のエラーは既に出している
            err(t, n, "つなぐイベントを選ぶか、タイトルを書いてください")
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

# セルに貼られた写真を拾う。ここが失敗しても、文字の内容だけで先に進む。
if not LOCAL:
    try:
        import sheet_images
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
        tmp = Path(tempfile.gettempdir()) / "kizuna_sheet.xlsx"
        with urllib.request.urlopen(url, timeout=120) as r:
            tmp.write_bytes(r.read())
        CELL_IMAGES, notes = sheet_images.extract(tmp)
        for n in notes:
            print("  写真:", n)
        tmp.unlink(missing_ok=True)
    except Exception as exc:                            # 写真が取れなくても止めない
        warnings.append(f"セルの写真を読めませんでした（{type(exc).__name__}: {exc}）。"
                        "写真は今のままにします。")

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

if PHOTO_URLS:                                          # URLで指定された写真を登録する
    pf = DATA / "photos.json"
    ph = json.loads(pf.read_text(encoding="utf-8"))
    slot = ph.setdefault("photos", {})
    for k, v in PHOTO_URLS.items():
        slot[k] = {**slot.get(k, {}), "url": v}
    pf.write_text(json.dumps(ph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for m in warnings:
    print("  ! " + m)
print(f"読み込みました：イベント {len(events)}件 / お知らせ {len(news)}件 / スライド {len(hero['slides'])}枚")
for f in SAVED_IMAGES:
    print("  写真を保存:", f)
for k, v in PHOTO_URLS.items():
    print(f"  写真のURLを登録: {k} → {v[:60]}")
