"""扫描所有 item 尾部：end 之后、下一同组句之前若有强语音块，说明尾词被切。"""
import json, struct, math, subprocess, collections

MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
SR = 16000
STEP = 320  # 20ms


def loud_runs(lo, hi, thr=-32.0):
    if hi - lo < 0.05:
        return []
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-ss', '%.3f' % lo, '-t', '%.3f' % (hi - lo),
         '-i', MP3, '-ar', str(SR), '-ac', '1', '-f', 's16le', '-'],
        capture_output=True).stdout
    n = len(raw) // 2
    s = struct.unpack('<%dh' % n, raw[:n * 2])
    runs = []
    cur = None
    for i in range(0, n - STEP, STEP):
        seg = s[i:i + STEP]
        rms = math.sqrt(sum(x * x for x in seg) / STEP)
        db = 20 * math.log10(rms / 32768) if rms > 0 else -99
        t = lo + i / SR
        if db > thr:
            if cur is None:
                cur = [t, t]
            else:
                cur[1] = t + 0.02
        else:
            if cur is not None and cur[1] - cur[0] >= 0.12:
                runs.append((cur[0], cur[1]))
            cur = None
    if cur is not None and cur[1] - cur[0] >= 0.12:
        runs.append((cur[0], cur[1]))
    return runs


m = json.load(open('_source/audio_map_v3.json', encoding='utf-8'))
for day, info in m.items():
    byg = collections.defaultdict(list)
    for it in info['items']:
        byg[it['group']].append(it)
    for g, items in byg.items():
        items.sort(key=lambda x: x['start'])
        for i, it in enumerate(items):
            end = it['end']
            # 下一同组句的起点，作为扫描上限（最多看 0.9s）
            nxt = items[i + 1]['start'] if i + 1 < len(items) else end + 0.9
            upper = min(nxt - 0.05, end + 0.9)
            runs = loud_runs(end + 0.02, upper)
            if runs:
                print('%s %s[%d] %-30s end=%.2f  尾部后续语音: %s' % (
                    day, g, it['index'], it['it'][:30], end,
                    ', '.join('%.2f-%.2f' % r for r in runs)))
print('扫描完成')
