# -*- coding: utf-8 -*-
"""探测 plus 组四句的真实语音边界（波形能量，20ms 窗）"""
import struct, math, subprocess

MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
SR = 16000
STEP = int(SR * 0.02)  # 20ms


def curve(lo, hi):
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


TARGETS = [
    ('plus.3  È abbastanza lontano.', 1091.8, 1095.2),
    ('plus.4  Quanto ci vuole?',      1097.8, 1100.2),
    ('plus.6  Dieci minuti in macchina.', 1108.8, 1112.6),
    ('plus.7  È troppo lontano a piedi.', 1114.0, 1119.4),
]

for name, lo, hi in TARGETS:
    print('=== %s  (%.2f-%.2f) ===' % (name, lo, hi))
    for t, db in curve(lo, hi):
        if db > -48:
            print('  %7.3f %6.1fdB %s' % (t, db, '#' * max(0, int(db + 50))))
    print()
