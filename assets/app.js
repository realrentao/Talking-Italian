/* 点击意大利语文本即发音（浏览器内置语音，it-IT） */
(function () {
  var voices = [];
  function loadVoices() {
    if (window.speechSynthesis) voices = window.speechSynthesis.getVoices() || [];
  }
  if (window.speechSynthesis) {
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }

  window.speakEl = function (el) {
    if (!window.speechSynthesis) {
      alert('当前浏览器不支持语音朗读，建议使用 Chrome 或 Edge。');
      return;
    }
    var text = (el.textContent || '').replace(/\s*🔊\s*/g, '').trim();
    if (!text) return;
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.lang = 'it-IT';
    u.rate = 0.86;
    u.pitch = 1;
    var v = voices.filter(function (x) { return /it[-_]IT/i.test(x.lang); })[0];
    if (v) u.voice = v;
    el.classList && (el.classList.add('speaking'));
    u.onend = u.onerror = function () {
      el.classList && el.classList.remove('speaking');
    };
    window.speechSynthesis.speak(u);
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
