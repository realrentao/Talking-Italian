# -*- coding: utf-8 -*-
"""把 gt01 情景对话 10 句写入 audio_map_v3.json（dialogue 组），
边界经波形能量二次校正，避免短词切头。"""
import json, os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import refine_boundaries as RB

MAP = os.path.join(ROOT, 'audio_map_v3.json')

# 从定向转写拿到的词级原始边界
RAW = [
    (0, 'Buongiorno.',                                  547.34, 548.48),
    (1, 'Buongiorno. Devo andare all’albergo Regina Margherita.', 549.34, 554.16),
    (2, 'In quale via?',                                555.32, 556.48),
    (3, 'In via Pace.',                                 557.18, 557.94),
    (4, 'A quale numero è l’albergo?',                  558.98, 561.60),
    (5, 'Al numero otto, credo.',                       562.28, 564.64),
    (6, 'Va bene, al numero otto di via Pace.',         564.88, 567.98),
    (7, 'Ecco l’albergo Regina Margherita. Sono €10.',  570.48, 574.98),
    (8, 'Bene, grazie. Ecco a lei.',                    576.54, 579.20),
    (9, 'Grazie, arrivederci.',                         580.18, 581.94),
]

data = json.load(open(MAP, encoding='utf-8'))
items = data['gt01']['items']
# 移除旧的 dialogue 条目（已有的错配一律替换）
items = [it for it in items if not (it['group'] == 'dialogue')]

added = []
for idx, it_text, s, e in RAW:
    ns = RB.refine_start(s, e)
    ne = RB.refine_end(s, e)
    item = dict(key='gt01.dialogue.%d' % idx, group='dialogue', index=idx,
                it=it_text, start=ns, end=ne, score=1.0, matched='directed-transcribe')
    items.append(item)
    added.append((idx, it_text[:28], s, e, ns, ne))

gorder = {'core': 0, 'dialogue': 1, 'extra': 2, 'plus': 3}
items.sort(key=lambda x: (gorder.get(x['group'], 9), x['index']))
data['gt01']['items'] = items
json.dump(data, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('=== dialogue 10 句（原始 -> 波形校正）===')
for idx, t, s, e, ns, ne in added:
    print('%d %-30s %7.2f-%7.2f -> %7.2f-%7.2f' % (idx, t, s, e, ns, ne))
print('gt01 TOTAL', len(items))
