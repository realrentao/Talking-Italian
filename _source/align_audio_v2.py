# -*- coding: utf-8 -*-
"""对齐 v2：基于词级时间戳精确定位，解决断头断尾与漏匹配。

改进点：
1. 用每个词的 s/e 作为切片边界（不是整段 boundary）→ 不切半个词
2. 词级 + 字符级混合相似度 → 容忍 tiny 的听错（echo≈ecco, di ecci≈dieci）
3. 短句严格阈值防错配（"Buongiorno." 不再命中无关句）
4. 全局词流滑窗 → 一句话跨多个 segment 也能命中
5. 记录 matched words，便于人工核查
"""
import json, os, re, sys, unicodedata, difflib, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
WORDSDIR = os.environ.get('WORDS_DIR', os.path.join(ROOT, 'transcript_words'))
CONTENT = os.path.join(ROOT, 'content')
OUT = os.environ.get('OUT', os.path.join(ROOT, 'audio_map_v2.json'))

NUMWORDS = {'uno':'1','una':'1','due':'2','tre':'3','quattro':'4','cinque':'5',
            'sei':'6','sette':'7','otto':'8','nove':'9','dieci':'10',
            'undici':'11','dodici':'12','tredici':'13','quattordici':'14',
            'quindici':'15','sedici':'16','diciassette':'17','diciotto':'18',
            'diciannove':'19','venti':'20','trenta':'30','quaranta':'40',
            'cinquanta':'50','sessanta':'60','settanta':'70','ottanta':'80',
            'novanta':'90','cento':'100','mille':'1000'}
# tiny 常见听错 → 归一（提升匹配）
FIX = {'echo':'ecco','eccho':'ecco','ecco':'ecco','albergo':'albergo','albargo':'albergo',
       'regina':'regina','margarita':'margherita','margherita':'margherita',
       'di ecci':'dieci','dieci':'dieci','patche':'pace','pace':'pace',
       'quali':'quale','quale':'quale','ecci':'dieci','sonno':'sono','sono':'sono',
       ' grazie':'grazie','arrivederci':'arrivederci','buongiorno':'buongiorno',
       'caffe':'caffe','caffè':'caffe'}


