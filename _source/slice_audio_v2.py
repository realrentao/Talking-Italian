# -*- coding: utf-8 -*-
"""按 v2 词级精确边界从原 MP3 切出意大利语配音片段。"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ROOT)
MP3 = sys.argv[1] if len(sys.argv) > 1 else 'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
MAP = os.path.join(ROOT, 'audio_map_v2.json')
OUTROOT = os.path.join(SITE, 'site', 'audio', 'get')
PAD = float(os.environ.get('PAD', '0.06'))  # 词边界已精确，仅留极小缓冲

data = json.load(open(MAP, encoding='utf-8'))
made, skipped, failed = 0, 0, 0
manifest = {}
for day, info in data.items():
    outdir = os.path.join(OUTROOT, day)
    os.makedirs(outdir, exist_ok=True)
    # 直接覆盖写入（ffmpeg -y），不做批量删除，避免触发安全拦截
    for it in info['items']:
        s, e = it['start'], it['end']
        dur = e - s
        if dur < 0.35 or dur > 16:
            skipped += 1
            continue
        name = '%s_%d.mp3' % (it['group'], it['index'])
        out = os.path.join(outdir, name)
        ss = max(0, s - PAD)
        length = dur + 2 * PAD
        cmd = ['ffmpeg', '-y', '-v', 'error', '-ss', '%.3f' % ss, '-t', '%.3f' % length,
               '-i', MP3, '-ar', '22050', '-ac', '1', '-b:a', '64k',
               '-c:a', 'libmp3lame', out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and os.path.getsize(out) > 600:
            made += 1
            manifest[it['key']] = 'audio/get/%s/%s' % (day, name)
        else:
            failed += 1
            if os.path.exists(out):
                os.remove(out)
            print('FAIL', it['key'], r.stderr[-120:])
    print('day', day, 'dir', outdir)

json.dump(manifest, open(os.path.join(ROOT, 'audio_manifest.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('made', made, 'skipped', skipped, 'failed', failed)
