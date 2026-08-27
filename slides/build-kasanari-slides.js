/* かさなり 発表スライド (10分 / 16枚)
   前回デッキ（「面倒だな」を、形にしています。）と同じデザイン規約で組む。
   出力: kasanari-slides.pptx と、目視QA用の preview.html */

const PptxGenJS = require('pptxgenjs');
const fs = require('fs');

/* ---- design tokens（前回デッキから採寸） ---- */
const INK      = '141210';   // 地の黒
const ACCENT   = 'E8593C';   // 朱
const PAPER    = 'F5F2EC';   // 明るい文字
const MUTED    = '8A857D';   // 弱い文字
const CARD     = '1E1B18';   // カードの面
const RULE     = '3B3630';   // 罫
const ON_ACC   = '1C0D08';   // 朱地の上の文字
const ON_ACC_M = '6B2A1B';   // 朱地の上の弱い文字
const ON_ACC_P = '4A1B11';   // 朱地の上のノンブル
const FONT     = 'Noto Sans JP';

const M   = 0.85;            // 左右の余白
const W   = 8.3;             // 本文幅

const pres = new PptxGenJS();
pres.layout = 'LAYOUT_16x9';          // 10 x 5.625 in
pres.author = '仙波章信';
pres.title  = 'かさなり — 日程調整ツールができるまで';

const warnings = [];
let html = [];
let page = 0;

/* ---- 文字幅の見積り（全角1.0em / 半角0.55em）で溢れを検出 ---- */
const emWidth = s => [...s].reduce((n, c) => {
  const cp = c.codePointAt(0);
  const full = cp > 0x2000 && !(cp >= 0x2010 && cp <= 0x2027);
  return n + (full ? 1 : 0.55);
}, 0);

/* runs = [{text, options:{fontSize, breakLine}}] を、改行位置で束ねて行数と高さを見る */
function checkFit(runs, o, label) {
  const boxPt = o.w * 72;
  const rows = [];
  let cur = { pt: 0, sz: 0, head: '' };
  runs.forEach(r => {
    const sz = r.options.fontSize || o.sz;
    cur.pt += emWidth(r.text) * sz;
    cur.sz = Math.max(cur.sz, sz);
    if (!cur.head) cur.head = r.text;
    if (r.options.breakLine) { rows.push(cur); cur = { pt: 0, sz: 0, head: '' }; }
  });
  if (cur.sz || cur.pt) rows.push(cur);
  let need = 0;
  rows.forEach(r => {
    const wrapped = Math.max(1, Math.ceil(r.pt / boxPt - 0.001));
    need += (wrapped * r.sz * (o.lineSpacingPct || 1.4)) / 72;
  });
  if (need > o.h + 0.02) {
    warnings.push(`p${page} ${label}: ≒${need.toFixed(2)}in > 枠 ${o.h}in / "${rows[0].head}"`);
  }
}

/* ---- 描画プリミティブ（pptx と html を同時に吐く） ---- */
function rect(s, o) {
  s.addShape(pres.ShapeType.rect, {
    x: o.x, y: o.y, w: o.w, h: o.h,
    fill: o.transparency != null ? { color: o.fill, transparency: o.transparency } : { color: o.fill },
    line: { type: 'none' },
  });
  html.push(`<div class="r" style="left:${o.x * 96}px;top:${o.y * 96}px;width:${o.w * 96}px;height:${o.h * 96}px;background:#${o.fill};opacity:${o.transparency != null ? (100 - o.transparency) / 100 : 1}"></div>`);
}

