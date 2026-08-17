/* Chart.js loader (vendor-first, CDN fallback) + dashboard helpers. */
(function () {
  'use strict';

  var PALETTE = ['#818cf8', '#34d399', '#67e8f9', '#a855f7', '#f59e0b', '#f43f5e', '#38bdf8', '#f97316'];

  function isDark() {
    return document.documentElement.getAttribute('data-theme') !== 'light';
  }

  function baseOpts() {
    var dark = isDark();
    var grid = dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.07)';
    var ticks = dark ? '#a1a1aa' : '#4a4a52';
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: ticks, boxWidth: 10, boxHeight: 10, usePointStyle: true, padding: 14, font: { family: 'Inter', size: 11 } }
        },
        tooltip: {
          backgroundColor: dark ? 'rgba(13,13,17,0.92)' : 'rgba(255,255,255,0.95)',
          titleColor: dark ? '#f5f5f7' : '#0e0e11',
          bodyColor: dark ? '#a1a1aa' : '#4a4a52',
          borderColor: dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
          usePointStyle: true,
          callbacks: {
            labelColor: function (c) { return { backgroundColor: c.dataset.borderColor || c.dataset.backgroundColor || '#818cf8' }; }
          }
        }
      },
      scales: {
        x: { grid: { color: grid }, ticks: { color: ticks, font: { family: 'Inter', size: 11 } } },
        y: { grid: { color: grid }, ticks: { color: ticks, font: { family: 'Inter', size: 11 } } }
      }
    };
  }

  window.ATMCharts = {
    palette: PALETTE,
    isDark: isDark,

    color: function (i) { return PALETTE[i % PALETTE.length]; },

    alpha: function (hex, a) {
      var n = parseInt(hex.slice(1), 16);
      var r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
      return 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')';
    },

    base: baseOpts,

    /* Build a Chart from a config object stored in data-chart JSON. */
    initAll: function () {
      document.querySelectorAll('[data-chart]').forEach(function (el) {
        if (el.getAttribute('data-chart-init')) return;
        if (el.closest('.collapsible.is-collapsed')) return;
        if (el.offsetParent === null && !document.body.contains(el)) return;
        var spec;
        try { spec = JSON.parse(el.getAttribute('data-chart')); } catch (e) { return; }
        var ctx = el.getContext('2d');
        if (!ctx) return;
        var opts = baseOpts();
        if (spec.options) opts = Object.assign({}, opts, spec.options);
        var ds = (spec.datasets || []).map(function (d, i) {
          var c = d.color || PALETTE[i % PALETTE.length];
          return Object.assign({}, d, { borderColor: c, backgroundColor: d.backgroundColor || (spec.type === 'line' ? ATMCharts.alpha(c, 0.15) : c) });
        });
        new Chart(ctx, { type: spec.type || 'bar', data: { labels: spec.labels || [], datasets: ds }, options: opts });
        el.setAttribute('data-chart-init', '1');
      });
    }
  };

  /* Chart.js lazy loader: vendor file first, CDN fallback. */
  function loadChart() {
    return new Promise(function (resolve, reject) {
      if (window.Chart) { resolve(window.Chart); return; }
      var urls = [
        document.body.getAttribute('data-chart-vendor') || '/static/vendor/chart.umd.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js'
      ];
      var i = 0;
      (function tryNext() {
        if (i >= urls.length) { reject(new Error('Chart.js failed to load')); return; }
        var s = document.createElement('script');
        s.src = urls[i++];
        s.onload = function () { window.Chart ? resolve(window.Chart) : tryNext(); };
        s.onerror = tryNext;
        document.head.appendChild(s);
      })();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (!document.querySelector('[data-chart]')) return;
    loadChart().then(function () {
      ATMCharts.initAll();
      document.addEventListener('atm-collapse-changed', function () { ATMCharts.initAll(); });
    }).catch(function () {});
  });
})();
