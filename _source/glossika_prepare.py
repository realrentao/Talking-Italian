# -*- coding: utf-8 -*-
"""清理 Glossika 提取数据：去 IPA 尾号、切分为 30 课（每 100 句）。"""
import os, re, json

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, 'glossika')


def clean_ipa(s):
    # 去掉尾部混入的句子编号串（如 "…bɛlːo. 8989 9090" 或 "…domạni? 20012001"）
    s = re.sub(r'(?:\s+\d{3,})+[\s.]*$', '', s).strip()
    s = re.sub(r'\d{3,}', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def clean_en(s):
    return re.sub(r'\s+', ' ', s).strip()


def clean_it(s):
    return re.sub(r'\s+', ' ', s).strip()


lessons = []
for b in (1, 2, 3):
    data = json.load(open(os.path.join(DIR, 'book%d.json' % b), encoding='utf-8'))
    for i, r in enumerate(data):
        r['ipa'] = clean_ipa(r['ipa'])
        r['en'] = clean_en(r['en'])
        r['it'] = clean_it(r['it'])
    json.dump(data, open(os.path.join(DIR, 'book%d.json' % b), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    for k in range(10):  # 每册 10 课，每课 100 句
        seg = data[k * 100:(k + 1) * 100]
        lessons.append({
            'id': 'G%d-L%02d' % (b, k + 1),
            'book': b, 'lesson': k + 1,
            'title': '第 %d 课' % (k + 1),
            'range': [k * 100 + 1, (k + 1) * 100],
            'items': [{'n': k * 100 + j + 1, 'en': x['en'], 'it': x['it'],
                       'ipa': x['ipa'], 'page': x['page']} for j, x in enumerate(seg)]
        })

# 全局句库：gid 为 1-3000 全局唯一编号（注意 n 在三册内各自 1-1000 会重复！）
all_items = []
gid = 0
for L in lessons:
    for it in L['items']:
        gid += 1
        row = {'id': L['id'], **it}
        row['gid'] = gid
        all_items.append(row)
        it['gid'] = gid
json.dump(all_items, open(os.path.join(DIR, 'all_items.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump(lessons, open(os.path.join(DIR, 'lessons.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

bad = [x for x in all_items if not x['en'] or not x['it'] or re.search(r'\d{3,}', x['ipa'])]
print('课程数', len(lessons), '句子数', len(all_items), '异常', len(bad))
print('样例', all_items[0])
print('IPA 样例', all_items[0]['ipa'])