function text(s, lines, o) {
  const arr = (Array.isArray(lines) ? lines : [lines]);
  const runs = arr.map((l, i) => {
    const t = typeof l === 'string' ? l : l.text;
    const ov = typeof l === 'string' ? {} : (l.opts || {});
    return { text: t, options: Object.assign({ breakLine: i < arr.length - 1 }, ov) };
  });
  checkFit(runs, o, o.label || '');
  const opt = {
    x: o.x, y: o.y, w: o.w, h: o.h,
    fontFace: FONT, fontSize: o.sz, bold: !!o.bold,
    color: o.color, align: o.align || 'left', valign: o.valign || 'middle',
    margin: 0, isTextBox: true, wrap: true,
  };
  if (o.spc) opt.charSpacing = o.spc;
  if (o.lineSpacingPct) opt.lineSpacingMultiple = o.lineSpacingPct;
  s.addText(runs, opt);

  const inner = runs.map(r => {
    const ov = r.options;
    const st = [ov.color ? `color:#${ov.color}` : '', ov.bold ? 'font-weight:700' : '', ov.fontSize ? `font-size:${ov.fontSize * 96 / 72}px` : ''].filter(Boolean).join(';');
    return `<span style="${st}">${r.text.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</span>` + (ov.breakLine ? '<br>' : '');
  }).join('');
  const just = o.valign === 'top' ? 'flex-start' : o.valign === 'bottom' ? 'flex-end' : 'center';
  html.push(`<div class="t" style="left:${o.x * 96}px;top:${o.y * 96}px;width:${o.w * 96}px;height:${o.h * 96}px;font-size:${o.sz * 96 / 72}px;font-weight:${o.bold ? 700 : 400};color:#${o.color};text-align:${o.align || 'left'};justify-content:${just};letter-spacing:${(o.spc || 0) / 100}em;line-height:${o.lineSpacingPct || 1.4}"><div>${inner}</div></div>`);
}

/* ---- スライドの型 ---- */
function slide(kind) {
  page++;
  const dark = kind !== 'accent';
  const s = pres.addSlide();
  s.background = { color: dark ? INK : ACCENT };
  html.push(`<section style="background:#${dark ? INK : ACCENT}"><div class="n">${String(page).padStart(2, '0')}</div>`);
  rect(s, { x: 0.55, y: 0.45, w: 0.1, h: 0.1, fill: dark ? ACCENT : INK });
  if (page > 1) {
    text(s, String(page).padStart(2, '0'), {
      x: 8.6, y: 4.95, w: 0.85, h: 0.3, sz: 10, color: dark ? MUTED : ON_ACC_P, align: 'right', label: 'ノンブル',
    });
  }
  s.close = () => html.push('</section>');
  return s;
}

/* 見出し（本文スライド共通） */
function head(s, eyebrow, lines, o = {}) {
  text(s, eyebrow, { x: M, y: 1.25, w: W, h: 0.35, sz: 12, bold: true, color: ACCENT, label: 'eyebrow' });
  text(s, lines, { x: M, y: 1.68, w: o.w || W, h: o.h || 0.5, sz: o.sz || 20, bold: true, color: PAPER, label: '見出し' });
}

/* 小見出し付きカード */
function card(s, o) {
  rect(s, { x: o.x, y: o.y, w: o.w, h: o.h, fill: CARD });
  rect(s, { x: o.x + 0.28, y: o.y + 0.32, w: 0.08, h: 0.08, fill: o.marker || ACCENT });
  text(s, o.title, { x: o.x + 0.55, y: o.y + 0.18, w: o.w - 0.85, h: 0.36, sz: 14, bold: true, color: PAPER, label: 'card title' });
  text(s, o.body, { x: o.x + 0.28, y: o.y + 0.68, w: o.w - 0.56, h: o.h - 0.9, sz: 11.5, color: MUTED, valign: 'top', lineSpacingPct: 1.5, label: 'card body' });
}

/* =======================================================================
   01 タイトル
   ======================================================================= */
{
  const s = slide('dark');
  text(s, '空いている時間を、', { x: M, y: 1.5, w: W, h: 0.8, sz: 38, bold: true, color: MUTED });
  text(s, '重ねて決める。', { x: M, y: 2.32, w: W, h: 1.0, sz: 54, bold: true, color: PAPER });
  text(s, '日程調整ツール「かさなり」ができるまで', { x: M, y: 3.55, w: W, h: 0.4, sz: 15, bold: true, color: ACCENT });
  text(s, '仙波章信', { x: M, y: 4.75, w: W, h: 0.35, sz: 12, color: MUTED });
  s.addNotes(`【つかみ｜30秒】
『日程調整、面倒じゃないですか。その面倒を片づけるために作った道具の話を10分だけさせてください』
『名前は「かさなり」。空いている時間を重ねて、みんなが空いている時間を出すツールです』
・作った経緯 → 作り方 → 使い方 → これから、の順で話すと予告する。`);
  s.close();
}

