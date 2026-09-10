# -*- coding: utf-8 -*-
"""
無料版 WordPress.com 向けブロックマークアップ生成
------------------------------------------------
制約：
  - <style> タグは wp_kses で除去される → インラインスタイルのみ
  - インラインスタイルも safecss_filter_attr の許可プロパティに限られる
    （animation / transform / box-shadow / transition は不可）
  - プラグイン不可、カスタムCSS不可
方針：
  - 見た目を作り込む所 → カスタムHTMLブロック（検証されないので確実）
  - 文章を編集する所   → コアブロック（そのまま編集できる）
  - 明朝は Web フォントを読めないので OS 標準の明朝を指定する
"""

MIN  = '"Yu Mincho","Hiragino Mincho ProN","Noto Serif JP",serif'
MINJ = '\\"Yu Mincho\\",\\"Hiragino Mincho ProN\\",\\"Noto Serif JP\\",serif'
LAT  = 'Georgia,"Times New Roman",serif'
LATJ = 'Georgia,\\"Times New Roman\\",serif'

PAPER, PAPER_D, WHITE = '#FBF8F3', '#F3EDE3', '#ffffff'
INK, INK2, SUB        = '#1C1A17', '#4A443C', '#7A736A'
FOREST, FOREST_L      = '#14503F', '#E7EFEA'
SAKURA, GOLD, LINE    = '#D98C93', '#B08D3F', '#E2DACD'

IMG = 'https://picsum.photos/seed/{}/{}/{}'

out = []
def w(s): out.append(s)

def html(inner):
    w('<!-- wp:html -->\n' + inner.strip() + '\n<!-- /wp:html -->\n')

def sec_open(bg, content='1080px', pad_y='clamp(72px,11vw,140px)'):
    w(f'<!-- wp:group {{"align":"full","style":{{"color":{{"background":"{bg}"}},'
      f'"spacing":{{"padding":{{"top":"{pad_y}","right":"24px","bottom":"{pad_y}","left":"24px"}}}}}},'
      f'"layout":{{"type":"constrained","contentSize":"{content}"}}}} -->\n'
      f'<div class="wp-block-group alignfull has-background" style="background-color:{bg};'
      f'padding-top:{pad_y};padding-right:24px;padding-bottom:{pad_y};padding-left:24px">\n')

def sec_close():
    w('</div>\n<!-- /wp:group -->\n')

def shead(no, en, ja, anchor, dark=False):
    """01 / Event / イベント の見出し"""
    c_no = SAKURA
    c_en = PAPER if dark else INK
    c_ja = 'rgba(251,248,243,0.62)' if dark else SUB
    w(f'<!-- wp:paragraph {{"style":{{"color":{{"text":"{c_no}"}},"typography":{{"fontSize":"0.78rem",'
      f'"letterSpacing":"0.24em","fontFamily":"{LATJ}"}},"spacing":{{"margin":{{"bottom":"4px"}}}}}}}} -->\n'
      f'<p class="has-text-color" style="color:{c_no};margin-bottom:4px;font-family:{LAT};'
      f'font-size:0.78rem;letter-spacing:0.24em">{no}</p>\n<!-- /wp:paragraph -->\n')
    w(f'<!-- wp:heading {{"anchor":"{anchor}","style":{{"color":{{"text":"{c_en}"}},"typography":'
      f'{{"fontSize":"clamp(1.9rem,5.6vw,3rem)","letterSpacing":"0.08em","fontFamily":"{LATJ}",'
      f'"fontWeight":"400"}},"spacing":{{"margin":{{"bottom":"6px"}}}}}}}} -->\n'
      f'<h2 class="wp-block-heading has-text-color" id="{anchor}" style="color:{c_en};margin-bottom:6px;'
      f'font-family:{LAT};font-size:clamp(1.9rem,5.6vw,3rem);font-weight:400;letter-spacing:0.08em">{en}</h2>\n'
      f'<!-- /wp:heading -->\n')
    w(f'<!-- wp:paragraph {{"style":{{"color":{{"text":"{c_ja}"}},"typography":{{"fontSize":"0.8rem",'
      f'"letterSpacing":"0.22em"}},"spacing":{{"margin":{{"bottom":"38px"}}}}}}}} -->\n'
      f'<p class="has-text-color" style="color:{c_ja};margin-bottom:38px;font-size:0.8rem;'
      f'letter-spacing:0.22em">{ja}</p>\n<!-- /wp:paragraph -->\n')

