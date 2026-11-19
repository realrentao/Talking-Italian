# -*- coding: utf-8 -*-
"""审计 audio_map_v3 中缺失的教材条目，在已有词级转写里找最佳候选。

输出每条缺失句的最佳匹配分数/时间，用于区分：
- 词流里有（对齐阈值漏掉）-> 可直接补入
- 词流里没有 -> 需要定向转写
"""
import json, os, collections
import align_audio_v2 as A

ROOT = os.path.dirname(os.path.abspath(__file__))
START = [447.17, 1260.0, 1967.56, 3259.41, 4087.51,
         5122.31, 6191.66, 7020.18, 8177.44, 9330.3]

wf, segs = A.load_words()
m = json.load(open(os.path.join(ROOT, 'audio_map_v3.json'), encoding='utf-8'))
matched = {it['key'] for info in m.values() for it in info['items']}

rows = []
for day in range(1, 11):
    name = 'gt%02d' % day
    path = os.path.join(ROOT, 'content', name + '.json')
    if not os.path.exists(path):
        continue
    d = json.load(open(path, encoding='utf-8'))
    lo = START[day - 1]
    hi = START[day] if day < 10 else 10406.0
    for group in ('core', 'dialogue', 'extra', 'plus'):
        for idx, x in enumerate(d.get(group, [])):
            key = '%s.%s.%d' % (name, group, idx)
            if key in matched:
                continue
            best = A.match(x['it'], wf, lo, hi, after=0.0)
            sc = best['score'] if best else 0.0
            rows.append({'key': key, 'it': x['it'], 'score': sc,
                         'start': best['start'] if best else None,
                         'end': best['end'] if best else None,
                         'matched': best['matched'] if best else ''})

rows.sort(key=lambda r: -r['score'])
with open(os.path.join(ROOT, 'audit_missing.tsv'), 'w', encoding='utf-8') as f:
    f.write('key\tit\tscore\tstart\tend\tmatched\n')
    for r in rows:
        f.write('%s\t%s\t%.3f\t%s\t%s\t%s\n' %
                (r['key'], r['it'], r['score'], r['start'], r['end'], r['matched']))

buckets = collections.Counter()
for r in rows:
    s = r['score']
    buckets['>=0.75' if s >= 0.75 else '0.6-0.75' if s >= 0.6
            else '0.45-0.6' if s >= 0.45 else '<0.45'] += 1
print('缺失总数', len(rows))
print('词流候选分布', dict(buckets))
print('\n=== 高置信可直接补入 (>=0.6) ===')
for r in rows:
    if r['score'] >= 0.6:
        print('%-14s %.3f %7.2f-%7.2f %-28s | %s' %
              (r['key'], r['score'], r['start'], r['end'], r['it'][:28], r['matched'][:45]))
print('\n=== 0.45-0.6 需人工看 ===')
for r in rows:
    if 0.45 <= r['score'] < 0.6:
        print('%-14s %.3f %7.2f-%7.2f %-28s | %s' %
              (r['key'], r['score'], r['start'], r['end'], r['it'][:28], r['matched'][:45]))
