/* =========================================================
   キズナ ポータル — 動きのあるところだけ
   ・ハンバーガーメニューの開閉
   ・ヘッダーの地色（写真の上では透過、スクロールすると出る）
   ・注目イベントのスライド
   ・残り日数と「もうすぐ」の印
   内容そのものは data/*.json から build.py が書き出しています
   ========================================================= */
(function () {
  'use strict';

  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- ヘッダーの地色 ---------- */
  var hd = $('.hd');
  if (hd) {
    var onScroll = function () { hd.classList.toggle('is-solid', window.scrollY > 40); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------- ハンバーガーメニュー ---------- */
  var burger = $('.burger'), ovl = $('.ovl');
  if (burger && ovl) {
    var setNav = function (open) {
      document.body.classList.toggle('nav-open', open);
      burger.setAttribute('aria-expanded', String(open));
      ovl.setAttribute('aria-hidden', String(!open));
      document.body.style.overflow = open ? 'hidden' : '';
    };
    setNav(false);
    burger.addEventListener('click', function () {
      setNav(!document.body.classList.contains('nav-open'));
    });
    $$('.ovl a').forEach(function (a) {
      a.addEventListener('click', function () { setNav(false); });
    });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && document.body.classList.contains('nav-open')) setNav(false);
    });
  }

  /* ---------- 日付まわり ---------- */
  var now = new Date();
  var midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  var daysFrom = function (s) {
    var p = String(s).split('-');
    if (p.length !== 3) return null;
    var t = new Date(+p[0], p[1] - 1, +p[2]).getTime();
    return isNaN(t) ? null : Math.round((t - midnight) / 86400000);
  };

  /* 残り日数（スライドごとに計算する） */
  $$('[data-count]').forEach(function (el) {
    var d = daysFrom(el.dataset.count);
    if (d === null || d < 0) { el.hidden = true; return; }
    el.innerHTML = d === 0 ? 'きょう開催'
                 : d === 1 ? 'あした開催'
                 : 'あと<b>' + d + '</b>日';
    el.hidden = false;
  });

  /* 2週間以内のイベントに印をつける */
  $$('[data-ev-date]').forEach(function (el) {
    var d = daysFrom(el.dataset.evDate);
    if (d === null || d < 0 || d > 14) return;
    var slot = $('[data-soon]', el);
    if (!slot) return;
    slot.textContent = d === 0 ? 'きょう' : d === 1 ? 'あした' : 'もうすぐ';
    slot.hidden = false;
  });

  /* ---------- 文章のコピー ---------- */
  $$('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var el = document.getElementById(btn.dataset.copy);
      if (!el) return;
      var done = function () {
        var before = btn.textContent;
        btn.textContent = 'コピーしました';
        btn.classList.add('done');
        setTimeout(function () { btn.textContent = before; btn.classList.remove('done'); }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(el.textContent).then(done, function () {});
      } else {
        // 古い環境では、文章を選択状態にして手でコピーしてもらう
        var r = document.createRange();
        r.selectNodeContents(el);
        var sel = window.getSelection();
        sel.removeAllRanges(); sel.addRange(r);
      }
    });
  });

  /* ---------- 注目イベントのスライド ---------- */
  var track = $('[data-track]');
  if (track) {
    var slides = $$('.stage__slide', track);
    var dots = $$('.stage__dot');
    var at = function () { return Math.round(track.scrollLeft / track.clientWidth); };
    var goTo = function (i) {
      if (i >= slides.length) i = 0;          // 最後まで行ったら先頭に戻る
      if (i < 0) i = slides.length - 1;
      track.scrollTo({ left: i * track.clientWidth, behavior: 'smooth' });
    };
    var next = $('[data-go="next"]');
    if (next) next.addEventListener('click', function () { goTo(at() + 1); });
    dots.forEach(function (d) {
      d.addEventListener('click', function () { goTo(parseInt(d.dataset.go, 10)); });
    });
    var sync = function () {
      var i = at();
      dots.forEach(function (d, n) {
        if (n === i) d.setAttribute('aria-current', 'true');
        else d.removeAttribute('aria-current');
      });
    };
    track.addEventListener('scroll', sync, { passive: true });
    window.addEventListener('resize', sync);
    sync();
  }
})();
