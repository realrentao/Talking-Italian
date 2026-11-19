/* 点击意大利语文本即发音：只播放上传的教材原声 mp3，不使用浏览器合成音 */
(function () {
  var current = null;

  window.speakEl = function (el) {
    var src = el.getAttribute('data-audio');
    if (!src) return;  // 无教材原声则静默，不回退浏览器合成音
    if (current) { try { current.pause(); } catch (e) {} }
    el.classList && (el.classList.add('speaking'));
    try {
      var a = new Audio(src);
      current = a;
      a.preload = 'auto';
      var clear = function () { el.classList && el.classList.remove('speaking'); };
      a.onended = clear;
      a.onerror = clear;  // 音频加载失败也只清状态，不出声
      var p = a.play();
      if (p && p.catch) p.catch(clear);
    } catch (e) {
      el.classList && el.classList.remove('speaking');
    }
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