def para(text, color=INK2, size='0.94rem', lh='2.2', mb='1.4em', align=None, family=None, ls=None, weight=None):
    a  = f'"align":"{align}",' if align else ''
    cls = 'has-text-align-center ' if align == 'center' else ''
    ty = [f'"fontSize":"{size}"', f'"lineHeight":"{lh}"']
    st = [f'color:{color}', f'margin-bottom:{mb}']
    if family: ty.append(f'"fontFamily":"{family[1]}"'); st.append(f'font-family:{family[0]}')
    st.append(f'font-size:{size}')
    if weight: ty.append(f'"fontWeight":"{weight}"'); st.append(f'font-weight:{weight}')
    if ls: ty.append(f'"letterSpacing":"{ls}"'); st.append(f'letter-spacing:{ls}')
    st.append(f'line-height:{lh}')
    w(f'<!-- wp:paragraph {{{a}"style":{{"color":{{"text":"{color}"}},"typography":{{{",".join(ty)}}},'
      f'"spacing":{{"margin":{{"bottom":"{mb}"}}}}}}}} -->\n'
      f'<p class="{cls}has-text-color" style="{";".join(st)}">{text}</p>\n<!-- /wp:paragraph -->\n')

def more(label, href, dark=False):
    c = PAPER if dark else INK
    html(f'''
<p style="margin:0"><a href="{href}" style="display:inline-block;color:{c};text-decoration:none;
font-size:0.84rem;letter-spacing:0.16em;border-bottom:1px solid {c};padding-bottom:6px">{label}　—</a></p>
''')

# =====================================================================
w('''<!-- ============================================================
  キズナ トップページ / 無料版 WordPress.com 向け
  ------------------------------------------------------------
  貼り付け方：
   1. 固定ページを新規作成
   2. 右上の「︙」→「コードエディター」に切り替え
   3. このファイルの中身を丸ごと貼り付け
   4. 「︙」→「ビジュアルエディター」に戻す
   5. 「設定 → 表示設定」でこの固定ページをホームページに指定
  ------------------------------------------------------------
  ・<style> タグは使っていません（無料プランでも消えません）
  ・写真は picsum.photos のデモです。メディアに本番写真をアップして
    src を差し替えてください
  ・明朝体は OS 標準（游明朝／ヒラギノ明朝）を指定しています
============================================================ -->

''')

# ---------- ヒーロー（カスタムHTML：作り込み優先） ----------
html(f'''
<div style="background-image:url({IMG.format("kizuna-hero-2",1800,1200)});background-size:cover;background-position:center;background-color:#12241e">
 <div style="background-color:rgba(18,28,24,0.5);padding:clamp(96px,20vw,190px) clamp(22px,6vw,72px) clamp(64px,12vw,110px)">
  <div style="max-width:1080px;margin:0 auto">
    <p style="margin:0 0 20px;color:rgba(255,255,255,0.82);font-family:{LAT};font-size:0.76rem;letter-spacing:0.4em">KIZUNA CLUB</p>
    <h1 style="margin:0;color:#ffffff;font-family:{MIN};font-weight:500;font-size:clamp(1.95rem,7vw,4rem);line-height:1.55;letter-spacing:0.08em">子どもたちの毎日に、<br>ちいさな灯りを。</h1>
    <p style="margin:26px 0 0;max-width:34em;color:rgba(255,255,255,0.9);font-size:clamp(0.86rem,2.6vw,1rem);line-height:2.2;letter-spacing:0.04em">全国の子どもたちが、仏教の教えをもとに、ステキな毎日を送れるよう、さまざまなサポートを受けることができる集まりです。</p>
    <div style="display:flex;flex-wrap:wrap;gap:14px;margin-top:36px">
      <a href="#kzn-contact" style="display:inline-block;background-color:{FOREST};color:#ffffff;text-decoration:none;padding:18px 38px;border-radius:999px;font-size:0.94rem;letter-spacing:0.1em">キズナクラブに申し込む</a>
      <a href="#kzn-about" style="display:inline-block;border:1px solid rgba(255,255,255,0.65);color:#ffffff;text-decoration:none;padding:17px 38px;border-radius:999px;font-size:0.94rem;letter-spacing:0.1em">キズナについて知る</a>
    </div>
  </div>
 </div>
</div>
''')

