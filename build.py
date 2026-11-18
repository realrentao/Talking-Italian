# -*- coding: utf-8 -*-
"""从 _source/content/*.json 生成 Talking-Italian 静态站点。"""
import json, os, html, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, '_source', 'content')
SITE = os.path.join(ROOT, 'site')

def esc(s):
    return html.escape(str(s), quote=False)

def load(name):
    with open(os.path.join(SRC, name + '.json'), encoding='utf-8') as f:
        return json.load(f)

# 教材原声切片映射（可选；未生成时自动回退浏览器合成音）
AUDIO = {}
_audio_path = os.path.join(ROOT, '_source', 'audio_map.json')
if os.path.exists(_audio_path):
    with open(_audio_path, encoding='utf-8') as f:
        _audio_raw = json.load(f)
    for _day, _info in _audio_raw.items():
        for _item in _info.get('items', []):
            AUDIO[_item['key']] = _item

def audio_attr(day, group, idx):
    if day is None:
        return ''
    key = 'gt%02d.%s.%d' % (day, group, idx)
    if key not in AUDIO:
        return ''
    rel = 'audio/get/gt%02d/%s_%d.mp3' % (day, group, idx)
    if not os.path.exists(os.path.join(SITE, rel)):
        return ''
    return ' data-audio="../../%s"' % rel

def shell(title, depth, body, breadcrumb='', active=''):
    p = '../' * depth
    crumb = '<div class="wrap narrow"><div class="crumbs">%s</div></div>' % breadcrumb if breadcrumb else ''
    nav = '''<div class="scroll-progress"></div>
<nav class="top-nav"><div class="top-nav-inner">
  <a class="brand" href="%sindex.html"><span class="brand-mark">IT</span><span>意大利语学习书架</span></a>
  <div class="nav-links">
    <a href="%sindex.html"%s>总导航</a>
    <a href="%stalking-ten-days/index.html"%s>Talking Italian</a>
  </div>
</div></nav>''' % (p, p, ' class="active"' if active == 'home' else '',
                   p, ' class="active"' if active == 'book' else '')
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · 意大利语学习书架</title>
<link rel="stylesheet" href="%sassets/style.css">
</head>
<body>
%s
%s
%s
<footer class="site-footer">为意大利语学习者整理 · 意大利语原文点击即可发音 · <a href="%sindex.html">返回总导航</a></footer>
<script src="%sassets/app.js"></script>
</body>
</html>
''' % (esc(title), p, nav, crumb, body, p, p)

def write(path, content):
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print('WROTE', path)

def home_crumb():
    return ''

def book_crumb():
    return '<a href="../index.html">总导航</a><span>/</span>Talking Italian'

def vol_crumb(vol_name):
    return '<a href="../../index.html">总导航</a><span>/</span><a href="../index.html">Talking Italian</a><span>/</span>' + vol_name

def lesson_crumb(vol_name, title, back):
    return ('<a href="../../index.html">总导航</a><span>/</span>'
            '<a href="../index.html">Talking Italian</a><span>/</span>'
            '<a href="%s">%s</a><span>/</span>%s' % (back, vol_name, esc(title)))

# ---------- 总导航页 ----------
def build_home():
    cards = []
    cards.append('''<article class="book-card">
  <div class="card-top"><span class="badge live">已接入 · 第 1 册</span><span class="card-no">BOOK 01</span></div>
  <h3>十天开口说 · 十天流利说</h3>
  <div class="orig">Get Talking / Keep Talking Italian in Ten Days</div>
  <p class="desc">一套两册的意大利语口语教程，共 20 天课程。本套只是全部教材中的一册，后续教材将按同样的层级与入口规则陆续接入。</p>
  <div class="tag-row"><span class="tag">A1 入门</span><span class="tag">20 天课程</span><span class="tag">意中对照</span><span class="tag">点击发音</span></div>
  <a class="card-cta" href="talking-ten-days/index.html">进入教材</a>
