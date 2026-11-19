# -*- coding: utf-8 -*-
"""把中文翻译回填到课程数据，生成站点每册 JS 数据文件。"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_source', 'glossika')
OUT = os.path.join(ROOT, 'glossika', 'data')
os.makedirs(OUT, exist_ok=True)

lessons = json.load(open(os.path.join(SRC, 'lessons.json'), encoding='utf-8'))
tpath = os.path.join(SRC, 'translations.json')
trans = json.load(open(tpath, encoding='utf-8')) if os.path.exists(tpath) else {}

for b in (1, 2, 3):
    ls = []
    for L in lessons:
        if L['book'] != b:
            continue
        items = []
        for it in L['items']:
            items.append({'n': it['n'], 'zh': trans.get(str(it['gid']), ''),
                          'en': it['en'], 'it': it['it'], 'ipa': it['ipa']})
        ls.append({'lesson': L['lesson'], 'range': L['range'], 'items': items})
    data = {'book': b, 'lessons': ls}
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(OUT, 'book%d.js' % b), 'w', encoding='utf-8') as f:
        f.write('window.GLOSSIKA_B%d = %s;\n' % (b, payload))
    filled = sum(1 for L in ls for x in L['items'] if x['zh'])
    total = sum(len(L['items']) for L in ls)
    print('book%d.js lessons=%d zh=%d/%d size=%dKB' %
          (b, len(ls), filled, total, os.path.getsize(os.path.join(OUT, 'book%d.js' % b)) // 1024))
