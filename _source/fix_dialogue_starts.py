"""把 5 句对话起点吸附到波形真实起音点（修复短词切头）。"""
import json

MAP = '_source/audio_map_v3.json'
# key -> (new_start, new_end or None)
fixes = {
    'gt01.dialogue.1': (549.02, None),
    'gt01.dialogue.2': (555.22, None),
    'gt01.dialogue.3': (556.94, 558.00),   # 起音前移 + 尾部微延（"Pace" 到 557.98）
    'gt01.dialogue.5': (562.13, None),
    'gt01.dialogue.6': (564.78, None),
}

m = json.load(open(MAP, encoding='utf-8'))
changed = 0
for info in m.values():
    for it in info['items']:
        if it['key'] in fixes:
            ns, ne = fixes[it['key']]
            old = (it['start'], it['end'])
            it['start'] = ns
            if ne is not None:
                it['end'] = ne
            it['orig_start'], it['orig_end'] = old
            print('%s  %.2f-%.2f -> %.2f-%.2f  | %s' % (
                it['key'], old[0], old[1], it['start'], it['end'], it['it'][:30]))
            changed += 1
json.dump(m, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('修改条数:', changed)

# 重叠检查
items = sorted([x for x in m['gt01']['items'] if x['group'] == 'dialogue'],
               key=lambda x: x['index'])
bad = 0
for a, b in zip(items, items[1:]):
    ov = a['end'] - b['start']
    if ov > 0.05:
        print('OVERLAP', a['index'], 'end', round(a['end'], 2), '>',
              b['index'], 'start', round(b['start'], 2), '%.2f' % ov)
        bad += 1
print('重叠数:', bad)