# ---------- 01 EVENT ----------
sec_open(PAPER, '1080px')
shead('01', 'Event', 'イベント・行事', 'kzn-event')
para('イベントは随時入れ替わります。横にスワイプしてご覧ください。', SUB, '0.84rem', '2', '26px')
sec_close()

events = [
    ('kizuna-ev1', '09.13', '文化祭',   'キズナ文化祭 2026<br>in 東京ビッグサイト',   '東京ビッグサイト ／ 10:00 - 16:00'),
    ('kizuna-ev2', '受付中', '特別企画', 'キズナ式 才能診断<br>自分の強みを見つけよう', 'スマホで2分 ／ 中学生〜35才 ／ 無料'),
    ('kizuna-ev3', '10.05', 'キズナ塾', 'キズナ塾 体験会<br>勉強のはじめかた',        'オンライン開催 ／ 参加無料'),
    ('kizuna-ev4', '行事日', '受付',     'キズナポイント<br>提供品の受付',            '正本堂2階 キズナコーナー'),
    ('kizuna-ev5', '11.03', '交流会',   'ジュニアクラブ<br>秋の交流会',              '小学生対象 ／ 保護者の見学もできます'),
    ('kizuna-ev6', '通年',   '募集',     'キズナサポーター<br>募集のご案内',          '勉強サポートをしてくださる方へ'),
]
cards = []
for seed, date, tag, title, meta in events:
    cards.append(f'''  <a href="#" style="flex:0 0 78%;max-width:320px;display:block;text-decoration:none;color:{INK}">
    <img src="{IMG.format(seed,800,600)}" alt="" loading="lazy" style="width:100%;height:210px;object-fit:cover;border-radius:3px;display:block;background-color:{PAPER_D}">
    <div style="display:flex;align-items:center;gap:11px;margin-top:15px">
      <span style="font-family:{LAT};font-size:1.14rem;letter-spacing:0.06em;color:{INK}">{date}</span>
      <span style="background-color:{FOREST};color:#ffffff;font-size:0.64rem;letter-spacing:0.14em;padding:4px 12px;border-radius:999px">{tag}</span>
    </div>
    <p style="margin:11px 0 0;font-family:{MIN};font-size:1.02rem;line-height:1.75;letter-spacing:0.05em;color:{INK}">{title}</p>
    <p style="margin:8px 0 0;font-size:0.74rem;line-height:1.9;letter-spacing:0.06em;color:{SUB}">{meta}</p>
  </a>''')

html(f'''
<div style="background-color:{PAPER};padding:0 0 clamp(56px,9vw,110px)">
 <div style="max-width:1128px;margin:0 auto;padding:0 24px">
  <div style="display:flex;flex-wrap:nowrap;gap:20px;overflow:auto;overflow-x:auto;padding-bottom:22px">
{chr(10).join(cards)}
  </div>
  <p style="margin:18px 0 0"><a href="#" style="display:inline-block;color:{INK};text-decoration:none;font-size:0.84rem;letter-spacing:0.16em;border-bottom:1px solid {INK};padding-bottom:6px">イベントをすべて見る　—</a></p>
 </div>
</div>
''')

# ---------- 02 NEWS（最新の投稿ブロック：本物の投稿が並ぶ） ----------
sec_open(WHITE, '860px')
shead('02', 'News', 'お知らせ', 'kzn-news')
w('<!-- wp:latest-posts {"postsToShow":4,"displayPostContent":true,"excerptLength":70,'
  '"displayPostDate":true,"displayFeaturedImage":true,"featuredImageAlign":"left",'
  '"featuredImageSizeSlug":"medium","featuredImageSizeWidth":190,"featuredImageSizeHeight":140,'
  '"addLinkToFeaturedImage":true,"style":{"typography":{"fontSize":"0.9rem"}}} /-->\n')
para('※ 投稿がまだ無いときは何も表示されません。投稿を追加すると、新しい順に自動で並びます。',
     SUB, '0.78rem', '2', '26px')
