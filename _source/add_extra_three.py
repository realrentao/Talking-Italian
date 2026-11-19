# -*- coding: utf-8 -*-
"""补入 gt01.extra.0/1/2 三句配音（波形真实边界），并切片。"""
import json, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, '_source', 'audio_map_v3.json')
MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'

# key -> (it文本, start, end)  波形校正后边界
new = {
    'gt01.extra.0': ('Alla stazione, per favore.', 947.80, 949.94),
    'gt01.extra.1': ('All’aeroporto, per favore.', 958.76, 961.04),
    'gt01.extra.2': ('Al museo, per favore.', 969.84, 971.84),
}

m = json.load(open(MAP, encoding='utf-8'))
gt01 = m['gt01']
existing = {x['key'] for x in gt01['items']}
for key, (it, start, end) in new.items():
    if key in existing or key == 'gt01.extra.3':
        pass
    item = {'key': key, 'group': 'extra',
            'index': int(key.rsplit('.', 1)[1]), 'it': it,
            'start': start, 'end': end,
            'score': 1.0, 'matched': 'directed-transcribe-waveform'}
    # 若已存在则替换
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

# 切片三句
for key, (it, start, end) in new.items():
    idx = int(key.rsplit('.', 1)[1])
    out = os.path.join(ROOT, 'site', 'audio', 'get', 'gt01', 'extra_%d.mp3' % idx)
    s = start - 0.06
    dur = end - start + 0.12
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '%.3f' % s,
                    '-t', '%.3f' % dur, '-i', MP3,
                    '-ar', '22050', '-ac', '1', '-b:a', '64k', '-c:a', 'libmp3lame', out],
                   check=True)
    print('sliced extra_%d.mp3 %d bytes' % (idx, os.path.getsize(out)))
print('gt01 items:', len(gt01['items']))
