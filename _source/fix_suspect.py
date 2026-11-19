# -*- coding: utf-8 -*-
"""清理定向补入中的错配/零时长条目，修复可确认的切词边界。
原则：内容对不上（tiny 转写把别的句子误认成目标句）一律删除回退 TTS；
      只有波形+转写段双重确认的切词才延长边界。
"""
import json

MAP = 'audio_map_v3.json'
m = json.load(open(MAP, encoding='utf-8'))
idx = {it['key']: (info, it) for info in m.values() for it in info['items']}

# 内容错配或零时长 -> 删除（回退 TTS）
DROP = [
    'gt02.plus.5',   # 零时长；转写段文本混乱不可靠
    'gt03.plus.1',   # ogni dieci minuti 被配成 ogni 5 minuti
    'gt04.extra.2',  # con bagno 被配成 con doccia 且切尾
    'gt06.dialogue.2',  # Ah,sì,Lassey 只剩 ah si，Lassey 归属不明
    'gt06.extra.0',  # 转写段内容混乱，无法确认
    'gt07.extra.7',  # jeans 被配成 scarpe
    'gt08.extra.1',  # A che ora chiude? 被配成 visita guidata
    'gt10.plus.4',   # 零时长；转写未识别到 prurito
]

# 双重确认的切词 -> 修边界
FIX = {
    'gt05.extra.2': (4788.69, None),  # 切掉首词 Una，转写段起点 4788.69
    'gt09.plus.7': (None, 9273.50),   # 切掉尾部 deluso，转写段终点 9273.50
}

import refine_boundaries as R

for k in DROP:
    info, it = idx[k]
    info['items'].remove(it)
    print('DROP ', k, it['it'])

for k, (s, e) in FIX.items():
    info, it = idx[k]
    old = (it['start'], it['end'])
    if s is not None:
        it['start'] = R.refine_start(s, it['end'])
    if e is not None:
        it['end'] = R.refine_end(it['start'], e)
    it.setdefault('orig_start', old[0])
    it.setdefault('orig_end', old[1])
    print('FIX  ', k, '%.2f-%.2f -> %.2f-%.2f' % (old[0], old[1], it['start'], it['end']))

json.dump(m, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('最终条目', sum(len(v['items']) for v in m.values()))