/* =======================================================================
   02 CHAPTER 1
   ======================================================================= */
{
  const s = slide('accent');
  text(s, 'CHAPTER 1', { x: M, y: 1.55, w: W, h: 0.4, sz: 13, bold: true, color: ON_ACC_M, spc: 200 });
  text(s, ['きっかけは、', 'いつもの日程調整'], { x: M, y: 2.05, w: W, h: 1.7, sz: 34, bold: true, color: ON_ACC });
  s.addNotes(`【10秒】
『はじまりは、よくあるLINEのやりとりでした』
・扉なので流す。立ち止まらない。`);
  s.close();
}

/* =======================================================================
   03 実際のやりとり
   ======================================================================= */
{
  const s = slide('dark');
  head(s, 'きっかけ', 'こういう、やりとりでした');

  const L = { x: M, y: 2.3, w: 4.15, h: 2.35 };
  rect(s, { x: L.x, y: L.y, w: L.w, h: L.h, fill: CARD });
  text(s, 'こちらが出した候補', { x: L.x + 0.28, y: L.y + 0.2, w: L.w - 0.56, h: 0.28, sz: 10.5, bold: true, color: ACCENT });
  text(s, ['8/21(金) 17:00–21:00', '8/22(土) 9:00–10:00', '8/23(日) 21:00–22:00', '8/26(水) 19:00–21:00', '8/31(月) 19:00–22:00', '9/1(火) 17:00–22:00'],
    { x: L.x + 0.28, y: L.y + 0.6, w: L.w - 0.56, h: 1.6, sz: 12, color: PAPER, valign: 'top', lineSpacingPct: 1.55 });

  const R = { x: 5.35, y: 2.3, w: 3.8, h: 2.35 };
  rect(s, { x: R.x, y: R.y, w: R.w, h: R.h, fill: CARD });
  text(s, '返ってきた答え', { x: R.x + 0.28, y: R.y + 0.2, w: R.w - 0.56, h: 0.28, sz: 10.5, bold: true, color: ACCENT });
  text(s, ['8/26 20:00–21:00', '8/31 20:00–22:00', '9/1 20:00–22:00'],
    { x: R.x + 0.28, y: R.y + 0.6, w: R.w - 0.56, h: 0.78, sz: 12, color: PAPER, valign: 'top', lineSpacingPct: 1.55 });
  text(s, ['「過去の日時が入っているのはなぜ？」', '「調整さんを使う方が便利ですよ」'],
    { x: R.x + 0.28, y: R.y + 1.45, w: R.w - 0.56, h: 0.62, sz: 10.5, color: MUTED, valign: 'top', lineSpacingPct: 1.5 });

  text(s, '候補6日ぶん、のべ16時間。ここから重なりを探す。', { x: M, y: 4.72, w: W, h: 0.3, sz: 11, color: MUTED });
  s.addNotes(`【55秒】
『6日ぶんの候補を、時間帯つきで送りました。相手からも時間帯つきで返ってきます』
『ここまでは順調です。問題はこのあと』
・「過去の日時が入っている」「調整さんの方が便利」と指摘をもらった話も添える。
・この2つの指摘が、そのまま作るときの条件になった、と繋げる。`);
  s.close();
}

/* =======================================================================
   04 重なりは目で探していた
   ======================================================================= */
{
  const s = slide('dark');
  head(s, 'きっかけ', '重なりは、目で探していた');

  const answers = [
    ['8/26(水)', '20:00–21:00', '1時間'],
    ['8/31(月)', '20:00–22:00', '2時間'],
    ['9/1(火)', '20:00–22:00', '2時間'],
  ];
  answers.forEach((a, i) => {
    const x = M + i * 2.85;
    rect(s, { x, y: 2.4, w: 2.6, h: 1.35, fill: CARD });
    text(s, a[0], { x: x + 0.28, y: 2.6, w: 2.04, h: 0.28, sz: 11, bold: true, color: ACCENT });
    text(s, a[1], { x: x + 0.28, y: 2.94, w: 2.04, h: 0.42, sz: 17, bold: true, color: PAPER });
    text(s, a[2], { x: x + 0.28, y: 3.38, w: 2.04, h: 0.28, sz: 10.5, color: MUTED });
  });

  text(s, ['二人ぶんなら、指で追えば出せます。', 'けれど三人、四人と増えた時点で、この作業は現実的ではなくなります。'],
    { x: M, y: 4.05, w: W, h: 0.75, sz: 13, color: MUTED, valign: 'top', lineSpacingPct: 1.55 });
  s.addNotes(`【45秒】
『送った候補と返ってきた答えを見比べて、重なるのはこの3つだ、と手で出しました』
『二人ならできます。でも三人、四人になると、もう無理です』
・「これを勝手に出してくれる道具があればいい」と思ったのがはじまり、と言い切る。`);
  s.close();
}

