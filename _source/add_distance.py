# -*- coding: utf-8 -*-
"""补入 gt01.plus.3/4/6/7 四句配音（波形真实边界），并切片验证。"""
import json, os, subprocess, struct, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, '_source', 'audio_map_v3.json')
MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'

# key -> (it文本, start, end)  波形校正后边界
new = {
    'gt01.plus.3': ('È abbastanza lontano.', 1092.42, 1094.56),
    'gt01.plus.4': ('Quanto ci vuole?', 1098.28, 1099.54),
    'gt01.plus.6': ('Dieci minuti in macchina.', 1109.48, 1111.88),
    'gt01.plus.7': ('È troppo lontano a piedi.', 1116.18, 1118.60),
}

m = json.load(open(MAP, encoding='utf-8'))
gt01 = m['gt01']
for key, (it, start, end) in new.items():
    idx = int(key.rsplit('.', 1)[1])
    item = {'key': key, 'group': 'plus', 'index': idx, 'it': it,
            'start': start, 'end': end,
            'score': 1.0, 'matched': 'directed-transcribe-waveform'}
    found = False
    for i, x in enumerate(gt01['items']):
        if x['key'] == key:
            gt01['items'][i] = item
            found = True
            break
    if not found:
        gt01['items'].append(item)
    print('%-14s %-30s %.2f-%.2f' % (key, it, start, end))

json.dump(m, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# 切片
for key, (it, start, end) in new.items():
    idx = int(key.rsplit('.', 1)[1])
    out = os.path.join(ROOT, 'site', 'audio', 'get', 'gt01', 'plus_%d.mp3' % idx)
    s = start - 0.06
    dur = end - start + 0.12
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '%.3f' % s,
                    '-t', '%.3f' % dur, '-i', MP3,
                    '-ar', '22050', '-ac', '1', '-b:a', '64k', '-c:a', 'libmp3lame', out],
                   check=True)

# 验证首尾能量
print('\n=== 切片首尾能量验证 ===')
SR = 16000
STEP = int(SR * 0.05)
for key, (it, start, end) in new.items():
    idx = int(key.rsplit('.', 1)[1])
    p = os.path.join(ROOT, 'site', 'audio', 'get', 'gt01', 'plus_%d.mp3' % idx)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ar', str(SR),
                          '-ac', '1', '-f', 's16le', '-'], capture_output=True).stdout
    n = len(raw) // 2
    smp = struct.unpack('<%dh' % n, raw[:n * 2])
    def rms_db(i):
        seg = smp[i:i + STEP]
        r = math.sqrt(sum(x * x for x in seg) / len(seg))
        return 20 * math.log10(r / 32768) if r > 0 else -99
    head = max(rms_db(0), rms_db(STEP), rms_db(2 * STEP))
    tail = max(rms_db(n - 3 * STEP), rms_db(n - 2 * STEP), rms_db(n - STEP))
    print('%-14s %5.2fs  head=%5.1fdB  tail=%5.1fdB  %dB' % (
        key, n / SR, head, tail, os.path.getsize(p)))

print('\ngt01 items:', len(gt01['items']))
