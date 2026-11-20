/* 点击意大利语文本即发音：只播放上传的教材原声 mp3，不使用浏览器合成音。
   性能：音频对象池复用（同一 src 不重复下载）+ 相邻句空闲预加载。 */
(function () {
  var current = null;          // 当前正在播放的 Audio
  var pool = {};               // src -> Audio 缓存，避免重复创建/下载
  var idle = window.requestIdleCallback || function (fn) { return setTimeout(fn, 300); };

  function getAudio(src) {
    var a = pool[src];
    if (!a) {
      a = new Audio(src);
      a.preload = 'auto';
      pool[src] = a;
    }
    return a;
  }

  // 收集页面上所有可发音元素，预加载当前句附近的几句（只取 metadata，省流量）
  function prewarm(el) {
    var nodes = [].slice.call(document.querySelectorAll('[data-audio]'));
    var i = nodes.indexOf(el);
    if (i < 0) return;
    var near = [];
    for (var d = 1; d <= 2; d++) {
      if (nodes[i - d]) near.push(nodes[i - d]);
      if (nodes[i + d]) near.push(nodes[i + d]);
    }
    idle(function () {
      near.forEach(function (n) {
        var src = n.getAttribute('data-audio');
        if (src && !pool[src]) {
          var a = new Audio(src);
          a.preload = 'metadata';
          pool[src] = a;
        }
      });
    });
  }

  window.speakEl = function (el) {
    var src = el.getAttribute('data-audio');
    if (!src) return;  // 无教材原声则静默，不回退浏览器合成音
    if (current) {
      try { current.pause(); current.currentTime = 0; } catch (e) {}
    }
    document.querySelectorAll('.speaking').forEach(function (x) { x.classList.remove('speaking'); });
    el.classList && (el.classList.add('speaking'));
    try {
      var a = getAudio(src);
      current = a;
      var clear = function () { el.classList && el.classList.remove('speaking'); };
      a.onended = clear;
      a.onerror = clear;
      try { a.currentTime = 0; } catch (e) {}
      var p = a.play();
      if (p && p.catch) p.catch(clear);
      prewarm(el);
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
