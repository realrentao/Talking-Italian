# -*- coding: utf-8 -*-
"""从 Glossika Italian Fluency 1/2/3 PDF 提取 EN/IT/IPA 句子块。

正文排版：每句 EN 行、IT 行、IPA 行，句间夹句子编号行，页脚 "NN ENIT"。
"""
import os, re, json, sys
from pypdf import PdfReader

BASE = r'D:/Glossika Italian Fluency'
BOOKS = [1, 2, 3]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'glossika')
os.makedirs(OUT, exist_ok=True)


def clean_line(s):
    return re.sub(r'\s+', ' ', s).strip()


def is_noise(line):
    l = clean_line(line)
    if not l:
        return True
    # 页脚 NN ENIT / ENIT NN
    if re.fullmatch(r'\d{1,3}\s*ENIT', l) or re.fullmatch(r'ENIT\s*\d{1,3}', l):
        return True
    # 重复数字行（句子编号，如 8989 9090 9292）
    toks = l.split()
    if toks and all(re.fullmatch(r'\d{2,4}\d?', t) for t in toks):
        return True
    return False


def extract(book):
    fn = next(f for f in os.listdir(BASE) if f.endswith('.pdf') and ('Fluency %d ' % book) in f)
    reader = PdfReader(os.path.join(BASE, fn))
    records = []
    page_first_last = []
    for pi, page in enumerate(reader.pages):
        raw = page.extract_text() or ''
        lines = raw.split('\n')
        cur = None
        for line in lines:
            if is_noise(line):
                continue
            l = clean_line(line)
            m = re.match(r'^(EN|IT|IPA)\s+(.*)$', l)
            if m:
                tag, txt = m.group(1), m.group(2).strip()
                if tag == 'EN':
                    if cur:
                        records.append(cur)
                    cur = {'en': txt, 'it': '', 'ipa': '', 'page': pi + 1}
                elif cur:
                    cur[tag.lower()] = (cur[tag.lower()] + ' ' + txt).strip() if cur[tag.lower()] else txt
            else:
                # 续行：拼到当前最后一个字段
                if cur and l:
                    # 判断续行属于哪个字段：IT 未填满就补 IT？实际按出现顺序 EN->IT->IPA
                    if not cur['it']:
                        cur['en'] += ' ' + l
                    elif not cur['ipa']:
                        cur['it'] += ' ' + l
                    else:
                        cur['ipa'] += ' ' + l
        if cur:
            records.append(cur)
    # 过滤无效
    valid = [r for r in records if r['en'] and r['it']]
    json.dump(valid, open(os.path.join(OUT, 'book%d.json' % book), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('book%d pages=%d records=%d valid=%d' % (book, len(reader.pages), len(records), len(valid)))
    if valid:
        print('  first', valid[0])
        print('  last ', valid[-1])
    return valid


if __name__ == '__main__':
    total = 0
    for b in BOOKS:
        total += len(extract(b))
    print('TOTAL', total)
