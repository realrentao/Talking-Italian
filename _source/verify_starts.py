# -*- coding: utf-8 -*-
"""复核 check_all_starts 报出的切头风险：扩大前视窗，确认跳变是本句真实起音，
而不是前一句残响/检测窗边界误判。输出可安全前移的 start 值。
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


def jump_before(s, lookback):
    """在 [s-lookback, s] 内找最近的 静音->语音 跳变（d1<-38,d2>-32）。"""
    curve = energy(s - lookback, s + 0.02)
    jump = None
    for (t1, d1), (t2, d2) in zip(curve, curve[1:]):
        if t2 > s:
            break
        if d1 < -38 and d2 > -32:
            jump = t2
    return jump


m = json.load(open('audio_map_v3.json', encoding='utf-8'))
idx = {it['key']: it for info in m.values() for it in info['items']}
risky = []
for line in open('scan_starts_log.txt', encoding='utf-8'):
    parts = line.split()
    if parts and parts[0].startswith('gt') and 'start=' in line and len(parts[0].split('.')) == 3:
        risky.append(parts[0])

verified = []
for k in risky:
    it = idx[k]
    s = it['start']
    j055 = jump_before(s, 0.55)
    j120 = jump_before(s, 1.20)
    if j055 is None:
        continue
    # 稳定性：扩大窗口后跳变点不应明显前移（差值 < 0.06s）
    stable = j120 is not None and abs(j120 - j055) < 0.06
    back = s - j055
    # 前移幅度封顶 0.55s，且必须稳定
    if stable and 0.12 <= back <= 0.55:
        verified.append((k, s, round(j055, 3), round(back, 3), it['it']))
        print('OK   %-14s %.3f -> %.3f (前移 %.3f)  %s' % (k, s, j055, back, it['it'][:40]))
    else:
        print('SKIP %-14s %.3f  j055=%s j120=%s stable=%s back=%.3f  %s' %
              (k, s, j055, j120, stable, back, it['it'][:40]))

json.dump({k: j for k, s, j, back, t in verified},
          open('verified_starts.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n可安全前移', len(verified), '/', len(risky))
