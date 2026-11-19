# -*- coding: utf-8 -*-
"""把 audit_missing.tsv 中高置信候选补入 audio_map_v3.json，并做波形边界校正。"""
import json, os
import refine_boundaries as R

ROOT = os.path.dirname(os.path.abspath(__file__))
MAP = os.path.join(ROOT, 'audio_map_v3.json')
TSV = os.path.join(ROOT, 'audit_missing.tsv')
THR = float(os.environ.get('THR', '0.6'))

rows = []
with open(TSV, encoding='utf-8') as f:
    next(f)
    for line in f:
        key, it, score, start, end, matched = line.rstrip('\n').split('\t')
        sc = float(score)
        if sc >= THR and start and end:
            rows.append((key, it, sc, float(start), float(end), matched))

m = json.load(open(MAP, encoding='utf-8'))
existing = {it['key']: it for info in m.values() for it in info['items']}

added, fixed = 0, 0
for key, it, sc, s0, e0, matched in rows:
    if key in existing:
        continue
    day = key.split('.')[0]
    group = key.split('.')[1]
    idx = int(key.rsplit('.', 1)[1])
    ns = R.refine_start(s0, e0)
    ne = R.refine_end(s0, e0)
    # 校正后若跨度异常（吞进下一句），退回词级原边界
    if ns >= e0 - 0.05 or ne <= s0 + 0.05 or (ne - ns) > (e0 - s0) + 1.2:
        ns, ne = s0, e0
    else:
        fixed += 1
    item = {'key': key, 'group': group, 'index': idx, 'it': it,
            'start': round(ns, 3), 'end': round(ne, 3),
            'orig_start': s0, 'orig_end': e0,
            'score': sc, 'matched': matched, 'source': 'wordstream-recover'}
    m[day]['items'].append(item)
    existing[key] = item
    added += 1
    print('%-14s %.3f %7.2f-%7.2f -> %7.2f-%7.2f  %s' %
          (key, sc, s0, e0, ns, ne, it[:32]))

# 按 group/index 排序，便于阅读与切片
for info in m.values():
    info['items'].sort(key=lambda x: (x['group'], x['index']))

json.dump(m, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n补入', added, '条，其中波形校正', fixed, '条 ->', MAP)
print('总条目', sum(len(v['items']) for v in m.values()))
