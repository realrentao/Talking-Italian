# -*- coding: utf-8 -*-
"""扫描所有已切片的首尾能量：判断是否存在切头/切尾风险。

切片时 PAD=0.06s，若首/尾 60ms 仍是强语音，说明边界太贴，需要额外外扩。
"""
import os, glob, struct, math, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
SR = 16000
WIN = int(SR * 0.05)  # 50ms


def db(seg):
    r = math.sqrt(sum(x * x for x in seg) / len(seg))
    return 20 * math.log10(r / 32768) if r > 0 else -99


def edges(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ar', str(SR),
                          '-ac', '1', '-f', 's16le', '-'], capture_output=True).stdout
    n = len(raw) // 2
    s = struct.unpack('<%dh' % n, raw[:n * 2])
    head = max(db(s[0:WIN]), db(s[WIN:2 * WIN]))
    tail = max(db(s[max(0, n - 2 * WIN):n - WIN]), db(s[max(0, n - WIN):n]))
    return head, tail, n / SR


files = sorted(glob.glob(os.path.join(SITE, 'audio', 'get', 'gt*', '*.mp3')))
risky = []
for p in files:
    h, t, dur = edges(p)
    rel = os.path.relpath(p, SITE).replace('\\', '/')
    if h > -32 or t > -32:
        risky.append((rel, h, t, dur))
print('切片总数', len(files), '边界风险', len(risky))
for rel, h, t, dur in risky:
    print('%s  %5.2fs  head=%5.1f  tail=%5.1f' % (rel, dur, h, t))
