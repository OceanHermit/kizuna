#!/usr/bin/env python3
"""スプレッドシートのセルに貼られた写真を取り出す。

Google スプレッドシートを xlsx として書き出すと、セルに貼った写真が
ファイルの中に入ってきます。それをセルの位置（シート名・行・列）と
結びつけて返します。

写真の貼りかたには2通りあり、書き出され方も違うので両方を見ます:
  1. 「セルの上に画像を配置」 → 図形（drawing）として、位置情報つきで入る
  2. 「セル内に画像を挿入」   → richData という新しい形式で入る

どちらも見つからなかった場合は空の辞書を返すだけで、呼び出し側は
これまでどおり（photos.json の写真）で動きます。
"""
import re, zipfile
import xml.etree.ElementTree as ET

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
       "image/gif": ".gif"}


def _rels(z, part):
    """ある部品の関係ファイル（_rels）を {Id: Target} で返す。"""
    base = part.rsplit("/", 1)
    rels_path = f"{base[0]}/_rels/{base[1]}.rels" if len(base) == 2 else f"_rels/{part}.rels"
    if rels_path not in z.namelist():
        return {}
    out = {}
    for rel in ET.fromstring(z.read(rels_path)).findall("rel:Relationship", NS):
        target = rel.get("Target", "")
        if target.startswith("/"):
            target = target[1:]
        else:                                           # 相対パスを解決する
            d = base[0] if len(base) == 2 else ""
            while target.startswith("../"):
                target, d = target[3:], d.rsplit("/", 1)[0] if "/" in d else ""
            target = f"{d}/{target}" if d else target
        out[rel.get("Id")] = target
    return out


def _cell_ref(ref):
    """\"B7\" → (行7, 列1)。列は0から数える。"""
    m = re.fullmatch(r"([A-Z]+)(\d+)", ref or "")
    if not m:
        return None
    col = 0
    for ch in m[1]:
        col = col * 26 + (ord(ch) - 64)
    return int(m[2]), col - 1


def _media(z, path):
    data = z.read(path)
    ext = "." + path.rsplit(".", 1)[-1].lower()
    if ext == ".jpeg":
        ext = ".jpg"
    return data, ext


EMU_PX = 9525              # 1ピクセルあたりのEMU
EMU_PT = 12700             # 1ポイントあたりのEMU


def _px(width_chars):
    """列幅（文字数）をピクセルに直す。Excel の既定フォントでの目安。"""
    return round(width_chars * 7) + 5


def _geometry(z, sheet_part):
    """シートの列幅と行の高さを EMU で返す。画像の位置を解くために使う。"""
    root = ET.fromstring(z.read(sheet_part))
    fmt = root.find("main:sheetFormatPr", NS)
    def_col = float((fmt.get("defaultColWidth") if fmt is not None else None) or 8.43)
    def_row = float((fmt.get("defaultRowHeight") if fmt is not None else None) or 15.0)
    cols = {}
    for c in root.iter(f"{{{NS['main']}}}col"):
        w = float(c.get("width", def_col))
        for i in range(int(c.get("min", 1)) - 1, int(c.get("max", 1))):
            cols[i] = _px(w) * EMU_PX
    rows = {}
    for r in root.iter(f"{{{NS['main']}}}row"):
        if r.get("ht"):
            rows[int(r.get("r"))] = round(float(r.get("ht")) * EMU_PT)
    return cols, rows, _px(def_col) * EMU_PX, round(def_row * EMU_PT)


def _col_emu(geo, i):
    return geo[0].get(i, geo[2])


def _row_emu(geo, r):
    return geo[1].get(r, geo[3])


def _to_emu(geo, col, col_off, row, row_off):
    """アンカー（列・行＋ずれ）を、シート左上からの絶対位置（EMU）にする。"""
    x = sum(_col_emu(geo, i) for i in range(col)) + col_off
    y = sum(_row_emu(geo, r) for r in range(1, row + 1)) + row_off
    return x, y


def _to_cell(geo, x, y):
    """絶対位置（EMU）が、どのセルの中にあるかを返す。(行は1から, 列は0から)"""
    col, acc = 0, 0
    while acc + _col_emu(geo, col) <= x and col < 1000:
        acc += _col_emu(geo, col)
        col += 1
    row, acc = 1, 0
    while acc + _row_emu(geo, row) <= y and row < 100000:
        acc += _row_emu(geo, row)
        row += 1
    return row, col