more('お知らせをすべて見る', '#')
sec_close()

# ---------- 03 ABOUT ----------
sec_open(PAPER_D, '1080px')
shead('03', 'About', 'キズナとは', 'kzn-about')
w(f'''<!-- wp:media-text {{"mediaPosition":"left","mediaWidth":42,"mediaLink":"#","imageFill":false,"mediaSizeSlug":"large","style":{{"spacing":{{"margin":{{"bottom":"48px"}}}}}}}} -->
<div class="wp-block-media-text is-stacked-on-mobile" style="margin-bottom:48px;grid-template-columns:42% auto"><figure class="wp-block-media-text__media"><img src="{IMG.format("kizuna-ab1",900,1120)}" alt=""/></figure><div class="wp-block-media-text__content">
<!-- wp:paragraph {{"style":{{"color":{{"text":"{INK}"}},"typography":{{"fontSize":"clamp(1.35rem,4.2vw,2.1rem)","lineHeight":"1.85","letterSpacing":"0.08em","fontFamily":"{MINJ}"}},"spacing":{{"margin":{{"bottom":"26px"}}}}}}}} -->
<p class="has-text-color" style="color:{INK};margin-bottom:26px;font-family:{MIN};font-size:clamp(1.35rem,4.2vw,2.1rem);letter-spacing:0.08em;line-height:1.85">ひとりで抱えこまずに、<br>いっしょに考えていく。</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph {{"style":{{"color":{{"text":"{INK2}"}},"typography":{{"fontSize":"0.92rem","lineHeight":"2.3"}},"spacing":{{"margin":{{"bottom":"1.5em"}}}}}}}} -->
<p class="has-text-color" style="color:{INK2};margin-bottom:1.5em;font-size:0.92rem;line-height:2.3">キズナは、全国の子どもたちが仏教の教えをもとに、ステキな毎日を送れるよう、さまざまなサポートを受けることができる集まりです。</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph {{"style":{{"color":{{"text":"{INK2}"}},"typography":{{"fontSize":"0.92rem","lineHeight":"2.3"}},"spacing":{{"margin":{{"bottom":"0"}}}}}}}} -->
<p class="has-text-color" style="color:{INK2};margin-bottom:0;font-size:0.92rem;line-height:2.3">学校のこと、進路のこと、毎日のこと。子どもたち一人ひとりの状況に合わせて、無理のないかたちで参加できます。保護者の方のご相談も、いつでもお受けしています。</p>
<!-- /wp:paragraph -->
</div></div>
<!-- /wp:media-text -->
''')

pts = [('kizuna-pt1','仏教の教えをもとに','毎日をステキに過ごすための考え方を、子どもたちの言葉で伝えています。'),
       ('kizuna-pt2','一人ひとりに合わせて','年齢や状況に応じたコースをご用意。無料体験からはじめられます。'),
       ('kizuna-pt3','全国に、仲間がいる','行事や文化祭を通じて、同じ年ごろの仲間と出会うことができます。')]
pt_html = []
for seed, ttl, txt in pts:
    pt_html.append(f'''  <div style="flex:1 1 250px;display:flex;gap:16px;align-items:center">
    <img src="{IMG.format(seed,200,200)}" alt="" loading="lazy" style="width:72px;height:72px;object-fit:cover;border-radius:999px;background-color:{PAPER_D}">
    <div>
      <p style="margin:0 0 4px;font-family:{MIN};font-size:0.98rem;letter-spacing:0.06em;color:{INK}">{ttl}</p>
      <p style="margin:0;font-size:0.78rem;line-height:1.9;color:{SUB}">{txt}</p>
    </div>
  </div>''')
html(f'''
<div style="display:flex;flex-wrap:wrap;gap:26px 30px;margin-top:8px">
{chr(10).join(pt_html)}
</div>
<p style="margin:38px 0 0"><a href="#" style="display:inline-block;color:{INK};text-decoration:none;font-size:0.84rem;letter-spacing:0.16em;border-bottom:1px solid {INK};padding-bottom:6px">キズナクラブの詳細を見る　—</a></p>
''')
sec_close()

