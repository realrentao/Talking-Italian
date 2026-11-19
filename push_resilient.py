# -*- coding: utf-8 -*-
"""稳健版推送：断点续传 blob、全局 socket 超时、进度落盘、失败可重跑。

用法:
  python push_resilient.py            # 开始/继续推送
blob 上传进度存于 _push_cache.json（path -> sha），中断后重跑会跳过已上传的 blob。
"""
import base64, hashlib, json, os, socket, sys, time, urllib.request, urllib.error

socket.setdefaulttimeout(30)  # 全局 socket 超时，防止代理层无限 hang

cfg = json.load(open(os.path.expanduser('~/.workbuddy/mcp.json'), encoding='utf-8'))
TOKEN = cfg['mcpServers']['github']['env']['GITHUB_PERSONAL_ACCESS_TOKEN']
OWNER, REPO, BRANCH = 'realrentao', 'Talking-Italian', 'main'
ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, 'site')
CACHE = os.path.join(ROOT, '_push_cache.json')
base_url = 'https://api.github.com/repos/%s/%s' % (OWNER, REPO)
MSG = 'Add original audio for 4 distance phrases in Day 1 plus section'

def api(url, method='GET', data=None, timeout=30):
    h = {'Accept': 'application/vnd.github+json',
         'Authorization': 'Bearer ' + TOKEN,
         'X-GitHub-Api-Version': '2022-11-28',
         'User-Agent': 'talking-italian-builder'}
    req = urllib.request.Request(url, method=method, headers=h)
    if data is not None:
        req.data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    last = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'ignore')
            if e.code in (429, 502, 503, 504) and attempt < 5:
                last = e; time.sleep(3 * (attempt + 1)); continue
            raise RuntimeError('HTTP %s %s: %s' % (e.code, url, body[:200]))
        except Exception as e:
            last = e
            if attempt < 5:
                time.sleep(3 * (attempt + 1)); continue
            raise RuntimeError('%s -> %s' % (url, e))
    raise RuntimeError('%s -> %s' % (url, last))

# 收集文件
files = {}
for dp, ds, fs in os.walk(SITE):
    for f in fs:
        full = os.path.join(dp, f)
        rel = os.path.relpath(full, SITE).replace('\\', '/')
        files[rel] = open(full, 'rb').read()
for rel in ['build.py', 'push_github.py', 'push_resilient.py',
            '_source/audio_manifest.json', '_source/audio_map_v3.json',
            '_source/refine_boundaries.py', '_source/transcribe_dialogue.py',
            '_source/add_dialogue.py', '_source/align_audio_v2.py',
            '_source/fix_dialogue_starts.py', '_source/check_dialogue_starts.py',
            '_source/fix_euro_tail.py', '_source/check_tails.py', '_source/probe_tails.py',
            '_source/transcribe_extra.py', '_source/add_extra_three.py', '_source/probe_extra.py',
            '_source/transcribe_distance.py', '_source/probe_distance.py', '_source/add_distance.py',
            '_source/slice_audio_v2.py', '_source/transcribe_audio.py',
            '_source/content/kt00.json'] + [
            '_source/content/%s%02d.json' % (p, i)
            for p in ('gt', 'kt') for i in range(1, 11)]:
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    if os.path.exists(full):
        files[rel] = open(full, 'rb').read()
files['README.md'] = ('# Talking-Italian\n\n意大利语学习网站：总导航页 + 逐级课程页。\n\n'
    '- 在线：https://realrentao.github.io/Talking-Italian/\n'
    '- 内容数据在 `_source/content/`，运行 `python build.py` 重建 `site/`。\n').encode('utf-8')
print('FILES', len(files), flush=True)

# 断点缓存
cache = {}
if os.path.exists(CACHE):
    try: cache = json.load(open(CACHE, encoding='utf-8'))
    except Exception: cache = {}

# 逐个上传 blob（带进度落盘）。缓存值存 "sha|md5"，内容变了会重新上传。
for i, (path, content) in enumerate(sorted(files.items()), 1):
    cm = hashlib.md5(content).hexdigest()
    cached = cache.get(path, '')
    if '|' in cached and cached.split('|', 1)[1] == cm:
        continue
    digest = base64.b64encode(content).decode('ascii')
    for attempt in range(4):
        try:
            b = api('%s/git/blobs' % base_url, method='POST',
                    data={'content': digest, 'encoding': 'base64'}, timeout=25)
            cache[path] = b['sha'] + '|' + cm
            json.dump(cache, open(CACHE, 'w', encoding='utf-8'))
            break
        except Exception as e:
            print('RETRY blob', i, path, str(e)[:80], flush=True)
            if attempt == 3:
                raise
    if i % 20 == 0 or i == len(files):
        print('BLOBS %d/%d' % (i, len(files)), flush=True)
print('BLOBS DONE', len(cache), flush=True)

# 取 base
ref = api('%s/git/ref/heads/%s' % (base_url, BRANCH))
parent_sha = ref['object']['sha']
parent = api('%s/git/commits/%s' % (base_url, parent_sha))
base_tree = parent['tree']['sha']

tree = [{'path': p, 'mode': '100644', 'type': 'blob', 'sha': cache[p].split('|', 1)[0]}
        for p in sorted(files)]
new_tree = api('%s/git/trees' % base_url, method='POST',
               data={'base_tree': base_tree, 'tree': tree})
commit = api('%s/git/commits' % base_url, method='POST', data={
    'message': MSG, 'tree': new_tree['sha'], 'parents': [parent_sha]})
api('%s/git/refs/heads/%s' % (base_url, BRANCH), method='PATCH',
    data={'sha': commit['sha'], 'force': False})
print('COMMIT', commit['sha'][:12], flush=True)
os.remove(CACHE)  # 提交成功后清缓存
print('URL https://realrentao.github.io/%s/' % REPO, flush=True)