</article>''')
    for i in range(2, 6):
        cards.append('''<article class="book-card placeholder">
  <div class="card-top"><span class="badge soon">预留入口</span><span class="card-no">BOOK %02d</span></div>
  <div class="slot-mark">＋</div>
  <h3>教材待接入</h3>
  <div class="orig">Slot reserved for a future textbook</div>
  <p class="desc">同层级预留位。新增教材时只需在此追加一张同版式卡片，并接入对应的教材首页，现有内容无需改动。</p>
  <div class="tag-row"><span class="tag">待定</span><span class="tag">同版式入口</span></div>
  <span class="card-cta">即将接入</span>
</article>''' % i)
    body = '''<header class="hero"><div class="hero-inner">
  <span class="eyebrow">ITALIANO · 中文学习者专用</span>
  <h1>意大利语学习书架</h1>
  <p>以教材为单位组织学习。点开一册，逐级展开课程；学完随时回到这里，切换到下一册。</p>
  <div class="hero-stats">
    <div class="hero-stat"><b>1</b><span>已接入教材</span></div>
    <div class="hero-stat"><b>20</b><span>可学课程</span></div>
    <div class="hero-stat"><b>4</b><span>预留教材位</span></div>
  </div>
</div></header>
<div class="wrap"><section class="section">
  <div class="section-head"><h2>教材书架</h2><span class="sub">每册一个入口 · 版式与展开规则一致</span></div>
  <div class="card-grid">%s</div>
  <div class="notice"><b>说明：</b>当前接入的《十天开口说 · 十天流利说》只是全部教材中的一册，并非唯一教材。其余卡片为同层级预留位，后续可直接追加，无需改动现有页面。</div>
</section></div>''' % '\n'.join(cards)
    write('index.html', shell('总导航', 0, body, active='home'))

# ---------- 教材首页 ----------
def build_book():
    body = '''<header class="hero"><div class="hero-inner">
  <span class="eyebrow">BOOK 01 · 已接入教材</span>
  <h1>Talking Italian in Ten Days</h1>
  <p>本册由两本音频教程组成：<b>Get Talking</b> 带你从零开口，<b>Keep Talking</b> 帮你把话说顺。两册各 10 天，英文讲解已整理为润色中文，意大利语原文保留并可点击发音。</p>
  <div class="hero-stats">
    <div class="hero-stat"><b>2</b><span>分册</span></div>
    <div class="hero-stat"><b>20</b><span>天课程</span></div>
    <div class="hero-stat"><b>900+</b><span>意中对照条目</span></div>
  </div>
</div></header>
<div class="wrap"><section class="section">
  <div class="section-head"><h2>选择分册</h2><span class="sub">从分册页进入每天的课程</span></div>
  <div class="card-grid">
    <article class="book-card">
      <div class="card-top"><span class="badge">分册一 · 入门</span><span class="card-no">PART A</span></div>
      <h3>十天开口说</h3><div class="orig">Get Talking Italian in Ten Days</div>
      <p class="desc">打车、租车、公交、订房、咖啡馆、餐厅、购物、博物馆、歌剧、药店——把旅行中最常用的 10 个场景说出口。</p>
      <div class="tag-row"><span class="tag">10 天</span><span class="tag">零起点</span><span class="tag">场景对话</span></div>
      <a class="card-cta" href="get-talking/index.html">进入分册</a>
    </article>
    <article class="book-card">
      <div class="card-top"><span class="badge">分册二 · 进阶</span><span class="card-no">PART B</span></div>
      <h3>十天流利说</h3><div class="orig">Keep Talking Italian in Ten Days</div>
      <p class="desc">坐火车、问路、电话订位、到店用餐、逛集市、品酒、节庆、交友、聊工作、回顾假期——把话说得更自然。</p>
      <div class="tag-row"><span class="tag">10 天</span><span class="tag">进阶</span><span class="tag">表达扩展</span></div>
      <a class="card-cta" href="keep-talking/index.html">进入分册</a>
    </article>
  </div>
  <div class="notice">学习路径：<b>总导航 → 本页 → 分册 → 每天课程</b>。每一页都可返回上一级；课程页底部可直接回到总导航。</div>
