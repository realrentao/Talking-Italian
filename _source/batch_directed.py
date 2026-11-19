# -*- coding: utf-8 -*-
"""批量定向转写：把 Day1 的 initial_prompt + 短窗 + beam5 + 波形校正流程推广到全部单元。

用法（worker 必须用系统 python，因为 faster_whisper 只装在那里）：
  D:/Python/python.exe batch_directed.py prepare
  D:/Python/python.exe batch_directed.py run            # 断点续跑
  C:/Users/.../python.exe batch_directed.py apply       # 纯 stdlib
"""
import json, os, subprocess, sys, glob, time, re

ROOT = os.path.dirname(os.path.abspath(__file__))
BATCH = os.path.join(ROOT, 'batch_directed')
MAP = os.path.join(ROOT, 'audio_map_v3.json')
MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
MODEL = os.path.join(ROOT, 'models', 'tiny')
SYSPY = r'D:/Python/python.exe'
START = [447.17, 1260.0, 1967.56, 3259.41, 4087.51,
         5122.31, 6191.66, 7020.18, 8177.44, 9330.3]
CHUNK = 150.0
OVERLAP = 12.0


def day_window(day):
    n = int(day[2:])
    return START[n - 1], (START[n] if n < 10 else 10406.0)


def missing_by_day():
    import collections
    m = json.load(open(MAP, encoding='utf-8'))
    have = {it['key'] for info in m.values() for it in info['items']}
    rows = []
    with open(os.path.join(ROOT, 'audit_missing.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            k, it, sc, s, e, mt = line.rstrip('\n').split('\t')
            rows.append((k, it, float(sc)))
    rem = collections.defaultdict(list)
    for k, it, sc in rows:
        if sc < 0.6 and k not in have:
            rem[k[:4]].append({'key': k, 'it': it})
    return dict(rem)


def prepare():
    os.makedirs(BATCH, exist_ok=True)
    rem = missing_by_day()
    tasks = []
    for day, items in sorted(rem.items()):
        lo, hi = day_window(day)
        prompt = 'Esercizio di italiano. ' + ' '.join(x['it'] for x in items)
        with open(os.path.join(BATCH, day + '_prompt.txt'), 'w', encoding='utf-8') as f:
            f.write(prompt)
        json.dump(items, open(os.path.join(BATCH, day + '_missing.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        t = lo
        ci = 0
        while t < hi:
            ce = min(t + CHUNK, hi)
            tasks.append({'day': day, 'ci': ci, 'lo': round(t, 3), 'hi': round(ce, 3)})
            if ce >= hi:
                break
            t = ce - OVERLAP
            ci += 1
        print(day, 'missing', len(items), 'chunks', ci + 1)
    json.dump(tasks, open(os.path.join(BATCH, 'tasks.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('TOTAL TASKS', len(tasks))


def worker(day, ci):
    from faster_whisper import WhisperModel
    tasks = json.load(open(os.path.join(BATCH, 'tasks.json'), encoding='utf-8'))
    task = next(x for x in tasks if x['day'] == day and x['ci'] == int(ci))
    lo, hi = task['lo'], task['hi']
    prompt = open(os.path.join(BATCH, day + '_prompt.txt'), encoding='utf-8').read()
    wav = os.path.join(BATCH, '_wav_%s_%02d.wav' % (day, int(ci)))
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '%.3f' % lo, '-t', '%.3f' % (hi - lo),
                    '-i', MP3, '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', wav], check=True)
    model = WhisperModel(MODEL, device='cpu', compute_type='int8',
                         cpu_threads=1, num_workers=1)
    segs, _ = model.transcribe(
        wav, language='it', initial_prompt=prompt, beam_size=5,
        vad_filter=False, word_timestamps=True, condition_on_previous_text=False)
    out = []
    for s in segs:
        words = []
        for w in (s.words or []):
            if w.start is None or w.end is None:
                continue
            words.append({'w': w.word, 's': round(lo + w.start, 3), 'e': round(lo + w.end, 3)})
        out.append({'start': round(lo + s.start, 3), 'end': round(lo + s.end, 3),
                    'text': s.text.strip(), 'words': words})
    with open(os.path.join(BATCH, '%s_%02d.json' % (day, int(ci))), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    if os.path.exists(wav):
        os.remove(wav)
    print('%s_%02d %.0f-%.0f segs=%d' % (day, int(ci), lo, hi, len(out)), flush=True)


def run():
    tasks = json.load(open(os.path.join(BATCH, 'tasks.json'), encoding='utf-8'))
    skip = int(os.environ.get('SKIP', '0'))
    for i, t in enumerate(tasks):
        out = os.path.join(BATCH, '%s_%02d.json' % (t['day'], t['ci']))
        if os.path.exists(out) or i < skip:
            continue
        cmd = [SYSPY, os.path.abspath(__file__), 'worker', t['day'], str(t['ci'])]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           env=dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
        msg = (r.stdout.strip() or r.stderr.strip()[-200:]).replace('\n', ' ')[:160]
        print('[%d/%d] %s' % (i + 1, len(tasks), msg), flush=True)


def apply():
    import align_audio_v2 as A
    import refine_boundaries as R
    wf = []
    for f in sorted(glob.glob(os.path.join(BATCH, 'gt*_*.json'))):
        if not re.search(r'gt\d+_\d+\.json$', f):
            continue
        for seg in json.load(open(f, encoding='utf-8')):
            for w in seg['words']:
                t = A.fixword(A.norm(w['w']))
                if not t:
                    continue
                wf.append({'w': t, 's': w['s'], 'e': w['e']})
    wf.sort(key=lambda x: x['s'])
    uniq = []
    for w in wf:
        if uniq and abs(w['s'] - uniq[-1]['s']) < 0.10 and w['w'] == uniq[-1]['w']:
            continue
        uniq.append(w)
    print('定向转写词数', len(uniq))

    m = json.load(open(MAP, encoding='utf-8'))
    have = {it['key'] for info in m.values() for it in info['items']}
    added = 0
    for day, items in sorted(missing_by_day().items()):
        lo, hi = day_window(day)
        for x in items:
            if x['key'] in have:
                continue
            nw = len(x['it'].split())
            best = A.match(x['it'], uniq, lo, hi, after=0.0, strict=nw <= 3)
            if not best:
                continue
            need = 0.9 if nw <= 2 else 0.62
            if best['score'] < need:
                continue
            s0, e0 = best['start'], best['end']
            ns, ne = R.refine_start(s0, e0), R.refine_end(s0, e0)
            if ns >= e0 - 0.05 or ne <= s0 + 0.05 or (ne - ns) > (e0 - s0) + 1.2:
                ns, ne = s0, e0
            group = x['key'].split('.')[1]
            idx = int(x['key'].rsplit('.', 1)[1])
            item = {'key': x['key'], 'group': group, 'index': idx, 'it': x['it'],
                    'start': round(ns, 3), 'end': round(ne, 3),
                    'orig_start': s0, 'orig_end': e0,
                    'score': best['score'], 'matched': best['matched'],
                    'source': 'directed-transcribe-waveform'}
            m[day]['items'].append(item)
            have.add(x['key'])
            added += 1
            print('%-14s %.3f %7.2f-%7.2f  %-30s | %s' %
                  (x['key'], best['score'], ns, ne, x['it'][:30], best['matched'][:40]))
    for info in m.values():
        info['items'].sort(key=lambda z: (z['group'], z['index']))
    json.dump(m, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('定向补入', added, '条；总条目', sum(len(v['items']) for v in m.values()))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'prepare':
        prepare()
    elif cmd == 'worker':
        worker(sys.argv[2], sys.argv[3])
    elif cmd == 'run':
        run()
    elif cmd == 'apply':
        apply()
