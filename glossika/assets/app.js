/* Glossika 三语学习站：hash 路由 + 数据懒加载 + 显示模式 + 搜索。
   发音仅来自上传的教材原声 mp3；未上传原声则静默，不使用浏览器合成音。 */
(function () {
  var VIEWS = document.getElementById('view');
  var NAV = document.getElementById('nav-links');
  var DATA = {};
  var currentAudio = null;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'})[c];
    });
  }
  function shellNav(active) {
    NAV.innerHTML =
      '<a href="#/"' + (active === 'home' ? ' class="active"' : '') + '>总览</a>' +
      '<a href="#/book/1"' + (active === 'b1' ? ' class="active"' : '') + '>Fluency 1</a>' +
      '<a href="#/book/2"' + (active === 'b2' ? ' class="active"' : '') + '>Fluency 2</a>' +
      '<a href="#/book/3"' + (active === 'b3' ? ' class="active"' : '') + '>Fluency 3</a>' +
      '<a href="../index.html">← 书架</a>';
  }
  function loadData(book, cb) {
    if (DATA[book]) return cb(DATA[book]);
    var s = document.createElement('script');
    s.src = 'data/book' + book + '.js?v25';
    s.onload = function () { DATA[book] = window['GLOSSIKA_B' + book]; cb(DATA[book]); };
    s.onerror = function () { VIEWS.innerHTML = '<div class="wrap"><p>数据加载失败</p></div>'; };
    document.head.appendChild(s);
  }

  function home() {
    shellNav('home');
    VIEWS.innerHTML =
      '<header class="hero"><div class="hero-inner">' +
      '<span class="eyebrow">GLOSSIKA · ITALIAN FLUENCY</span>' +
      '<h1>Glossika 意大利语流利度</h1>' +
      '<p>三册共 3000 个高频句型，中 / 英 / 意三语逐句对照，附意大利语 IPA 发音。中文置顶，点击任意一行即可听对应原声发音；发音仅来自已上传的教材 mp3。</p>' +
      '<div class="hero-stats"><div class="hero-stat"><b>3</b><span>册</span></div>' +
      '<div class="hero-stat"><b>30</b><span>课</span></div>' +
      '<div class="hero-stat"><b>3000</b><span>句型</span></div></div>' +
      '<p style="margin-top:16px"><a href="#/lesson/G1-L01" style="display:inline-block;background:#fff;color:#C0392B;font-weight:700;padding:10px 20px;border-radius:10px">🎧 进入逐句原声发音（已上线 50 句）→</a></p>' +
      '</div></header>' +
      '<div class="wrap"><section class="section"><div class="section-head"><h2>选择分册</h2>' +
      '<span class="sub">每册 1000 句 · 分 10 课 · 每课 100 句</span></div><div class="card-grid">' +
      [1, 2, 3].map(function (b) {
        return '<a class="book-card" href="#/book/' + b + '"><span class="badge">FLUENCY ' + b + '</span>' +
          '<span class="card-no">BOOK 0' + b + '</span><h3>意大利语流利度 ' + b + '</h3>' +
          '<div class="orig">Glossika Italian Fluency ' + b + '</div>' +
          '<p>1000 个递进句型，覆盖日常、旅行、情感与抽象表达，按科学间隔重复编排。</p>' +
          '<span class="cta">进入分册 →</span></a>';
      }).join('') + '</div><div class="notice">中文为依据原书英文释义翻译的参考译文，意大利语原文与 IPA 均保留自原书。中 / 英 / 意三行均可点击听发音，发音只播放已上传的教材原声 mp3，不使用浏览器合成音；未上传原声的句子点击后静默。</div></section></div>' +
      footer();
  }

  function bookView(b) {
    shellNav('b' + b);
    loadData(b, function (d) {
      var cards = d.lessons.map(function (L) {
        return '<a class="day-card" href="#/lesson/G' + b + '-L' + String(L.lesson).padStart(2, '0') + '">' +
          '<div class="day-num">L' + String(L.lesson).padStart(2, '0') + '</div>' +
          '<div><h4>第 ' + L.lesson + ' 课</h4><span class="orig">句 ' + L.range[0] + '–' + L.range[1] + '</span>' +
          '<p>100 句中英意对照</p></div></a>';
      }).join('');
      VIEWS.innerHTML =
        '<header class="hero"><div class="hero-inner"><span class="eyebrow">BOOK 0' + b + '</span>' +
        '<h1>Italian Fluency ' + b + '</h1><p>Glossika Italian Fluency ' + b + ' · 1000 句 · 10 课</p></div></header>' +
        '<div class="wrap"><section class="section"><div class="section-head"><h2>课程列表</h2>' +
        '<span class="sub">按顺序学习，或任选一课</span></div><div class="day-grid">' + cards + '</div>' +
        '<div class="nav-buttons"><a class="btn" href="#/">← 返回总览</a></div></section></div>' + footer();
    });
  }

  function lessonView(id) {
    var m = /^G(\d)-L(\d+)$/.exec(id || '');
    if (!m) return home();
    var b = +m[1], li = +m[2];
    shellNav('b' + b);
    loadData(b, function (d) {
      var L = d.lessons[li - 1];
      if (!L) return home();
      function line(cls, txt, audio) {
        return '<div class="line ' + cls + '"' +
          (audio ? ' data-audio="' + esc(audio) + '" onclick="speakEl(this)"' : '') +
          '>' + esc(txt) + '</div>';
      }
      var rows = L.items.map(function (it) {
        return '<div class="sent" data-n="' + it.n + '"><div class="n">' + it.n + '</div><div class="body">' +
          line('zh', it.zh || '', it.zhAudio) +
          line('en', it.en, it.enAudio) +
          line('it', it.it, it.itAudio) +
          '<div class="ipa">' + esc(it.ipa) + '</div></div></div>';
      }).join('');
      VIEWS.innerHTML =
        '<div class="wrap"><div class="lesson-head"><span class="chip">FLUENCY ' + b + ' · 第 ' + li + ' 课</span>' +
        '<h2>第 ' + li + ' 课 · 句 ' + L.range[0] + '–' + L.range[1] + '</h2>' +
        '<a class="btn" style="margin-left:auto" href="#/book/' + b + '">返回分册</a></div>' +
        '<div class="toolbar"><input id="search" class="search" placeholder="搜索中文 / 英文 / 意大利语…">' +
        '<div class="modes"><button data-m="all" class="active">三语</button>' +
        '<button data-m="zh-it">中意</button><button data-m="it">仅意语</button></div></div>' +
        '<div id="list">' + rows + '</div>' +
        '<div class="nav-buttons">' +
        (li > 1 ? '<a class="btn" href="#/lesson/G' + b + '-L' + String(li - 1).padStart(2, '0') + '">← 上一课</a>' : '') +
        (li < d.lessons.length ? '<a class="btn primary" href="#/lesson/G' + b + '-L' + String(li + 1).padStart(2, '0') + '">下一课 →</a>' : '') +
        '</div></div>' + footer();
      bindLesson();
    });
  }

  function bindLesson() {
    var search = document.getElementById('search');
    search.addEventListener('input', function () {
      var q = search.value.trim().toLowerCase();
      document.querySelectorAll('#list .sent').forEach(function (el) {
        el.style.display = !q || el.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
      });
    });
    document.querySelectorAll('.modes button').forEach(function (btn) {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.modes button').forEach(function (x) { x.classList.remove('active'); });
        btn.classList.add('active');
        var m = btn.getAttribute('data-m');
        document.querySelectorAll('#list .sent').forEach(function (el) {
          el.classList.toggle('hide-en', m !== 'all');
          el.classList.toggle('hide-zh', m === 'it');
          /* IPA 常显，任何模式都不隐藏 */
        });
      });
    });
  }

  // 只播放上传的教材原声 mp3；无 data-audio 则静默，绝不回退浏览器合成音
  window.speakEl = function (el) {
    var src = el.getAttribute('data-audio');
    if (!src) return;
    if (currentAudio) { try { currentAudio.pause(); } catch (e) {} }
    document.querySelectorAll('#list .line.playing').forEach(function (x) { x.classList.remove('playing'); });
    var row = el.closest ? el.closest('.sent') : null;
    if (row) row.classList.add('speaking');
    el.classList.add('playing');
    var clear = function () { el.classList.remove('playing'); if (row) row.classList.remove('speaking'); };
    try {
      var a = new Audio(src);
      currentAudio = a;
      a.preload = 'auto';
      a.onended = clear;
      a.onerror = clear;
      var p = a.play();
      if (p && p.catch) p.catch(clear);
    } catch (e) {
      clear();
    }
  };

  function footer() {
    return '<footer class="site-footer">Glossika Italian Fluency 1–3 · 中英意三语对照学习站 · 发音仅来自上传的原声 mp3</footer>';
  }

  function route() {
    var hash = location.hash.replace(/^#\/?/, '');
    if (!hash) return home();
    if (hash.indexOf('book/') === 0) return bookView(+hash.split('/')[1]);
    if (hash.indexOf('lesson/') === 0) return lessonView(hash.split('/')[1]);
    home();
  }
  window.addEventListener('hashchange', route);
  route();
})();