</section></div>'''
    write('talking-ten-days/index.html', shell('Talking Italian', 1, body, book_crumb(), active='book'))

VOL = {
    'get': ('get-talking', '十天开口说', 'Get Talking Italian in Ten Days',
            '从零开始，用十天走完旅行中最常见的十个场景。每天一组核心句型、一段真实对话、若干拓展表达与小练习。'),
    'keep': ('keep-talking', '十天流利说', 'Keep Talking Italian in Ten Days',
             '在已有基础上把话说顺。每天一个生活场景，加入更多表达、语法提示与开口练习。')
}
DAY_TITLES = {}

def build_volume(key):
    slug, zh, orig, desc = VOL[key]
    days = [load('%s%02d' % ('gt' if key == 'get' else 'kt', i)) for i in range(1, 11)]
    DAY_TITLES[key] = {d['day']: d['title'] for d in days}
    cards = []
    for d in days:
        cards.append('''<a class="day-card" href="day-%02d.html">
  <div class="day-num">D%02d</div>
  <div><h4>第 %d 天 · %s</h4><span class="orig">%s</span><p>%s</p></div>
</a>''' % (d['day'], d['day'], d['day'], esc(d['title']), esc(d['orig']), esc(d['lead'])))
    extra = ''
    if key == 'keep':
        extra = '''<a class="day-card" href="expressions.html" style="border-style:dashed">
  <div class="day-num" style="background:linear-gradient(135deg,#1A5276,#2E86C1)">速查</div>
  <div><h4>实用表达速查</h4><span class="orig">Useful expressions</span><p>数字、星期、月份与救急短句，随时回来查。</p></div>
</a>'''
    body = '''<header class="unit-hero"><div class="unit-hero-inner">
  <span class="level-pill">%s</span>
  <h1>%s</h1><div class="orig">%s</div><p>%s</p>
  <div class="meta-row"><div><b>10</b>天课程</div><div><b>点击</b>意大利语发音</div><div><b>中文</b>讲解与译文</div></div>
</div></header>
<div class="wrap"><section class="section">
  <div class="section-head"><h2>十天课程</h2><span class="sub">按顺序学，也可以挑感兴趣的一天</span></div>
  <div class="day-grid">%s%s</div>
  <div class="nav-buttons">
    <a class="nav-btn" href="../index.html">← 返回教材首页</a>
    <a class="nav-btn primary" href="../../index.html">返回总导航 →</a>
  </div>
</section></div>''' % ('分册一 · 入门' if key == 'get' else '分册二 · 进阶',
                       esc(zh), esc(orig), esc(desc), '\n'.join(cards), extra)
    write('talking-ten-days/%s/index.html' % slug, shell(zh, 2, body, vol_crumb(zh), active='book'))

# ---------- 课程页 ----------
def phrase_table(items, day=None, group='core'):
    rows = ''.join('<tr><td class="it" onclick="speakEl(this)"%s>%s</td><td class="zh">%s</td></tr>'
                   % (audio_attr(day, group, i), esc(x['it']), esc(x['zh']))
                   for i, x in enumerate(items))
    return '<table class="vocab"><thead><tr><th>意大利语（点击发音）</th><th>中文</th></tr></thead><tbody>%s</tbody></table>' % rows

def dialogue_block(lines, day=None):
    out = []
    for i, x in enumerate(lines):
        out.append('''<div class="dlg-line">
  <div class="dlg-who">%s</div>
  <div class="dlg-it" onclick="speakEl(this)"%s>%s</div>
  <div class="dlg-zh">%s</div>
</div>''' % (esc(x['who']), audio_attr(day, 'dialogue', i), esc(x['it']), esc(x['zh'])))
    return '<div class="dialogue">%s</div>' % ''.join(out)

def build_lesson(key, d):
    slug, volzh, _, _ = VOL[key]
    n = d['day']
    goals = ''.join('<li>%s</li>' % esc(g) for g in d['goals'])
    tasks = ''.join('<li>%s</li>' % esc(t) for t in d['tasks'])
    tips = ''.join('<div class="tip-box"><b>语言提示 · </b>%s</div>' % esc(t) for t in d['tips'])
    prev = ('day-%02d.html' % (n - 1)) if n > 1 else None
    nxt = ('day-%02d.html' % (n + 1)) if n < 10 else None
    nav = '<div class="nav-buttons">'
    nav += '<a class="nav-btn %s" href="%s">← 上一天</a>' % ('' if prev else 'disabled', prev or '#')
    nav += '<a class="nav-btn" href="index.html">返回分册</a>'
    nav += '<a class="nav-btn %s" href="%s">下一天 →</a>' % ('' if nxt else 'disabled', nxt or '#')
    nav += '</div><div class="nav-buttons" style="padding-top:0"><a class="nav-btn primary" href="../../index.html">返回总导航 →</a></div>'
    audio_day = n if key == 'get' else None
    plus_html = ''
    if d.get('plus'):
        plus_html = ('<section class="panel"><h2><span class="ico">➕</span>%s</h2>%s</section>'
                     % (esc(d.get('plusTitle', '拓展表达')),
                        phrase_table(d['plus'], audio_day, 'plus')))
    body = '''<header class="lesson-hero"><div class="lesson-hero-inner">
  <span class="day-chip">DAY %02d · 第 %d 天</span>
  <h1>%s</h1><p class="orig">%s</p><p class="lead">%s</p>