def _anchor_center(geo, anchor):
    """画像の中心がどのセルにあるかを返す。

    左上の角で判断すると、セルの境目ぎりぎりに貼られた写真を
    隣のセルのものと誤って判定してしまうため、中心で見る。
    """
    frm = anchor.find("xdr:from", NS)
    if frm is None:
        return None
    x0, y0 = _to_emu(geo,
                     int(frm.findtext("xdr:col", "0", NS)),
                     int(frm.findtext("xdr:colOff", "0", NS)),
                     int(frm.findtext("xdr:row", "0", NS)),
                     int(frm.findtext("xdr:rowOff", "0", NS)))
    to = anchor.find("xdr:to", NS)
    if to is not None:                                  # twoCellAnchor
        x1, y1 = _to_emu(geo,
                         int(to.findtext("xdr:col", "0", NS)),
                         int(to.findtext("xdr:colOff", "0", NS)),
                         int(to.findtext("xdr:row", "0", NS)),
                         int(to.findtext("xdr:rowOff", "0", NS)))
    else:                                               # oneCellAnchor
        ext = anchor.find("xdr:ext", NS)
        cx = int(ext.get("cx", 0)) if ext is not None else 0
        cy = int(ext.get("cy", 0)) if ext is not None else 0
        x1, y1 = x0 + cx, y0 + cy
    return _to_cell(geo, (x0 + x1) // 2, (y0 + y1) // 2)


def extract(xlsx_path):
    """{(シート名, 行, 列): (画像のバイト列, 拡張子)} を返す。行は1から、列は0から。"""
    found, notes = {}, []
    with zipfile.ZipFile(xlsx_path) as z:
        names = set(z.namelist())
        if not any(n.startswith("xl/media/") for n in names):
            return found, ["セルに貼られた写真は見つかりませんでした。"]

        wb_rels = _rels(z, "xl/workbook.xml")
        sheets = []
        for sh in ET.fromstring(z.read("xl/workbook.xml")).iter(
                f"{{{NS['main']}}}sheet"):
            rid = sh.get(f"{{{NS['r']}}}id")
            if rid in wb_rels:
                sheets.append((sh.get("name"), wb_rels[rid]))

        # --- 1) セルの上に置かれた画像（drawing） ---------------------------
        for name, part in sheets:
            d_rels = _rels(z, part)
            root = ET.fromstring(z.read(part))
            drawing = root.find("main:drawing", NS)
            if drawing is None:
                continue
            target = d_rels.get(drawing.get(f"{{{NS['r']}}}id"))
            if not target or target not in names:
                continue
            art_rels = _rels(z, target)
            geo = _geometry(z, part)
            for anchor in ET.fromstring(z.read(target)):
                blip = anchor.find(".//a:blip", NS)
                if blip is None:
                    continue
                pos = _anchor_center(geo, anchor)
                media = art_rels.get(blip.get(f"{{{NS['r']}}}embed"))
                if pos and media and media in names:
                    found[(name, pos[0], pos[1])] = _media(z, media)
                    notes.append(f"（セルの上の画像）{name} {pos[0]}行 {pos[1] + 1}列目")

        # --- 2) セル内に挿入された画像（richData） -------------------------
        rv_path = "xl/richData/rdrichvalue.xml"
        rel_path = "xl/richData/richValueRel.xml"
        if rv_path in names and rel_path in names:
            rel_ids = [e.get(f"{{{NS['r']}}}id") for e in
                       ET.fromstring(z.read(rel_path))]
            rel_map = _rels(z, rel_path)
            media_by_index = []
            for rv in ET.fromstring(z.read(rv_path)):    # <rv> の並び＝vm の順
                idx = None
                for v in rv:
                    if (v.text or "").strip().isdigit():
                        idx = int(v.text.strip())
                        break
                media_by_index.append(idx)
            for name, part in sheets:
                root = ET.fromstring(z.read(part))
                for c in root.iter(f"{{{NS['main']}}}c"):
                    vm = c.get("vm")
                    if not vm:
                        continue
                    pos = _cell_ref(c.get("r"))
                    i = int(vm) - 1
                    if pos is None or not (0 <= i < len(media_by_index)):
                        continue
                    ri = media_by_index[i]
                    if ri is None or not (0 <= ri < len(rel_ids)):
                        continue
                    media = rel_map.get(rel_ids[ri])
                    if media and media in names:
                        found[(name, pos[0], pos[1])] = _media(z, media)
                        notes.append(f"（セル内の画像）{name} {pos[0]}行 {pos[1] + 1}列目")

    if not found:
        notes.append("xl/media に画像はありましたが、どのセルのものか分かりませんでした。")
    return found, notes


if __name__ == "__main__":
    import sys
    imgs, notes = extract(sys.argv[1])
    for n in notes:
        print(" ", n)
    for (sheet, row, col), (data, ext) in sorted(imgs.items()):
        print(f"  {sheet} / {row}行 / {col + 1}列 → {len(data)} bytes {ext}")


def dimensions(data):
    """画像の幅と高さを返す（分からなければ None）。外部ライブラリは使わない。"""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data[:2] == b"\xff\xd8":                         # JPEG：SOF マーカーを探す
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            m = data[i + 1]
            if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                return (int.from_bytes(data[i + 7:i + 9], "big"),
                        int.from_bytes(data[i + 5:i + 7], "big"))
            if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
                i += 2
            else:
                i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
        return None
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X":
            return (int.from_bytes(data[24:27], "little") + 1,
                    int.from_bytes(data[27:30], "little") + 1)
    return None
