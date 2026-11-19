# -*- coding: utf-8 -*-
"""探测三句 extra 的真实语音边界（20ms 能量曲线）。"""
import struct, math, subprocess

MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
SR = 16000
STEP = 320

probes = [
    ('stazione 1st', 947.6, 951.2),
    ('aeroporto 1st', 958.6, 961.8),
    ('museo 1st', 968.3, 972.9),
]
for name, lo, hi in probes:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '%.3f' % lo,
                          '-t', '%.3f' % (hi - lo), '-i', MP3,
                          '-ar', str(SR), '-ac', '1', '-f', 's16le', '-'],
                         capture_output=True).stdout
    n = len(raw) // 2
    s = struct.unpack('<%dh' % n, raw[:n * 2])
    print('=== %s ===' % name)
    for i in range(0, n - STEP, STEP):
        seg = s[i:i + STEP]
        rms = math.sqrt(sum(x * x for x in seg) / STEP)
        db = 20 * math.log10(rms / 32768) if rms > 0 else -99
        t = lo + i / SR
        if db > -45:
            print('  %7.3f %6.1fdB' % (t, db))