</div></header>
<div class="wrap narrow">
  <section class="panel"><h2><span class="ico">🎯</span>今天要学会</h2><p class="hint">学完这一课，你应该能够：</p><ul class="goals">%s</ul></section>
  <section class="panel"><h2><span class="ico">💬</span>核心表达</h2><p class="hint">点击意大利语即可听发音；优先播放教材原声，其余为浏览器合成音。</p>%s</section>
  <section class="panel"><h2><span class="ico">🗣️</span>情景对话</h2><p class="hint">先听懂，再跟读；说话人按角色标注。</p>%s</section>
  <section class="panel"><h2><span class="ico">📖</span>%s</h2>%s</section>
  %s
  <section class="panel"><h2><span class="ico">🧩</span>%s</h2><p class="hint">教材原有听力与跟读任务，已整理为中文。</p><ol class="task-list">%s</ol></section>
  <section class="panel"><h2><span class="ico">💡</span>语言提示</h2>%s</section>
  %s
</div>''' % (n, n, esc(d['title']), esc(d['orig']), esc(d['lead']), goals,
             phrase_table(d['core'], audio_day, 'core'),
             dialogue_block(d['dialogue'], audio_day),
             esc(d['extraTitle']), phrase_table(d['extra'], audio_day, 'extra'),
             plus_html,
             '练习与跟读', tasks, tips, nav)
    crumb = lesson_crumb(volzh, d['title'], 'index.html')
    write('talking-ten-days/%s/day-%02d.html' % (slug, n), shell('第%d天 · %s' % (n, d['title']), 2, body, crumb, active='book'))

# ---------- 速查页 ----------
def build_expressions():
    d = load('kt00')
    groups = []
    for sec in d['sections']:
        rows = ''.join('<tr><td class="it" onclick="speakEl(this)">%s</td><td class="zh">%s</td></tr>'
                       % (esc(x['it']), esc(x['zh'])) for x in sec['items'])
        groups.append('''<div class="ref-group"><h2>%s</h2>
<table class="vocab"><thead><tr><th>意大利语（点击发音）</th><th>中文</th></tr></thead><tbody>%s</tbody></table></div>'''
                       % (esc(sec['title']), rows))
    body = '''<header class="unit-hero"><div class="unit-hero-inner">
  <span class="level-pill">随查随用</span><h1>%s</h1><div class="orig">%s</div><p>%s</p>
</div></header>
<div class="wrap narrow"><section class="section">%s</section>
  <div class="nav-buttons">
    <a class="nav-btn" href="index.html">← 返回分册</a>
    <a class="nav-btn primary" href="../../index.html">返回总导航 →</a>
  </div>
</div>''' % (esc(d['title']), esc(d['orig']), esc(d['lead']), ''.join(groups))
    write('talking-ten-days/keep-talking/expressions.html', shell('实用表达速查', 2, body,
          vol_crumb('十天流利说') + '<span>/</span>实用表达速查', active='book'))

def main():
    os.makedirs(SITE, exist_ok=True)
    build_home()
    build_book()
    for key in ('get', 'keep'):
        build_volume(key)
        for n in range(1, 11):
            build_lesson(key, load('%s%02d' % ('gt' if key == 'get' else 'kt', n)))
    build_expressions()
    print('DONE')

if __name__ == '__main__':
    main()
