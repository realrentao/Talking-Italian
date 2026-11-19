"""检查所有 dialogue 句的起点是否落在语音块中间（前面紧邻语音 → 可能被切头）。"""
import json, struct, math, subprocess

MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
SR = 16000
STEP = int(SR * 0.02)  # 20ms


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


m = json.load(open('_source/audio_map_v3.json', encoding='utf-8'))
items = sorted([x for x in m['gt01']['items'] if x['group'] == 'dialogue'],
               key=lambda x: x['index'])

print('idx | 文本 | 当前start | start前0.3s能量分布（是否有更早起音）')
for it in items:
    s = it['start']
    curve = energy(s - 0.35, s + 0.05)
    # 起点前紧邻的窗口（s-0.1 ~ s）若已经是强语音，说明可能切头
    pre = [(t, db) for t, db in curve if s - 0.10 <= t < s]
    pre_loud = [db for t, db in pre if db > -35]
    # 找 s 之前最近的静音→语音跳变
    jump = None
    for (t1, d1), (t2, d2) in zip(curve, curve[1:]):
        if t2 > s: break
        if d1 < -38 and d2 > -32:
            jump = t2
    flag = ''
    if pre_loud:
        flag = '  <== 起点前已是语音，可能切头'
    print('%2d | %-22s | %7.3f | 最近静音→语音 %s%s' % (
        it['index'], it['it'][:22], s,
        ('%.3f' % jump) if jump else '无', flag))
