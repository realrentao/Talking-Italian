# -*- coding: utf-8 -*-
"""应用复核通过的起点前移（verified_starts.json），并做同组相邻重叠检查。"""
import json

MAP = 'audio_map_v3.json'
m = json.load(open(MAP, encoding='utf-8'))
verified = json.load(open('verified_starts.json', encoding='utf-8'))
idx = {it['key']: it for info in m.values() for it in info['items']}

n = 0
for k, ns in verified.items():
    it = idx[k]
    old = it['start']
    if ns >= old:
        continue
    it['orig_start'] = old
    it['start'] = ns
    n += 1
    print('SHIFT %-14s %.3f -> %.3f  %s' % (k, old, ns, it['it'][:40]))

json.dump(m, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('前移', n, '条')

# 重叠检查：同 day 同 group 相邻 index 是否存在 end > next.start
bad = 0
for day, info in m.items():
    groups = {}
    for it in info['items']:
        groups.setdefault(it['group'], []).append(it)
    for g, items in groups.items():
        items.sort(key=lambda x: x['index'])
        for a, b in zip(items, items[1:]):
            ov = a['end'] - b['start']
            if ov > 0.05:
                print('OVERLAP %s.%s %d end=%.2f > %d start=%.2f (%.2fs)' %
                      (day, g, a['index'], a['end'], b['index'], b['start'], ov))
                bad += 1
print('重叠', bad, '处')