def norm(s, digits=False):
    s = unicodedata.normalize('NFKD', str(s).lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('’', "'").replace('‘', "'")
    s = re.sub(r'[^a-z0-9\']+', ' ', s)
    s = re.sub(r'\b(e|ed)\b', 'e', s)
    if digits:
        s = ' '.join(NUMWORDS.get(w, w) for w in s.split())
    s = ' '.join(s.split())
    return s


def fixword(w):
    return FIX.get(w, w)


def load_words():
    """合并所有分段词级转写为全局词流。"""
    segs = []
    for f in sorted(glob.glob(os.path.join(WORDSDIR, 'seg_*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            try:
                segs.append(json.loads(line))
            except Exception:
                pass
    segs.sort(key=lambda r: r['start'])
    # 段去重（相邻起点 < 0.3 且文本更长的保留）
    ded = []
    for r in segs:
        if ded and r['start'] - ded[-1]['start'] < 0.3:
            if len(r.get('text','')) > len(ded[-1].get('text','')):
                ded[-1] = r
            continue
        ded.append(r)
    # 展平词流
    wf = []
    for r in ded:
        for w in (r.get('words') or []):
            t = fixword(norm(w.get('w','')))
            if not t or w.get('s') is None or w.get('e') is None:
                continue
            wf.append({'w': t, 's': round(w['s'],3), 'e': round(w['e'],3)})
    wf.sort(key=lambda x: x['s'])
    # 词去重（重叠段边界）
    uniq = []
    for w in wf:
        if uniq and abs(w['s'] - uniq[-1]['s']) < 0.12 and w['w'] == uniq[-1]['w']:
            continue
        uniq.append(w)
    return uniq, ded


def word_ratio(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def char_ratio(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def score_window(tw, win):
    """目标词序列 vs 候选词窗口：词级为主，字符级兜底听错。
    首尾多余的无关词（上一句尾巴）按数量扣分，让干净窗口胜出。"""
    ww = [x['w'] for x in win]
    wr = word_ratio(tw, ww)
    cr = char_ratio(' '.join(tw), ' '.join(ww))
    sc = max(wr, cr * 0.92)
    # 首尾多余词惩罚
    sm = difflib.SequenceMatcher(None, tw, ww, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size > 0]
    if blocks:
        lead = blocks[0].b
        trail = len(ww) - (blocks[-1].b + blocks[-1].size)
        sc *= (0.88 ** (lead + trail))
    return sc


def match(target, wf, lo, hi, after=0.0, strict=False):
    """在 [lo,hi] 词流中找目标句；返回 {start,end,score,matched}。"""
    tw = [fixword(x) for x in norm(target, digits=True).split()]
    if not tw:
        return None
    pool = [w for w in wf if lo - 0.5 <= w['s'] <= hi and w['e'] > after - 0.3]
    if len(pool) < len(tw):
        return None
    n = len(tw)
    # 短句要求接近完整匹配；长句容忍 tiny 漏词/多词
    sizes = ([n] if n <= 2 else [n-1, n, n+1, n+2] if n <= 6
             else [n-2, n-1, n, n+1, n+2, n+3])
    thr = 0.68 if strict or n <= 3 else 0.52
    cands = []
    for size in sizes:
        if size < 1 or size > len(pool):
            continue
        for i in range(0, len(pool) - size + 1):
            win = pool[i:i+size]
            if win[0]['s'] < after - 0.8:
                continue
            sc = score_window(tw, win)
            # 短句首词必须出现（防 "Ecco l'albergo" 只命中 "l'albergo"）；
            # 长句轻罚，因 tiny 常把首词翻成英文（Buongiorno→morning）
            if tw[0] not in [x['w'] for x in win]:
                sc *= 0.62 if n <= 4 else 0.88
            if n <= 3 and size > n + 1:
                sc *= 0.85
            if sc < thr:
                continue
            cands.append({'score': round(sc,3), 'start': win[0]['s'],
                          'end': win[-1]['e'], 'matched': ' '.join(x['w'] for x in win)})
    if not cands:
        return None
    # 分数接近时优先更早 occurrence（教材常在重复跟读段复述同一句，
    # 真实对话在先）。取最高分 -0.06 以内的候选中最早的一个。
    top = max(c['score'] for c in cands)
    near = [c for c in cands if c['score'] >= top - 0.06]
    near.sort(key=lambda c: c['start'])
    return near[0]


def detect_part2(segs, lo, hi):
    """在当天窗口内检测 'part two' 对话起点。"""
    cands = []
    for r in segs:
        if not (lo <= r['start'] <= hi):
            continue
        t = norm(r.get('text',''))
        if ('part two' in t or 'part 2' in t or 'listen carefully' in t
                or 'listen to the conversation' in t):
            cands.append(r['start'])
    return min(cands) if cands else None


def main():
    wf, segs = load_words()
    print('segments', len(segs), 'words', len(wf))
    print('word span %.1f - %.1f' % (wf[0]['s'] if wf else 0, wf[-1]['e'] if wf else 0))
    starts = [447.17, 1260.0, 1967.56, 3259.41, 4087.51,
              5122.31, 6191.66, 7020.18, 8177.44, 9330.3]
    result = {}
    for day in range(1, 11):
        name = 'gt%02d' % day
        path = os.path.join(CONTENT, name + '.json')
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding='utf-8'))
        lo = starts[day-1]
        hi = starts[day] if day < 10 else 10406.0
        p2 = detect_part2(segs, lo, hi)
        # 各组起点：core/extra 在 Part1；dialogue 从 Part2 开始；plus 从 Part2 后段
        group_lo = {
            'core': lo,
            'extra': lo,
            'dialogue': p2 if p2 else lo + 90,
            'plus': (p2 + 60) if p2 else lo + 150,
        }
        items = []
        for group in ('core', 'dialogue', 'extra', 'plus'):
            last = group_lo[group] - 2.0
            for idx, x in enumerate(d.get(group, [])):
                m = match(x['it'], wf, max(lo, group_lo[group]-2), hi, after=last,
                          strict=(group == 'dialogue' and len(x['it'].split()) <= 3))
                if m:
                    items.append({'key': '%s.%s.%d' % (name, group, idx),
                                  'group': group, 'index': idx, 'it': x['it'],
                                  'start': m['start'], 'end': m['end'],
                                  'score': m['score'], 'matched': m['matched']})
                    last = m['end']
        total = sum(len(d.get(g, [])) for g in ('core','dialogue','extra','plus'))
        good = sum(1 for x in items if x['score'] >= 0.65)
        result[name] = {'window': [round(lo,2), round(hi,2)], 'part2': p2, 'items': items}
        print('%s p2=%s matched %d/%d (high %d)' %
              (name, round(p2,1) if p2 else None, len(items), total, good))
    json.dump(result, open(OUT,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
    print('WROTE', OUT, 'total', sum(len(v['items']) for v in result.values()))


if __name__ == '__main__':
    main()