/* =======================================================================
   05 調整さんでは足りなかった理由
   ======================================================================= */
{
  const s = slide('dark');
  head(s, '既存のツールでは', '「調整さんを使えば？」に答えられなかった');

  rect(s, { x: 5.0, y: 2.35, w: 0.012, h: 2.1, fill: RULE });

  text(s, '5分刻みの候補に直すと', { x: M, y: 2.42, w: 3.9, h: 0.3, sz: 11.5, bold: true, color: ACCENT });
  text(s, [
    { text: '126', opts: { fontSize: 54, bold: true, color: PAPER, breakLine: false } },
    { text: '  通り', opts: { fontSize: 18, bold: true, color: MUTED, breakLine: false } },
  ], { x: M, y: 2.78, w: 3.9, h: 1.0, sz: 54, color: PAPER, valign: 'top' });
  text(s, ['この6日間を候補として並べた場合。', '15分刻みでも46通りになります。'],
    { x: M, y: 3.95, w: 3.9, h: 0.62, sz: 11.5, color: MUTED, valign: 'top', lineSpacingPct: 1.5 });

  const pts = [
    ['細かい時間が刻めない', '「17:00〜22:00の中でなら」が書けない'],
    ['刻むと候補が爆発する', '長い時間帯ほど、行が増えて手に負えない'],
    ['過ぎた日も並んだまま', '見る人に「なぜ？」と聞かれてしまう'],
  ];
  pts.forEach((p, i) => {
    const y = 2.42 + i * 0.7;
    rect(s, { x: 5.45, y: y + 0.13, w: 0.08, h: 0.08, fill: ACCENT });
    text(s, p[0], { x: 5.75, y, w: 3.4, h: 0.32, sz: 13.5, bold: true, color: PAPER });
    text(s, p[1], { x: 5.75, y: 0.3 + y, w: 3.4, h: 0.3, sz: 10.5, color: MUTED });
  });
  s.addNotes(`【50秒】
『調整さんは便利です。使わなかったのは、時間まで詰めたかったからです』
『候補を1行ずつ並べる方式だと、17時から22時のような長い枠は書けません。刻めば書けますが、5分刻みにすると126行になります』
・「じゃあ何が要るのか」を次のスライドで言い切る前フリにする。`);
  s.close();
}

/* =======================================================================
   06 発想の転換（ステートメント）
   ======================================================================= */
{
  const s = slide('dark');
  text(s, ['候補から選んでもらうのをやめて、', '「時間の幅」で答えてもらう。'],
    { x: 0.8, y: 1.4, w: 8.4, h: 2.75, sz: 32, bold: true, color: PAPER, lineSpacingPct: 1.5 });
  text(s, '── 重なりの計算は、こちらでやればいい', { x: 0.8, y: 4.05, w: 8.4, h: 0.4, sz: 13, color: MUTED });
  s.addNotes(`【20秒】
第1章の締め。ゆっくり言う。
『答える人には「この時間の中でなら空いている」とだけ言ってもらう。重なりを出すのは機械の仕事です』
・一拍おいてから次へ。`);
  s.close();
}

/* =======================================================================
   07 CHAPTER 2
   ======================================================================= */
{
  const s = slide('accent');
  text(s, 'CHAPTER 2', { x: M, y: 1.55, w: W, h: 0.4, sz: 13, bold: true, color: ON_ACC_M, spc: 200 });
  text(s, ['どうやって', '作ったか'], { x: M, y: 2.05, w: W, h: 1.7, sz: 34, bold: true, color: ON_ACC });
  s.addNotes(`【10秒】
『ここからは、実際にどう作ったかです』
・技術の詳細に寄りすぎない。決めごと → 仕組み → つまずき、の順。`);
  s.close();
}

