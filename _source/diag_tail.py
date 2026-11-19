# -*- coding: utf-8 -*-
"""诊断可疑条目：打印 orig_end 之后波形的 20ms 能量曲线，判断尾词是否被切。"""
import json, struct, math, subprocess, glob, re, os

MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
SR = 16000
STEP = int(SR * 0.02)

WATCH = ['gt04.extra.2', 'gt05.extra.2', 'gt06.dialogue.2', 'gt06.extra.0',
         'gt07.extra.7', 'gt07.plus.0', 'gt08.extra.1', 'gt09.plus.7',
         'gt02.plus.5', 'gt10.plus.4', 'gt03.plus.1']


def energy(lo, hi):
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-ss', '%.3f' % lo, '-t', '%.3f' % (hi - lo),
         '-i', MP3, '-ar', str(SR), '-ac', '1', '-f', 's16le', '-'],
        capture_output=True).stdout
    n = len(raw) // 2
    smp = struct.unpack('<%dh' % n, raw[:n * 2])
    out = []
    for i in range(0, n - STEP, STEP):
        seg = smp[i:i + STEP]
        rms = math.sqrt(sum(x * x for x in seg) / STEP)
        db = 20 * math.log10(rms / 32768) if rms > 0 else -99
        out.append((lo + i / SR, db))
    return out


m = json.load(open('audio_map_v3.json', encoding='utf-8'))
d = {it['key']: it for info in m.values() for it in info['items']}

# 收集定向转写段，用于对照真实文本
segs = []
for f in glob.glob(os.path.join('batch_directed', 'gt*_*.json')):
    if not re.search(r'gt\d+_\d+\.json$', f):
        continue
    segs += json.load(open(f, encoding='utf-8'))
segs.sort(key=lambda s: s['start'])

for k in WATCH:
    it = d[k]
    e = it['end']
    print('\n=== %s  dur=%.2f  [%0.2f-%0.2f]  %s <=> %s' %
          (k, e - it['start'], it['start'], e, it['it'], it['matched']))
    # 落在 [start-0.5, end+2.0] 的转写段
    rel = [s for s in segs if s['end'] > it['start'] - 0.5 and s['start'] < e + 2.0]
    for s in rel[:6]:
        print('   SEG %7.2f-%7.2f %s' % (s['start'], s['end'], s['text'][:80]))
    # 尾部能量：从 end-0.3 到 end+1.8，每 0.02s 一个点，压缩成字符
    cur = energy(e - 0.3, e + 1.8)
    bar = ''.join('#' if db > -30 else ('+' if db > -42 else '.') for t, db in cur)
    print('   TAIL(e-0.3 .. e+1.8): %s' % bar)
