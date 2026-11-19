# -*- coding: utf-8 -*-
"""精修 gt01.dialogue.7 尾部：euro 被切。end 574.98 -> 575.62（定向转写 euro=575.06-575.54）。"""
import json, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, '_source', 'audio_map_v3.json')
MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'

m = json.load(open(MAP, encoding='utf-8'))
item = None
for info in m.values():
    for it in info['items']:
        if it['key'] == 'gt01.dialogue.7':
            item = it
            break
assert item, 'not found'
old_end = item['end']
item['orig_end'] = old_end
item['end'] = 575.62
json.dump(m, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('dialogue.7 end %.2f -> %.2f | %s' % (old_end, item['end'], item['it']))

# 只重切这一条
out = os.path.join(ROOT, 'site', 'audio', 'get', 'gt01', 'dialogue_7.mp3')
start = item['start'] - 0.06
dur = item['end'] - start + 0.06
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '%.3f' % start,
                '-t', '%.3f' % dur, '-i', MP3,
                '-ar', '22050', '-ac', '1', '-b:a', '64k', '-c:a', 'libmp3lame', out],
               check=True)
print('resliced:', out, os.path.getsize(out), 'bytes')