/* =======================================================================
   08 先に決めた3つのこと
   ======================================================================= */
{
  const s = slide('dark');
  head(s, '手順 ①　設計', '先に決めた、3つのこと');
  const cards = [
    { title: '時間帯で答える', body: '○と△の人には、その日の空いている帯をドラッグで示してもらう。' },
    { title: '5分単位で重ねる', body: '集まった帯を5分ごとに数え、重なりの濃さとして持つ。' },
    { title: '所要時間で切り出す', body: '1時間の予定なら、1時間まるごと入る時間だけを候補に出す。' },
  ];
  cards.forEach((c, i) => card(s, Object.assign({ x: M + i * 2.85, y: 2.35, w: 2.6, h: 1.8 }, c)));
  text(s, '「いつなら空いているか」ではなく「この幅の中のどこなら空いているか」を集める。',
    { x: M, y: 4.45, w: W, h: 0.3, sz: 11, color: MUTED });
  s.addNotes(`【50秒】
『作る前に決めたのはこの3つだけです』
『○×だけだと粗い、細かく刻むと候補が増える。その真ん中をとって、幅で答えて5分で数える形にしました』
・3つ目が効いている、と補足：1時間の予定なら1時間まるごと入る時間しか出さないので、出てきた候補はそのまま使える。`);
  s.close();
}

/* =======================================================================
   09 仕組み（重ねる図）
   ======================================================================= */
{
  const s = slide('dark');
  head(s, '手順 ②　仕組み', '帯を重ねて、いちばん濃いところを出す');

  const T = { x: 1.75, w: 6.6 };              // 19:00–22:00 を 6.6in に割り当て
  const px = h => T.x + (h - 19) * (T.w / 3);
  const rows = [
    ['Aさん', 19, 21],
    ['Bさん', 20, 22],
    ['Cさん', 19.5, 21],
  ];
  rows.forEach((r, i) => {
    const y = 2.3 + i * 0.42;
    text(s, r[0], { x: M, y, w: 0.8, h: 0.3, sz: 11, color: MUTED });
    rect(s, { x: T.x, y, w: T.w, h: 0.3, fill: CARD });
    rect(s, { x: px(r[1]), y, w: px(r[2]) - px(r[1]), h: 0.3, fill: ACCENT, transparency: 45 });
  });

  const y4 = 3.62;
  text(s, '重なり', { x: M, y: y4, w: 0.8, h: 0.34, sz: 11, bold: true, color: PAPER });
  rect(s, { x: T.x, y: y4, w: T.w, h: 0.34, fill: CARD });
  rect(s, { x: px(20), y: y4, w: px(21) - px(20), h: 0.34, fill: ACCENT });
  text(s, '20:00–21:00', { x: px(20), y: y4, w: px(21) - px(20), h: 0.34, sz: 11, bold: true, color: PAPER, align: 'center' });

  ['19:00', '20:00', '21:00', '22:00'].forEach((t, i) => {
    text(s, t, { x: px(19 + i) - 0.35, y: 4.05, w: 0.7, h: 0.25, sz: 9.5, color: MUTED, align: 'center' });
  });
  text(s, '5分ごとに○の人数を数えて、多い順に並べる。上位5件を「いちばん重なる時間」として出す。',
    { x: M, y: 4.5, w: W, h: 0.3, sz: 11, color: MUTED });
  s.addNotes(`【55秒】
『やっていることは単純です。三人ぶんの帯を重ねて、全員が入っているところを探すだけ』
『5分ごとに○の人数を数えているので、20時ちょうどでなくても、20時5分からでも見つかります』
★ 実際の画面の「日ごとの重なり」バーを見せると早い。濃いところが人数の多い時間。`);
  s.close();
}

