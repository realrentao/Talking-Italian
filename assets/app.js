/* 点击意大利语文本即发音：只播放上传的教材原声 mp3，不使用浏览器合成音。
   ima/WebView 优化：单 Audio 实例 + preload=none；点击后用 fetch 低优先级预取相邻 2 句；
   小体积 Blob URL 缓存（LRU 6），避免内置浏览器里一堆 Audio 同时抢网络。 */
(function () {
  var player = null;                  // 全页共用一个 Audio，避免对象池无限膨胀
  var currentSrc = null;              // 当前播放对应的原始 src（用于保护 Blob）
  var blobUrls = Object.create(null); // src -> blob URL
  var pending = Object.create(null);  // 正在预取的 src
  var cacheOrder = [];                // LRU
  var queue = [];                     // 串行预取队列
  var fetching = false;
  var MAX_CACHE = 6;
  var idle = window.requestIdleCallback
    ? function (fn) { window.requestIdleCallback(fn, { timeout: 600 }); }
    : function (fn) { setTimeout(fn, 200); };
  var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  var canFetch = typeof fetch === 'function' &&
                 typeof URL !== 'undefined' && typeof URL.createObjectURL === 'function';

  function ensurePlayer() {
    if (!player) {
      player = new Audio();
      player.preload = 'none';   // 关键：ima/WebView 下 auto/metadata 都可能被当成整文件预取
      player.setAttribute('playsinline', '');
    }
    return player;
  }

  function revoke(src) {
    var u = blobUrls[src];
    if (!u) return;
    try { URL.revokeObjectURL(u); } catch (e) {}
    delete blobUrls[src];
  }

  function remember(src, url) {
    if (blobUrls[src]) return;
    blobUrls[src] = url;
    cacheOrder.push(src);
    while (cacheOrder.length > MAX_CACHE) {
      var old = cacheOrder.shift();
      if (old === currentSrc) { cacheOrder.push(old); continue; }
      revoke(old);
    }
  }

  // 串行、低优先级预取；音频都很小，播放中保持 1 个请求，点下一句才能命中缓存
  function pump() {
    if (fetching || !queue.length || !canFetch) return;
    var src = queue.shift();
    var ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, 8000);
    var opt = { credentials: 'omit', cache: 'default' };
    if (ctrl) opt.signal = ctrl.signal;
    try { opt.priority = 'low'; } catch (e) {}  // Chromium 认；其它内核忽略
    fetching = true;
    fetch(src, opt)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.blob(); })
      .then(function (b) { remember(src, URL.createObjectURL(b)); })
      .catch(function () {})
      .then(function () {
        clearTimeout(timer);
        delete pending[src];
        fetching = false;
        pump();
      });
  }

  function enqueue(src) {
    if (!src || !canFetch || blobUrls[src] || pending[src]) return;
    if (conn && conn.saveData) return;   // 省流量模式不预取
    pending[src] = true;
    queue.push(src);
    pump();
  }

  // 只在首次点击后预热相邻 2 句：上一句 + 下一句
  function prewarm(el) {
    var nodes = [].slice.call(document.querySelectorAll('[data-audio]'));
    var i = nodes.indexOf(el);
    if (i < 0) return;
    var near = [];
    if (nodes[i - 1]) near.push(nodes[i - 1]);
    if (nodes[i + 1]) near.push(nodes[i + 1]);
    idle(function () {
      if (document.hidden) return;
      near.forEach(function (n) { enqueue(n.getAttribute('data-audio')); });
    });
  }

  window.speakEl = function (el) {
    var src = el.getAttribute('data-audio');
    if (!src) return;  // 无教材原声则静默，不回退浏览器合成音
    document.querySelectorAll('.speaking').forEach(function (x) { x.classList.remove('speaking'); });
    el.classList && (el.classList.add('speaking'));

    var a = ensurePlayer();
    try { a.pause(); } catch (e) {}
    var url = blobUrls[src] || src;
    if (a.src !== url) a.src = url;   // 有缓存则同步切到 blob，点击当帧就能 play
    currentSrc = src;
    try { a.currentTime = 0; } catch (e) {}
    var clear = function () { el.classList && el.classList.remove('speaking'); };
    a.onended = clear;
    a.onerror = clear;
    try {
      var p = a.play();
      if (p && p.catch) p.catch(clear);
    } catch (e) {
      clear();
    }
    prewarm(el);
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