# ---------- 04 SERVICE ----------
sec_open(PAPER, '1080px')
shead('04', 'Service', 'キズナでできること', 'kzn-menu')
svc = [
    ('kizuna-m1','01','キズナクラブ・ジュニアクラブ','CLUB','入会・登録内容の変更・会費のご案内。まずはお気軽にお申し込みください。'),
    ('kizuna-m2','02','キズナ塾','STUDY','学びたい子と、教えたい大人をつなぐ取り組み。サポーターも募集中です。'),
    ('kizuna-m3','03','キズナ式 才能診断','DIAGNOSIS','心理分析「ビッグ5」で、自分の強みを活かせる進路が分かります。'),
    ('kizuna-m4','04','キズナクラブ特典','BENEFITS','会員のみなさまが受けられる特典をご案内しています。'),
    ('kizuna-m5','05','キズナカード・キズナポイント','POINT','ポイントのため方・つかい方、提供品の受付についてはこちら。'),
    ('kizuna-m6','06','スタッフ・サポーター紹介','MEMBER','キズナを支えている人たちをご紹介します。'),
]
svc_html = []
for seed, no, ttl, en, txt in svc:
    svc_html.append(f'''  <a href="#" style="flex:1 1 280px;max-width:340px;display:block;text-decoration:none;color:{INK}">
    <img src="{IMG.format(seed,700,880)}" alt="" loading="lazy" style="width:100%;height:300px;object-fit:cover;border-radius:3px;display:block;background-color:{PAPER_D}">
    <p style="margin:16px 0 0;font-family:{LAT};font-size:0.72rem;letter-spacing:0.2em;color:{SAKURA}">{no}　{en}</p>
    <p style="margin:6px 0 0;font-family:{MIN};font-size:1.04rem;line-height:1.7;letter-spacing:0.05em;color:{INK}">{ttl}</p>
    <p style="margin:8px 0 0;font-size:0.78rem;line-height:1.9;color:{SUB}">{txt}</p>
  </a>''')
html(f'''
<div style="display:flex;flex-wrap:wrap;gap:clamp(26px,4vw,44px) clamp(16px,2.4vw,30px)">
{chr(10).join(svc_html)}
</div>
''')
sec_close()

# ---------- 05 ACTIVITY ----------
sec_open(FOREST, '1080px')
shead('05', 'Activity', 'キズナの活動', 'kzn-act', dark=True)
para('全国で、こんな時間を過ごしています。行事、文化祭、勉強会、そしてなんでもない日のおしゃべりまで。子どもたちが安心して過ごせる場所をつくっています。',
     'rgba(251,248,243,0.82)', '0.9rem', '2.2', '38px')
acts = ''.join(
    f'<img src="{IMG.format(f"kizuna-a{i}",800,600)}" alt="" loading="lazy" '
    f'style="flex:1 1 210px;height:170px;object-fit:cover;border-radius:3px;background-color:#0f3f31">\n'
    for i in range(1, 7))
html(f'''
<div style="display:flex;flex-wrap:wrap;gap:12px">
{acts}</div>
<p style="margin:34px 0 0"><a href="#" style="display:inline-block;color:{PAPER};text-decoration:none;font-size:0.84rem;letter-spacing:0.16em;border-bottom:1px solid {PAPER};padding-bottom:6px">活動の記録をもっと見る　—</a></p>
''')
sec_close()