/* =======================================================================
   10 技術構成
   ======================================================================= */
{
  const s = slide('dark');
  head(s, '手順 ③　組み立て', '中身は、思ったより単純');

  rect(s, { x: 5.0, y: 2.4, w: 0.012, h: 2.2, fill: RULE });

  text(s, '見えるところ', { x: M, y: 2.45, w: 3.9, h: 0.3, sz: 11.5, bold: true, color: ACCENT });
  [['HTML 1ファイル、1,215行', 'ライブラリも組み立て作業もなし'],
   ['GitHub Pages に置くだけ', 'フォルダ名がそのままURLになる'],
   ['スマホの指で触る前提', 'ドラッグで帯、±ボタンで微調整']].forEach((p, i) => {
    const y = 2.9 + i * 0.62;
    rect(s, { x: M, y: y + 0.12, w: 0.08, h: 0.08, fill: ACCENT });
    text(s, p[0], { x: M + 0.3, y, w: 3.6, h: 0.3, sz: 12.5, bold: true, color: PAPER });
    text(s, p[1], { x: M + 0.3, y: y + 0.28, w: 3.6, h: 0.26, sz: 10, color: MUTED });
  });

  text(s, '保存するところ', { x: 5.45, y: 2.45, w: 3.7, h: 0.3, sz: 11.5, bold: true, color: ACCENT });
  [['Firebase に予定と回答を置く', '匿名ログイン＋Googleログイン'],
   ['回答は全員の画面にすぐ出る', '開いたままでも自動で更新される'],
   ['つくる人だけログイン', '答える人はリンクを開くだけ']].forEach((p, i) => {
    const y = 2.9 + i * 0.62;
    rect(s, { x: 5.45, y: y + 0.12, w: 0.08, h: 0.08, fill: ACCENT });
    text(s, p[0], { x: 5.75, y, w: 3.4, h: 0.3, sz: 12.5, bold: true, color: PAPER });
    text(s, p[1], { x: 5.75, y: y + 0.28, w: 3.4, h: 0.26, sz: 10, color: MUTED });
  });
  s.addNotes(`【40秒】
『中身は、HTMLが1ファイルと、保存先のFirebaseだけです』
『GitHub Pagesに置いているので、URLを配れば誰でも開けます。アプリのインストールも要りません』
・「1,215行」は、思ったより小さい規模だと伝わる数字なので言っておく。`);
  s.close();
}

/* =======================================================================
   11 つまずいたところ
   ======================================================================= */
{
  const s = slide('dark');
  head(s, '手順 ④　直したところ', 'つくる途中で、つまずいた3つ');
  const rows = [
    ['日ごとの時間帯が、そのままでは保存できなかった', '入れ子の配列を持てない保存先だったので、1日ぶんの帯をまとめて文字列にして持たせた。'],
    ['指では、5分きざみを狙って動かせない', 'ドラッグは15分きざみ。細かい調整は±ボタンで5分ずつ。触りやすさと細かさを分けた。'],
    ['あとからログインすると、別人になってしまう', '匿名のまま答えた人がログインしても、アカウントを繋いで同じ人として扱うようにした。'],
  ];
  rows.forEach((r, i) => {
    const y = 2.3 + i * 0.82;
    rect(s, { x: M, y: y + 0.13, w: 0.08, h: 0.08, fill: ACCENT });
    text(s, r[0], { x: M + 0.3, y, w: 8.0, h: 0.32, sz: 13.5, bold: true, color: PAPER });
    text(s, r[1], { x: M + 0.3, y: y + 0.32, w: 8.0, h: 0.3, sz: 11, color: MUTED });
  });
  text(s, 'どれも、実際に自分で触ってみて気づいたこと。使いながら直すのが、いちばん早い。',
    { x: M, y: 4.72, w: W, h: 0.3, sz: 11, color: MUTED });
  s.addNotes(`【50秒】
『作ってみて分かったことを3つだけ』
『特に2つ目。指で5分きざみは無理でした。ドラッグは15分、細かいところはボタンで5分ずつ、と分けたら一気に使いやすくなりました』
・技術の話に寄りすぎず、「触って直した」という姿勢が伝わればいい。`);
  s.close();
}

/* =======================================================================
   12 CHAPTER 3
   ======================================================================= */
{
  const s = slide('accent');
  text(s, 'CHAPTER 3', { x: M, y: 1.55, w: W, h: 0.4, sz: 13, bold: true, color: ON_ACC_M, spc: 200 });
  text(s, ['つかいかたは、', '3ステップ'], { x: M, y: 2.05, w: W, h: 1.7, sz: 34, bold: true, color: ON_ACC });
  s.addNotes(`【10秒】
『使い方は3ステップです。ここは実際の画面を見てもらいます』
★ 可能ならスマホでその場で開く。`);
  s.close();
}

