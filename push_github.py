# -*- coding: utf-8 -*-
"""创建 realrentao/Talking-Italian 并推送站点（Git Data API，单次提交）。"""
import base64, json, os, urllib.request, urllib.error

TOKEN = None
cfg = json.load(open(os.path.expanduser('~/.workbuddy/mcp.json'), encoding='utf-8'))
TOKEN = cfg['mcpServers']['github']['env']['GITHUB_PERSONAL_ACCESS_TOKEN']
OWNER, REPO, BRANCH = 'realrentao', 'Talking-Italian', 'main'
ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, 'site')

def api(url, method='GET', data=None):
    h = {'Accept': 'application/vnd.github+json',
         'Authorization': 'Bearer ' + TOKEN,
         'X-GitHub-Api-Version': '2022-11-28',
         'User-Agent': 'talking-italian-builder'}
    req = urllib.request.Request(url, method=method, headers=h)
    if data is not None:
        req.data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'ignore')
        raise RuntimeError('%s %s -> HTTP %s: %s' % (method, url, e.code, body[:400]))

# 1. 仓库是否存在
repo_url = 'https://api.github.com/repos/%s/%s' % (OWNER, REPO)
try:
    repo = api(repo_url)
    print('REPO EXISTS', repo['html_url'])
except RuntimeError as e:
    if 'HTTP 404' not in str(e):
        raise
    repo = api('https://api.github.com/user/repos', method='POST', data={
        'name': REPO,
        'description': '意大利语学习网站 · 以教材为单位组织的学习书架（中文讲解 + 意语点击发音）',
        'homepage': 'https://realrentao.github.io/%s/' % REPO,
        'private': False,
        'auto_init': True,
        'default_branch': BRANCH,
    })
    print('REPO CREATED', repo['html_url'])

# 2. 收集要推送的文件（站点全部 + 生成器与内容数据，便于后续追加教材）
files = {}
for dp, ds, fs in os.walk(SITE):
    for f in fs:
        full = os.path.join(dp, f)
        rel = os.path.relpath(full, SITE).replace('\\', '/')
        files[rel] = open(full, 'rb').read()
for rel in ['build.py', 'push_github.py',
            '_source/audio_manifest.json', '_source/audio_map_v2.json',
            '_source/align_audio_v2.py', '_source/slice_audio_v2.py',
            '_source/transcribe_audio.py',
            '_source/content/kt00.json'] + [
            '_source/content/%s%02d.json' % (p, i)
            for p in ('gt', 'kt') for i in range(1, 11)]:
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    if os.path.exists(full):
        files[rel] = open(full, 'rb').read()
files['README.md'] = ('# Talking-Italian\n\n'
    '意大利语学习网站：以教材为单位的总导航页 + 逐级展开的课程页。\n\n'
    '- 在线访问：https://realrentao.github.io/Talking-Italian/\n'
    '- 已接入教材：Get Talking / Keep Talking Italian in Ten Days（两册共 20 天，中文讲解 + 意语点击发音）\n'
    '- 总导航页预留同层级教材入口，后续追加教材无需改动现有页面。\n\n'
    '内容数据在 `_source/content/`，运行 `python build.py` 可重建 `site/`。\n').encode('utf-8')
print('FILES', len(files))

# 3. 取得当前 ref 与 base tree
base_url = 'https://api.github.com/repos/%s/%s' % (OWNER, REPO)
ref = api('%s/git/ref/heads/%s' % (base_url, BRANCH))
parent_sha = ref['object']['sha']
parent_commit = api('%s/git/commits/%s' % (base_url, parent_sha))
base_tree = parent_commit['tree']['sha']

# 4. 创建 blobs + tree
tree = []
for path, content in sorted(files.items()):
    b = api('%s/git/blobs' % base_url, method='POST',
            data={'content': base64.b64encode(content).decode('ascii'), 'encoding': 'base64'})
    tree.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': b['sha']})
new_tree = api('%s/git/trees' % base_url, method='POST',
               data={'base_tree': base_tree, 'tree': tree})

# 5. 提交并更新 ref
commit = api('%s/git/commits' % base_url, method='POST', data={
    'message': 'Fix audio clip boundaries with word-level alignment (no truncated sentences)',
    'tree': new_tree['sha'],
    'parents': [parent_sha],
})
api('%s/git/refs/heads/%s' % (base_url, BRANCH), method='PATCH',
    data={'sha': commit['sha'], 'force': False})
print('COMMIT', commit['sha'][:12])

# 6. 启用 Pages（若尚未启用）
try:
    pages = api('%s/pages' % base_url)
    print('PAGES EXISTS', pages.get('html_url'))
except RuntimeError as e:
    if 'HTTP 404' not in str(e):
        print('PAGES CHECK WARN', e)
    else:
        p = api('%s/pages' % base_url, method='POST',
                data={'source': {'branch': BRANCH, 'path': '/'}})
        print('PAGES ENABLED', p.get('html_url'))

print('URL https://realrentao.github.io/%s/' % REPO)
