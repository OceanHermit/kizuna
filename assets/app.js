/* =========================================================
   キズナ ポータル — 動きのあるところだけ
   ・ハンバーガーメニューの開閉
   ・注目イベントまでの残り日数
   ・近い行事に「もうすぐ」の印
   内容そのものは data/*.json から build.py が書き出しています
   ========================================================= */
(function () {
  'use strict';

  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- ハンバーガーメニュー ---------- */
  var burger = $('.burger');
  var ovl = $('.ovl');
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
  var daysFrom = function (ymd) {
    var p = String(ymd).split('-');
    if (p.length !== 3) return null;
    var t = new Date(+p[0], p[1] - 1, +p[2]).getTime();
    if (isNaN(t)) return null;
    return Math.round((t - midnight) / 86400000);
  };

  /* 注目イベントの残り日数（スライドごとに計算する） */
  $$('[data-count]').forEach(function (countEl) {
    var d = daysFrom(countEl.dataset.count);
    if (d === null || d < 0) {
      countEl.hidden = true;                 // 終わった行事なら出さない
    } else {
      countEl.innerHTML = d === 0 ? '<b>きょう</b> 開催'
                        : d === 1 ? '<b>あした</b> 開催'
                        : 'あと <b>' + d + '</b> 日';
      countEl.hidden = false;                // ここで初めて表示する
    }
  });

  /* ---------- 注目イベントのスライド ---------- */
  var track = $('[data-track]');
  if (track) {
    var slides = $$('.hero__slide', track);
    var dots = $$('.hero__dot');
    var at = function () { return Math.round(track.scrollLeft / track.clientWidth); };
    var goTo = function (i) {
      i = Math.max(0, Math.min(slides.length - 1, i));
      track.scrollTo({ left: i * track.clientWidth, behavior: 'smooth' });
    };
    $$('[data-go]').forEach(function (b) {
      if (b.classList.contains('hero__dot')) return;
      b.addEventListener('click', function () {
        goTo(at() + (b.dataset.go === 'next' ? 1 : -1));
      });
    });
    dots.forEach(function (d) {
      d.addEventListener('click', function () { goTo(parseInt(d.dataset.go, 10)); });
    });
    var sync = function () {
      var i = at();
      dots.forEach(function (d, n) {
        if (n === i) { d.setAttribute('aria-current', 'true'); }
        else { d.removeAttribute('aria-current'); }
      });
    };
    track.addEventListener('scroll', sync, { passive: true });
    window.addEventListener('resize', sync);
    sync();
  }

  /* 2週間以内の行事に印をつける */
  $$('[data-ev-date]').forEach(function (el) {
    var d = daysFrom(el.dataset.evDate);
    if (d === null || d < 0 || d > 14) return;
    var slot = $('[data-soon]', el);
    if (!slot) return;
    slot.textContent = d === 0 ? 'きょう' : d === 1 ? 'あした' : 'もうすぐ';
    slot.hidden = false;
  });
})();