/* =======================================================================
   13 3ステップ
   ======================================================================= */
{
  const s = slide('dark');
  head(s, 'つかいかた', 'つくる → 配る → 見る');
  const steps = [
    ['STEP 1', '予定をつくる', 'タイトル、候補日、回答してもらう時間のわく、この予定にかかる時間を選ぶ。'],
    ['STEP 2', 'リンクを配る', '6文字のあいことばとURLができる。相手はログインなしでそのまま答えられる。'],
    ['STEP 3', '重なりを見る', '集まった回答から、重なりの多い時間を上位5件。回答はその場で反映される。'],
  ];
  steps.forEach((st, i) => {
    const x = M + i * 2.85;
    rect(s, { x, y: 2.3, w: 2.6, h: 2.0, fill: CARD });
    text(s, st[0], { x: x + 0.28, y: 2.5, w: 2.04, h: 0.26, sz: 10, bold: true, color: ACCENT, spc: 150 });
    text(s, st[1], { x: x + 0.28, y: 2.82, w: 2.04, h: 0.34, sz: 15, bold: true, color: PAPER });
    text(s, st[2], { x: x + 0.28, y: 3.25, w: 2.04, h: 0.9, sz: 11, color: MUTED, valign: 'top', lineSpacingPct: 1.5 });
  });
  text(s, '答え方は ○（参加できる）／△（予定次第・メモを残せる）／✕（むり）の3つ。○と△の人だけ、帯を指定する。',
    { x: M, y: 4.5, w: W, h: 0.3, sz: 11, color: MUTED });
  s.addNotes(`【60秒】
『予定をつくる人だけログインが要ります。答える人はリンクを開くだけです』
『答え方は○△✕。○と△の人は、バーをドラッグして空いている時間を示します』
★ ここで実際の回答画面を出す。バーを引っぱって見せると一発で伝わる。
・△にはメモが残せる（「前の会議が延びたら遅れます」など）ことも触れる。`);
  s.close();
}

/* =======================================================================
   14 集計画面
   ======================================================================= */
{
  const s = slide('dark');
  head(s, 'つかいかた', '出てくるのは、こういう答え');

  const L = { x: M, y: 2.3, w: 4.15, h: 1.95 };
  rect(s, { x: L.x, y: L.y, w: L.w, h: L.h, fill: CARD });
  text(s, '8/31(月)', { x: L.x + 0.28, y: L.y + 0.22, w: 1.2, h: 0.28, sz: 11, color: MUTED });
  text(s, '20:00–22:00', { x: L.x + 0.28, y: L.y + 0.52, w: 2.2, h: 0.4, sz: 19, bold: true, color: PAPER });
  text(s, '○3　△1　✕0', { x: L.x + 2.3, y: L.y + 0.55, w: 1.57, h: 0.34, sz: 12, bold: true, color: ACCENT, align: 'right' });
  text(s, '○ 山田、佐藤、鈴木　　△ 田中', { x: L.x + 0.28, y: L.y + 1.02, w: L.w - 0.56, h: 0.28, sz: 11, color: PAPER });
  text(s, 'この 20:00–22:00 の中なら、どこで1時間とっても同じ顔ぶれです',
    { x: L.x + 0.28, y: L.y + 1.35, w: L.w - 0.56, h: 0.42, sz: 10, color: MUTED });

  const R = { x: 5.35, y: 2.3, w: 3.8, h: 1.95 };
  rect(s, { x: R.x, y: R.y, w: R.w, h: R.h, fill: CARD });
  text(s, '日ごとの重なり', { x: R.x + 0.28, y: R.y + 0.22, w: 2.4, h: 0.28, sz: 10.5, bold: true, color: ACCENT });
  const dens = [0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 2, 1, 1, 0, 0, 0];
  const bw = (R.w - 0.56) / dens.length;
  dens.forEach((d, i) => {
    const x = R.x + 0.28 + i * bw;
    rect(s, { x, y: R.y + 0.62, w: bw, h: 0.5, fill: d === 0 ? '2A2622' : ACCENT, transparency: d === 0 ? 0 : [0, 70, 45, 12][d] });
  });
  text(s, '9:00', { x: R.x + 0.28, y: R.y + 1.16, w: 1.0, h: 0.24, sz: 9, color: MUTED });
  text(s, '22:00', { x: R.x + R.w - 1.28, y: R.y + 1.16, w: 1.0, h: 0.24, sz: 9, color: MUTED, align: 'right' });
  text(s, '濃いところほど、○の人が多い時間。', { x: R.x + 0.28, y: R.y + 1.45, w: R.w - 0.56, h: 0.3, sz: 10, color: MUTED });

  text(s, '△の人が残したメモも、その時間のところに並ぶ。だから「誰に確認すればいいか」まで分かる。',
    { x: M, y: 4.5, w: W, h: 0.3, sz: 11, color: MUTED });
  s.addNotes(`【55秒】
『出てくるのは、重なりの多い順に並んだ時間です』
『○が誰で、△が誰かまで出るので、そのまま「じゃあこの時間で」と言えます』
・「この幅の中ならどこで1時間とっても同じ顔ぶれ」という表示が地味に効く、と補足。
★ 実際の集計画面を見せる。`);
  s.close();
}