# ---------- 06 ACCESS ----------
sec_open(WHITE, '1080px')
shead('06', 'Access', 'キズナコーナー', 'kzn-corner')
html(f'''
<div style="display:flex;flex-wrap:wrap;gap:clamp(28px,5vw,56px)">

 <div style="flex:1 1 300px;background-color:{PAPER};padding:26px;border-radius:3px">
  <p style="margin:0;text-align:center;font-family:{MIN};font-size:0.96rem;letter-spacing:0.06em;color:{INK}">高校生までの子供達が喜ぶもの</p>
  <p style="margin:2px 0 20px;text-align:center;font-size:0.74rem;color:{SUB}">（おもちゃ、漫画、ゲーム など）</p>
  <div style="display:flex;gap:9px">
   <div style="flex:1 1 0;background-color:#D8615C;color:#ffffff;text-align:center;padding:24px 6px;border-radius:2px;font-size:0.86rem;letter-spacing:0.06em">正本堂２階</div>
   <div style="flex:1 1 0;background-color:#4A8FBF;color:#ffffff;text-align:center;padding:24px 6px;border-radius:2px;font-size:0.86rem;letter-spacing:0.06em">サンキュー売店</div>
  </div>
  <div style="background-color:#F0C93F;color:{INK};text-align:center;padding:24px 6px;border-radius:2px;margin-top:9px;font-size:0.94rem;font-weight:700;letter-spacing:0.14em">キズナコーナー</div>
  <p style="margin:12px 0 0;text-align:center;font-size:0.78rem;letter-spacing:0.08em;color:{SAKURA}">↑ サンキュー売店のすぐそばです</p>
 </div>

 <div style="flex:1 1 300px">
  <div style="border-top:1px solid {LINE};padding:15px 0;border-bottom:1px solid {LINE};display:flex;gap:14px">
   <span style="flex:0 0 76px;font-family:{LAT};font-size:0.74rem;letter-spacing:0.16em;color:{SAKURA};padding-top:5px">PLACE</span>
   <span style="font-size:0.87rem;line-height:1.95;color:{INK2}">正本堂２階・サンキュー売店のすぐそば「キズナコーナー」</span>
  </div>
  <div style="padding:15px 0;border-bottom:1px solid {LINE};display:flex;gap:14px">
   <span style="flex:0 0 76px;font-family:{LAT};font-size:0.74rem;letter-spacing:0.16em;color:{SAKURA};padding-top:5px">ITEM</span>
   <span style="font-size:0.87rem;line-height:1.95;color:{INK2}">高校生までの子供達が喜ぶもの（おもちゃ・漫画・ゲームなど）</span>
  </div>
  <div style="padding:15px 0;border-bottom:1px solid {LINE};display:flex;gap:14px">
   <span style="flex:0 0 76px;font-family:{LAT};font-size:0.74rem;letter-spacing:0.16em;color:{SAKURA};padding-top:5px">MEETING</span>
   <span style="font-size:0.87rem;line-height:1.95;color:{INK2}">キズナ担当へのご紹介、打ち合わせも承っています</span>
  </div>
  <div style="padding:15px 0;border-bottom:1px solid {LINE};display:flex;gap:14px">
   <span style="flex:0 0 76px;font-family:{LAT};font-size:0.74rem;letter-spacing:0.16em;color:{SAKURA};padding-top:5px">TRIAL</span>
   <span style="font-size:0.87rem;line-height:1.95;color:{INK2}">個別コース登録・無料体験のご相談もこちらへ</span>
  </div>
  <p style="margin:22px 0 0;font-size:0.82rem;letter-spacing:0.06em;color:{GOLD}">※ 二千畳行事日のみ受付しております。</p>
 </div>

</div>
''')
sec_close()

# ---------- 07 Q&A ----------
sec_open(PAPER, '860px')
shead('07', 'Q &amp; A', 'よくある質問', 'kzn-faq')

