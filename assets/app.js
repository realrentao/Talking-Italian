/* 点击意大利语文本即发音：优先教材原声，缺失时回退浏览器 it-IT 合成音 */
(function () {
  var voices = [];
  var current = null;
  function loadVoices() {
    if (window.speechSynthesis) voices = window.speechSynthesis.getVoices() || [];
  }
  if (window.speechSynthesis) {
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }

  function tts(el, text) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = 'it-IT';
    u.rate = 0.86;
    u.pitch = 1;
    var v = voices.filter(function (x) { return /it[-_]IT/i.test(x.lang); })[0];
    if (v) u.voice = v;
    u.onend = u.onerror = function () { el.classList && el.classList.remove('speaking'); };
    window.speechSynthesis.speak(u);
  }

  window.speakEl = function (el) {
    var text = (el.textContent || '').replace(/\s*🔊\s*/g, '').trim();
    if (!text) return;
    if (current) { try { current.pause(); } catch (e) {} }
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    el.classList && (el.classList.add('speaking'));

    var src = el.getAttribute('data-audio');
    if (src) {
      var done = false;
      var fallback = function () {
        if (done) return;
        done = true;
        tts(el, text);
      };
      try {
        var a = new Audio(src);
        current = a;
        a.preload = 'auto';
        a.onended = function () {
          done = true;
          el.classList && el.classList.remove('speaking');
        };
        a.onerror = fallback;
        var p = a.play();
        if (p && p.catch) p.catch(fallback);
      } catch (e) {
        fallback();
      }
      return;
    }
    tts(el, text);
  };

  // 滚动进度条 + 导航滚动变色
  var bar = document.querySelector('.scroll-progress');
  var nav = document.querySelector('.top-nav');
  function update() {
    var h = document.documentElement;
    var p = h.scrollTop / Math.max(1, h.scrollHeight - h.clientHeight) * 100;
    if (bar) bar.style.width = p + '%';
    if (nav) nav.style.boxShadow = h.scrollTop > 12 ? '0 4px 18px rgba(60,45,25,.08)' : '';
  }
  window.addEventListener('scroll', update, { passive: true });
  update();
})();