/* =======================================================================
   15 これから
   ======================================================================= */
{
  const s = slide('dark');
  head(s, 'これから', '使いながら、育てていく');
  const stages = [
    ['いま', '実際の日程調整で使う', 'Googleログインを有効にして、まずは自分たちの予定で通しで試す。'],
    ['つぎ', '決まったら、そのまま予定に', '決まった時間をカレンダーに送る。案内文をそのまま貼れるようにする。'],
    ['その先', '地区の会合調整へ', '部会や班長会合の日程調整に。会合マトリックスとつなげば、表づくりまで一本になる。'],
  ];
  stages.forEach((st, i) => {
    const x = M + i * 2.85;
    rect(s, { x, y: 2.3, w: 2.6, h: 2.0, fill: CARD });
    text(s, st[0], { x: x + 0.28, y: 2.5, w: 2.04, h: 0.26, sz: 10.5, bold: true, color: i === 0 ? ACCENT : MUTED });
    text(s, st[1], { x: x + 0.28, y: 2.82, w: 2.04, h: 0.6, sz: 14, bold: true, color: PAPER, valign: 'top' });
    text(s, st[2], { x: x + 0.28, y: 3.45, w: 2.04, h: 0.72, sz: 10.5, color: MUTED, valign: 'top', lineSpacingPct: 1.5 });
  });
  text(s, '「つぎ」から先は、まだ構想。使ってみて、要ると分かったものから作る。',
    { x: M, y: 4.5, w: W, h: 0.3, sz: 11, color: MUTED });
  s.addNotes(`【45秒】
『いまは公開して、試している段階です』
『先の話は決め打ちしません。使ってみて要るとわかったものから作ります』
・地区の会合調整に使えると、既に作ってある会合マトリックスの仕組みと繋がる、という将来像だけ置いておく。`);
  s.close();
}

/* =======================================================================
   16 締め
   ======================================================================= */
{
  const s = slide('accent');
  text(s, ['「調整さんじゃ足りない」が、', '道具になりました。'],
    { x: 0.8, y: 1.5, w: 8.4, h: 1.6, sz: 30, bold: true, color: ON_ACC, lineSpacingPct: 1.5 });
  text(s, 'oceanhermit.github.io/my-tools/kasanari/', { x: 0.8, y: 3.35, w: 8.4, h: 0.5, sz: 17, bold: true, color: ON_ACC_M });
  text(s, '「こういうのが欲しい」と言ってもらえれば、だいたい形になります。', { x: 0.8, y: 4.0, w: 8.4, h: 0.35, sz: 13, color: ON_ACC_M });
  s.addNotes(`【25秒｜締め】
『不便だと言い続けていたら、道具になりました』
『URLはこれです。使ってみて、足りないところがあれば言ってください。そこが次に作るところです』
・最後は明るく終える。ありがとうございました。
─────────
全16枚 / 目安 約10分`);
  s.close();
}

/* ---- 書き出し ---- */
const OUT = process.argv[2] || 'kasanari-slides.pptx';
pres.writeFile({ fileName: OUT }).then(() => {
  const CSS = `<!doctype html><meta charset="utf-8"><style>
  body{margin:0;background:#666;font-family:"IPAGothic","Noto Sans JP",sans-serif}
  section{position:relative;width:960px;height:540px;margin:0 auto 12px;overflow:hidden}
  .r{position:absolute}
  .t{position:absolute;display:flex;flex-direction:column;white-space:pre-wrap;word-break:break-word}
  .n{position:absolute;right:4px;top:2px;color:#0f0;font:10px monospace;opacity:.6}
  </style>`;
  const secs = html.join('\n').split('</section>').filter(x => x.trim()).map(x => x + '</section>');
  const TAIL = '<div style="height:160px"></div>';
  fs.writeFileSync('preview-a.html', CSS + secs.slice(0, 8).join('\n') + TAIL);
  fs.writeFileSync('preview-b.html', CSS + secs.slice(8).join('\n') + TAIL);
  console.log('wrote', OUT, '/ preview.html /', page, 'slides');
  if (warnings.length) { console.log('\n⚠ 収まりの警告:'); warnings.forEach(w => console.log('  ' + w)); }
  else console.log('収まりの警告なし');
});
