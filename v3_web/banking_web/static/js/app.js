(function () {
  'use strict';

  var root = document.documentElement;

  /* ── THEME ── */
  function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem('atm-theme'); } catch (e) {}
    var prefersDark = !window.matchMedia || window.matchMedia('(prefers-color-scheme: dark)').matches;
    var theme = saved || (prefersDark ? 'dark' : 'light');
    applyTheme(theme);

    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        applyTheme(next);
        try { localStorage.setItem('atm-theme', next); } catch (e) {}
      });
    });
  }
  function applyTheme(t) {
    if (t === 'light') root.setAttribute('data-theme', 'light');
    else root.removeAttribute('data-theme');
    document.querySelectorAll('[data-theme-toggle]').forEach(function (b) {
      b.textContent = t === 'light' ? '\u25CE' : '\u2600';
    });
  }

  /* ── SIDEBAR DRAWER ── */
  function initSidebar() {
    var sidebar = document.getElementById('sidebar');
    var openBtn = document.getElementById('sidebar-open');
    var overlay = document.getElementById('sidebar-overlay');
    if (!sidebar || !openBtn) return;
    function close() { sidebar.classList.remove('open'); if (overlay) overlay.classList.remove('open'); }
    openBtn.addEventListener('click', function () { sidebar.classList.add('open'); if (overlay) overlay.classList.add('open'); });
    if (overlay) overlay.addEventListener('click', close);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    sidebar.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { if (window.innerWidth < 1025) close(); });
    });
  }

  /* ── SCROLL PROGRESS + BACK TO TOP ── */
  function initScrollFx() {
    var bar = document.getElementById('scroll-progress');
    var topBtn = document.getElementById('back-to-top');
    var ticking = false;
    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var st = window.pageYOffset;
        var h = document.documentElement.scrollHeight - window.innerHeight;
        if (bar) bar.style.transform = 'scaleX(' + (h > 0 ? st / h : 0) + ')';
        if (topBtn) topBtn.classList.toggle('visible', st > 320);
        ticking = false;
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    if (topBtn) topBtn.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  }

  /* ── COLLAPSE / EXPAND CARDS ── */
  function initCollapsibles() {
    var els = document.querySelectorAll('[data-collapsible]');
    if (!els.length) return;
    var pageKey = 'atm-collapsed-' + location.pathname;
    var collapsed = [];
    try { collapsed = JSON.parse(sessionStorage.getItem(pageKey) || '[]'); } catch (e) {}

    els.forEach(function (el, i) {
      var head = el.querySelector('.card-head');
      if (!head) return;
      var body = el.querySelector(':scope > .collapse-body');
      if (!body) {
        body = document.createElement('div');
        body.className = 'collapse-body';
        Array.prototype.slice.call(el.children).forEach(function (child) {
          if (child !== head) body.appendChild(child);
        });
        el.appendChild(body);
      }
      var toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'collapse-toggle';
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('title', 'Minimise / maximise');
      toggle.textContent = '▼';
      toggle.addEventListener('click', function () {
        el.classList.toggle('is-collapsed');
        var on = !el.classList.contains('is-collapsed');
        toggle.setAttribute('aria-expanded', on ? 'true' : 'false');
        var key = el.dataset.collapseKey || ('card-' + i);
        var set = new Set(JSON.parse(sessionStorage.getItem(pageKey) || '[]'));
        if (on) set.delete(key); else set.add(key);
        try { sessionStorage.setItem(pageKey, JSON.stringify(Array.from(set))); } catch (e) {}
        window.dispatchEvent(new Event('atm-collapse-changed'));
      });
      head.appendChild(toggle);
      head.classList.add('card-head--toggle');

      if (el.dataset.collapseKey) {
        var key = el.dataset.collapseKey;
        if (collapsed.indexOf(key) !== -1) {
          el.classList.add('is-collapsed');
          toggle.setAttribute('aria-expanded', 'false');
        }
      }
    });

    document.querySelectorAll('[data-collapse-all]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var collapse = btn.getAttribute('data-collapse-all') === 'collapse';
        document.querySelectorAll('[data-collapsible]').forEach(function (el) {
          var t = el.querySelector('.collapse-toggle');
          if (!t) return;
          var want = collapse ? true : false;
          if (el.classList.contains('is-collapsed') === want) return;
          el.classList.toggle('is-collapsed', want);
          t.setAttribute('aria-expanded', want ? 'false' : 'true');
        });
        try { sessionStorage.removeItem(pageKey); } catch (e) {}
        window.dispatchEvent(new Event('atm-collapse-changed'));
      });
    });
  }

  /* ── FLASH AUTO-DISMISS ── */
  function initFlashes() {
    document.querySelectorAll('.flash-stack .flash').forEach(function (f) {
      var kill = function () {
        f.classList.add('fade-out');
        setTimeout(function () { f.remove(); }, 420);
      };
      setTimeout(kill, 4600);
      f.addEventListener('click', kill);
    });
  }

  /* ── REVEAL ON SCROLL ── */
  function initReveals() {
    var els = document.querySelectorAll('.reveal');
    if (!els.length) return;
    if (!('IntersectionObserver' in window)) {
      els.forEach(function (e) { e.classList.add('in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.08 });
    els.forEach(function (e) { io.observe(e); });
  }

  /* ── 3D TILT CARDS ── */
  function initTilt() {
    var cards = document.querySelectorAll('.glass-card--tilt');
    if (!cards.length) return;
    var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return;
    cards.forEach(function (card) {
      card.addEventListener('mousemove', function (e) {
        var rect = card.getBoundingClientRect();
        var x = (e.clientX - rect.left) / rect.width - 0.5;
        var y = (e.clientY - rect.top) / rect.height - 0.5;
        card.style.transform = 'perspective(1000px) rotateY(' + (x * 5) + 'deg) rotateX(' + (-y * 5) + 'deg)';
      });
      card.addEventListener('mouseleave', function () {
        card.style.transform = '';
      });
    });
  }

  /* ── COUNTUP ── */
  function initCountUp() {
    var els = document.querySelectorAll('[data-countup]');
    if (!els.length) return;
    var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        io.unobserve(el);
        var target = parseFloat(el.getAttribute('data-countup'));
        var prefix = el.getAttribute('data-prefix') || '';
        var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
        var dur = 900;
        if (reduced || isNaN(target)) { el.textContent = prefix + (isNaN(target) ? el.textContent : target.toFixed(decimals)); return; }
        var start = null;
        function fmt(v) { return prefix + v.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }); }
        function step(ts) {
          if (!start) start = ts;
          var p = Math.min((ts - start) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = fmt(target * eased);
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.3 });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ── MODALS ── */
  function initModals() {
    document.querySelectorAll('[data-modal-open]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var m = document.getElementById(btn.getAttribute('data-modal-open'));
        if (m) m.classList.add('open');
      });
    });
    document.querySelectorAll('.modal-overlay').forEach(function (m) {
      m.addEventListener('click', function (e) {
        if (e.target === m) m.classList.remove('open');
      });
      var closeBtn = m.querySelector('.modal__close');
      if (closeBtn) closeBtn.addEventListener('click', function () { m.classList.remove('open'); });
    });
  }

  /* ── COOKIE BANNER ── */
  function initCookieBanner() {
    var banner = document.getElementById('cookie-banner');
    if (!banner) return;
    try {
      if (localStorage.getItem('cookie-consent') === '1') return;
      banner.hidden = false;
      document.getElementById('cookie-accept').addEventListener('click', function () {
        localStorage.setItem('cookie-consent', '1');
        banner.hidden = true;
      });
    } catch (e) { /* storage unavailable — leave hidden */ }
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initSidebar();
    initScrollFx();
    initFlashes();
    initCollapsibles();
    initReveals();
    initTilt();
    initCountUp();
    initModals();
    initCookieBanner();
  });
})();