faqs = [
 ('キズナクラブの登録内容の変更はどうすればいいでしょうか？',
  ['申し込みフォームの「登録情報の変更・修正はこちら」から変更していただけます。'],
  ('登録内容の変更はこちら', '#'), None),
 ('キズナ会費の納め方はどのようにすればいいでしょうか？',
  ['以下のページからご確認ください。会費はキズナクラブが月200円、オンラインコースが月2000円です。'],
  ('キズナ会費の納め方はこちら', '#'), None),
 ('キズナクラブ会費の自動引き落としはされていますか？',
  ['キズナクラブ会費の自動引き落としは行っておりません。規定の納め方で納入をお願いいたします。'],
  None, None),
 ('会費をまとめて納めていますが、途中からオンラインコース（2000円）に切り替わった時の会費はどうなりますか？',
  ['オンラインコースに登録された月の翌月から、2000円の会費に切り替わります。すでに納入済みの額は、オンラインコース2000円分に含めていただけたらと思います。'],
  None,
  '<b>例）</b>現在4月。月200円の会費を、昨年12月に1年分（2400円）納入済み。5月からオンラインコース（2000円）の場合。<br>→ 5月分として、あと600円ご納入ください。6月分以降は2000円として納めます。'),
 ('子どもへの個別コースの案内は、いつすればよいですか？',
  ['キズナ担当との打ち合わせ後にしていただけたらと思います。お子さんの年齢や状況に応じた伝え方がありますので、打ち合わせ後のご案内を推奨しております。'],
  None, None),
]
for q, answers, link, example in faqs:
    w(f'<!-- wp:html -->\n<hr style="border:0;border-top:1px solid {LINE};margin:0">\n<!-- /wp:html -->\n')
    w(f'<!-- wp:details {{"style":{{"spacing":{{"padding":{{"top":"22px","right":"4px","bottom":"22px","left":"4px"}}}},'
      f'"typography":{{"fontSize":"0.95rem","lineHeight":"1.85","fontFamily":"{MINJ}"}},'
      f'"color":{{"text":"{INK}"}}}}}} -->\n'
      f'<details class="wp-block-details has-text-color" style="color:{INK};padding-top:22px;padding-right:4px;'
      f'padding-bottom:22px;padding-left:4px;font-family:{MIN};font-size:0.95rem;line-height:1.85">'
      f'<summary>Q.　{q}</summary>')
    for a in answers:
        w(f'<!-- wp:paragraph {{"style":{{"color":{{"text":"{SUB}"}},"typography":{{"fontSize":"0.87rem",'
          f'"lineHeight":"2.1"}}}}}} -->\n'
          f'<p class="has-text-color" style="color:{SUB};font-size:0.87rem;line-height:2.1">A.　{a}</p>\n'
          f'<!-- /wp:paragraph -->\n')
    if example:
        w(f'<!-- wp:html -->\n<p style="background-color:{WHITE};border-left:2px solid {SAKURA};'
          f'padding:16px 20px;margin:0 0 1em;font-size:0.8rem;line-height:2;color:{INK2}">{example}</p>\n'
          f'<!-- /wp:html -->\n')
    if link:
        w(f'<!-- wp:html -->\n<p style="margin:0"><a href="{link[1]}" style="display:inline-block;color:{FOREST};'
          f'text-decoration:none;font-size:0.82rem;letter-spacing:0.14em;border-bottom:1px solid {FOREST};'
          f'padding-bottom:5px">{link[0]}　—</a></p>\n<!-- /wp:html -->\n')
    w('</details>\n<!-- /wp:details -->\n')
w(f'<!-- wp:html -->\n<hr style="border:0;border-top:1px solid {LINE};margin:0 0 34px">\n<!-- /wp:html -->\n')

sec_close()

