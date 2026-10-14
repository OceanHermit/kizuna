/* =========================================================
   キズナ ポータル — 動きのあるところだけ
   ・こども / おとな の切り替え
   ・今日のことば（日付で決まる）
   ・つぎの行事までのカウントダウン
   内容そのものは data/*.json から build.py が書き出しています
   ========================================================= */
(function () {
  'use strict';

  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  function readJSON(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  /* ---------- こども / おとな ---------- */
  var MODE_KEY = 'kizuna-mode';
  function setMode(mode) {
    document.body.setAttribute('data-mode', mode);
    $$('.mode button').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.mode === mode));
    });
    try { localStorage.setItem(MODE_KEY, mode); } catch (e) {}
  }
  var saved = 'kid';
  try { saved = localStorage.getItem(MODE_KEY) || 'kid'; } catch (e) {}
  setMode(saved === 'adult' ? 'adult' : 'kid');
  $$('.mode button').forEach(function (b) {
    b.addEventListener('click', function () { setMode(b.dataset.mode); });
  });

  /* ---------- あいさつ と 日付 ---------- */
  var now = new Date();
  var WD = ['日', '月', '火', '水', '木', '金', '土'];
  var greetEl = $('[data-greet]');
  if (greetEl) {
    var h = now.getHours();
    var g = h < 5 ? 'こんばんは' : h < 11 ? 'おはよう' : h < 18 ? 'こんにちは' : 'こんばんは';
    greetEl.textContent = g + '。';
  }
  var dateEl = $('[data-today]');
  if (dateEl) {
    dateEl.textContent = now.getFullYear() + '年' + (now.getMonth() + 1) + '月' +
      now.getDate() + '日（' + WD[now.getDay()] + '）';
  }

  /* ---------- 今日のことば ---------- */
  var words = readJSON('kizuna-words');
  if (words && words.length) {
    // 年始からの通算日で選ぶ＝毎日入れ替わり、同じ日なら誰が見ても同じ
    var start = new Date(now.getFullYear(), 0, 0);
    var day = Math.floor((now - start) / 86400000);
    var w = words[day % words.length];
    var t = $('[data-word-text]'), n = $('[data-word-note]');
    if (t) t.textContent = w.text;
    if (n) n.textContent = w.note || '';
  }

  /* ---------- つぎの行事までのカウントダウン ---------- */
  var events = readJSON('kizuna-events');
  var nextBox = $('[data-next]');
  if (events && events.length && nextBox) {
    var midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    var upcoming = events
      .map(function (e) {
        var p = e.date.split('-');
        return { e: e, t: new Date(+p[0], p[1] - 1, +p[2]).getTime() };
      })
      .filter(function (x) { return x.t >= midnight; })
      .sort(function (a, b) { return a.t - b.t; })[0];

    if (upcoming) {
      var days = Math.round((upcoming.t - midnight) / 86400000);
      var numEl = $('[data-next-num]'), unitEl = $('[data-next-unit]');
      if (numEl) {
        if (days === 0)      { numEl.textContent = 'きょう'; if (unitEl) unitEl.textContent = ''; }
        else if (days === 1) { numEl.textContent = 'あした'; if (unitEl) unitEl.textContent = ''; }
        else                 { numEl.textContent = String(days); if (unitEl) unitEl.textContent = '日後'; }
      }
      var d = new Date(upcoming.t);
      var set = function (sel, val) { var el = $(sel); if (el) el.textContent = val; };
      set('[data-next-title]', upcoming.e.title);
      set('[data-next-meta]',
        (d.getMonth() + 1) + '月' + d.getDate() + '日（' + WD[d.getDay()] + '）'
        + (upcoming.e.time ? '　' + upcoming.e.time : '')
        + (upcoming.e.place ? '　' + upcoming.e.place : ''));
      var link = $('[data-next-link]');
      if (link && upcoming.e.link) link.setAttribute('href', upcoming.e.link);
    } else {
      nextBox.setAttribute('hidden', '');
    }

    // 行事一覧で「もうすぐ」に印をつける
    $$('[data-ev-date]').forEach(function (el) {
      var p = el.dataset.evDate.split('-');
      var diff = Math.round((new Date(+p[0], p[1] - 1, +p[2]).getTime() - midnight) / 86400000);
      if (diff >= 0 && diff <= 14) {
        var tag = $('.ev__tag', el);
        if (tag) { tag.classList.add('ev__soon'); tag.textContent = diff === 0 ? 'きょう' : 'もうすぐ'; }
      }
    });
  }

  /* ---------- メニュー開閉 ---------- */
  var burger = $('.burger');
  if (burger) {
    burger.addEventListener('click', function () {
      var open = document.body.classList.toggle('nav-open');
      burger.setAttribute('aria-expanded', String(open));
    });
    $$('.drawer a').forEach(function (a) {
      a.addEventListener('click', function () {
        document.body.classList.remove('nav-open');
        burger.setAttribute('aria-expanded', 'false');
      });
    });
  }
})();
