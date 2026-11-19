# -*- coding: utf-8 -*-
"""用智谱 glm-4-flash 把 3000 句英文批量译成中文。

- 按固定批大小请求，输出用 [n] 编号，逐行对齐到原句
- 每批完成即写盘 translations.json，支持断点续传
- 失败自动重试，缺行批次可重跑
"""
import os, re, json, time, urllib.request, urllib.error, concurrent.futures

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, 'glossika')
ITEMS = json.load(open(os.path.join(DIR, 'all_items.json'), encoding='utf-8'))
OUT = os.path.join(DIR, 'translations.json')
KEY = os.environ.get('ZHIPUAI_API_KEY')
URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
MODEL = 'glm-4-flash'
BATCH = int(os.environ.get('BATCH', '20'))

translations = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}

SYS = ('你是意语学习教材的中文译者。把用户给出的英文句子逐条翻译成自然、简洁、口语化的简体中文，'
       '忠实原意、不要解释、不要加序号以外的任何内容。')
USER_TPL = ('逐条翻译下面 %d 条英文，每条译文前必须原样带上方括号编号，格式严格为：\n'
            '[编号] 译文\n'
            '不要漏条，不要合并，不要输出其它文字。\n\n%s')


def call_batch(batch):
    numbered = '\n'.join('[%d] %s' % (it['gid'], it['en']) for it in batch)
    data = {'model': MODEL, 'messages': [
        {'role': 'system', 'content': SYS},
        {'role': 'user', 'content': USER_TPL % (len(batch), numbered)}],
        'temperature': 0.1}
    for attempt in range(5):
        try:
            req = urllib.request.Request(
                URL, data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=90) as r:
                content = json.loads(r.read())['choices'][0]['message']['content']
            got = {}
            for line in content.split('\n'):
                m = re.match(r'^\s*\[(\d+)\]\s*(.*)$', line.strip())
                if m:
                    n = int(m.group(1))
                    txt = re.sub(r'^[\d.、)\s]+', '', m.group(2)).strip()
                    if txt:
                        got[n] = txt
            return got
        except Exception as e:
            if attempt == 4:
                print('FAIL batch', batch[0]['n'], '-', batch[-1]['n'], str(e)[:80], flush=True)
                return {}
            time.sleep(2 * (attempt + 1))


def main():
    # 校验 translations 使用的 key 必须是 gid；旧版按 n(册内号)存的会与 gid 冲突，全部丢弃重译
    valid = {str(it['gid']) for it in ITEMS}
    stale = [k for k in translations if k not in valid]
    if stale or os.environ.get('RESET') == '1':
        print('reset stale translations', len(stale), 'total', len(translations), flush=True)
        translations.clear()
    batches = [ITEMS[i:i + BATCH] for i in range(0, len(ITEMS), BATCH)]
    done = 0
    for bi, batch in enumerate(batches):
        need = [it for it in batch if str(it['gid']) not in translations]
        if not need:
            continue
        got = call_batch(need)
        for n, txt in got.items():
            translations[str(n)] = txt
        valid_gids = {str(it['gid']) for it in need}
        for k in [str(n) for n in got]:
            if k not in valid_gids:
                del translations[k]
        done += 1
        json.dump(translations, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        if done % 10 == 0 or bi == len(batches) - 1:
            print('batches %d/%d  translated %d/%d' %
                  (bi + 1, len(batches), len(translations), len(ITEMS)), flush=True)
    missing = [it['gid'] for it in ITEMS if str(it['gid']) not in translations]
    print('DONE translated', len(translations), 'missing', len(missing), missing[:40])


if __name__ == '__main__':
    main()