# ---------- 08 CONTACT ----------
html(f'''
<div id="kzn-contact" style="background-image:url({IMG.format("kizuna-ct",1600,900)});background-size:cover;background-position:center;background-color:#0c2820">
 <div style="background-color:rgba(12,40,32,0.88);padding:clamp(72px,11vw,140px) clamp(22px,6vw,72px)">
  <div style="max-width:820px;margin:0 auto;text-align:center">
  <p style="margin:0;color:rgba(255,255,255,0.7);font-family:{LAT};font-size:0.76rem;letter-spacing:0.4em">CONTACT</p>
  <p style="margin:16px 0 20px;color:#ffffff;font-family:{MIN};font-size:clamp(1.45rem,4.8vw,2.4rem);line-height:1.7;letter-spacing:0.1em">まずは、お話を<br>聞かせてください。</p>
  <p style="margin:0 auto;max-width:34em;color:rgba(255,255,255,0.82);font-size:0.88rem;line-height:2.1">キズナ担当へのご紹介、打ち合わせ、個別コース登録、無料体験のご相談を承っています。どんな小さなことでも、お気軽にご連絡ください。</p>

  <div style="display:flex;flex-wrap:wrap;gap:14px;justify-content:center;margin-top:36px">
   <a href="#" style="display:inline-block;background-color:{SAKURA};color:#ffffff;text-decoration:none;padding:18px 38px;border-radius:999px;font-size:0.94rem;letter-spacing:0.1em">相談フォームを開く</a>
   <a href="#" style="display:inline-block;border:1px solid rgba(255,255,255,0.65);color:#ffffff;text-decoration:none;padding:17px 38px;border-radius:999px;font-size:0.94rem;letter-spacing:0.1em">キズナクラブに申し込む</a>
  </div>

  <div style="border-top:1px solid rgba(255,255,255,0.22);margin-top:52px;padding-top:40px;display:flex;flex-wrap:wrap;gap:28px;text-align:left">
   <div style="flex:1 1 240px">
    <a href="tel:07041717569" style="display:block;color:#ffffff;text-decoration:none;font-family:{LAT};font-size:clamp(1.8rem,6.4vw,2.5rem);letter-spacing:0.06em;line-height:1.3">070-4171-7569</a>
    <span style="display:block;margin-top:4px;color:rgba(255,255,255,0.62);font-size:0.74rem;letter-spacing:0.14em">タップで電話がかけられます</span>
    <p style="margin:14px 0 0;color:rgba(255,255,255,0.78);font-size:0.82rem;letter-spacing:0.08em">主催：キズナクラブ ／ 担当：宮部 成美</p>
   </div>
   <div style="flex:1 1 240px">
    <p style="margin:0 0 16px;padding-left:16px;border-left:1px solid rgba(255,255,255,0.3);color:rgba(255,255,255,0.72);font-size:0.79rem;line-height:2"><b style="display:block;color:#ffffff;font-weight:500;letter-spacing:0.08em">お返事について</b>フォーム入力後のお返事は、目安として3日後です。お急ぎの場合は、キズナ担当に直接ご連絡ください。</p>
    <p style="margin:0;padding-left:16px;border-left:1px solid rgba(255,255,255,0.3);color:rgba(255,255,255,0.72);font-size:0.79rem;line-height:2"><b style="display:block;color:#ffffff;font-weight:500;letter-spacing:0.08em">個別コースのご案内</b>お子さんへのご案内は、キズナ担当との打ち合わせ後を推奨しております。</p>
   </div>
  </div>
 </div>
 </div>
</div>
''')

# ---------- フッター ----------
nav = ''.join(
    f'<a href="{h}" style="display:block;padding:9px 0;color:rgba(251,248,243,0.78);text-decoration:none;font-size:0.82rem;letter-spacing:0.08em">{t}</a>'
    for t, h in [('イベント','#kzn-event'),('お知らせ','#kzn-news'),('キズナとは','#kzn-about'),
                 ('できること','#kzn-menu'),('活動','#kzn-act'),('キズナコーナー','#kzn-corner'),
                 ('よくある質問','#kzn-faq'),('お問い合わせ','#kzn-contact')])
html(f'''
<div style="background-color:{INK};padding:clamp(52px,8vw,78px) clamp(22px,6vw,72px) 32px">
 <div style="max-width:1080px;margin:0 auto">
  <div style="display:flex;flex-wrap:wrap;gap:36px;padding-bottom:38px;border-bottom:1px solid rgba(251,248,243,0.14)">
   <div style="flex:1 1 260px">
    <p style="margin:0;color:{PAPER};font-family:{MIN};font-size:1.36rem;letter-spacing:0.36em">キズナ</p>
    <p style="margin:16px 0 0;max-width:24em;color:rgba(251,248,243,0.78);font-size:0.8rem;line-height:2.1">全国の子どもたちが、仏教の教えをもとに、ステキな毎日を送れるよう応援しています。</p>
    <a href="#" style="display:inline-block;margin-top:24px;padding:11px 24px;border:1px solid rgba(251,248,243,0.3);border-radius:999px;color:rgba(251,248,243,0.78);text-decoration:none;font-size:0.78rem;letter-spacing:0.14em">学徒サイトに戻る →</a>
   </div>
   <div style="flex:1 1 260px;display:flex;flex-wrap:wrap;gap:0 30px">
    <div style="flex:1 1 110px">{nav}</div>
   </div>
  </div>
  <div style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:14px;padding-top:26px;color:rgba(251,248,243,0.5);font-size:0.7rem;letter-spacing:0.12em">
   <span>© KIZUNA CLUB</span>
   <span style="font-family:{LAT}">Supporting children across Japan</span>
  </div>
 </div>
</div>
''')

open('wordpress/kizuna-top-free.html', 'w', encoding='utf-8').write('\n'.join(out))
print('generated: wordpress/kizuna-top-free.html')
