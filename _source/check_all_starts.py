# -*- coding: utf-8 -*-
"""把 Day1 的起点切头检查推广到全部 10 天、全部分组。

判定：start 前 0.1s 已是强语音，且在此之前 0.12s 以上存在静音→语音跳变，
说明真实起音被切掉（而不是正常的紧邻对话）。
"""
import json, struct, math, subprocess

MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
SR = 16000
STEP = int(SR * 0.02)


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
items = sorted([x for info in m.values() for x in info['items']], key=lambda x: x['start'])
risky = []
for it in items:
    s = it['start']
    curve = energy(s - 0.55, s + 0.03)
    pre = [(t, db) for t, db in curve if s - 0.10 <= t < s]
    if not [db for t, db in pre if db > -35]:
        continue
    jump = None
    for (t1, d1), (t2, d2) in zip(curve, curve[1:]):
        if t2 > s:
            break
        if d1 < -38 and d2 > -32:
            jump = t2
    if jump is not None and s - jump >= 0.12:
        risky.append((it['key'], it['it'], s, jump))

print('检查条目', len(items), '切头风险', len(risky))
for key, text, s, jump in risky:
    print('%-14s start=%8.3f 真实起音约=%8.3f 差=%+.3f  %s' %
          (key, s, jump, jump - s, text[:42]))
