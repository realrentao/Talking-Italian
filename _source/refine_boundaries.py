# -*- coding: utf-8 -*-
"""用波形能量对 v2 词级边界做二次校正，修复短词被切头/切尾。

思路：
- whisper tiny 对短词（如 "in"）的词级时间戳严重压缩（实测把 0.2s 的 in 标成 20ms），
  导致切片起点切晚、切掉首词辅音/元音。
- 对每条 item，在 [start-W, start+0.15] 内检测真实语音起点（静音结束点），
  在 [end-0.15, end+W] 内检测真实语音终点（静音开始点），把边界吸附到能量突变处。
- 只在存在明确静音间隙（低能量持续 >= 0.10s）时才校正，且幅度封顶，避免切进相邻语句。
"""
import json, os, math, struct, subprocess, sys, concurrent.futures

ROOT = os.path.dirname(os.path.abspath(__file__))
MP3 = 'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
MAP = os.path.join(ROOT, 'audio_map_v2.json')
OUT = os.path.join(ROOT, 'audio_map_v3.json')
SR = 16000
WIN = 0.02                 # 20ms 分析窗
SIL_DB = -42.0             # 静音阈值
MIN_SIL = 0.10             # 最小静音长度
W = 0.70                   # 向前/向后最大搜索范围
MAX_SHIFT_S = 0.75         # 起点最大前移
MAX_SHIFT_E = 0.75         # 终点最大后移

def db_of(seg):
    rms = math.sqrt(sum(x * x for x in seg) / len(seg))
    return 20 * math.log10(rms / 32768) if rms > 0 else -120.0

def decode_window(s, e):
    """解码 [s,e] 的 16k 单声道 s16le，返回 (base_time, samples)."""
    s = max(0, s)
    cmd = ['ffmpeg', '-v', 'error', '-ss', '%.3f' % s, '-t', '%.3f' % (e - s),
           '-i', MP3, '-ar', str(SR), '-ac', '1', '-f', 's16le', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // 2
    return s, struct.unpack('<%dh' % n, raw[:n * 2])

def energy_curve(s, e):
    base, smp = decode_window(s, e)
    step = int(SR * WIN)
    curve = []
    for i in range(0, len(smp) - step, step):
        db = db_of(smp[i:i + step])
        curve.append((base + i / SR, db))
    return curve

def refine_start(start, end):
    # 解码 [start-W, start+0.15]
    lo = max(0, start - W)
    curve = energy_curve(lo, start + 0.16)
    if not curve:
        return start
    # 只看时间 <= start+0.05 的部分，从 start 往前扫描，
    # 找到"最后一段 >=MIN_SIL 的静音"的结束点 = 真实语音起点
    silent_runs = []
    run_start = None
    for t, db in curve:
        if t > start + 0.05:
            break
        if db < SIL_DB:
            if run_start is None:
                run_start = t
        else:
            if run_start is not None and t - run_start >= MIN_SIL:
                silent_runs.append((run_start, t))
            run_start = None
    if not silent_runs:
        return start
    # 取最靠近 start 的静音段，其结束点作为语音起点
    last_sil_end = silent_runs[-1][1]
    cand = last_sil_end
    if cand < start - MAX_SHIFT_S:   # 限制过度前移
        return start
    return round(cand, 3)

def refine_end(start, end):
    hi = end + W
    curve = energy_curve(end - 0.16, hi)
    if not curve:
        return end
    # 从 end 往后找"第一段 >=MIN_SIL 的静音"的起点 = 真实语音终点
    run_start = None
    for t, db in curve:
        if t < end - 0.05:
            continue
        if db < SIL_DB:
            if run_start is None:
                run_start = t
            if t - run_start >= MIN_SIL:
                cand = run_start
                if cand > end + MAX_SHIFT_E:
                    return end
                return round(cand, 3)
        else:
            run_start = None
    return end

def refine_item(it):
    s0, e0 = it['start'], it['end']
    ns = refine_start(s0, e0)
    ne = refine_end(s0, e0)
    return it['key'], s0, e0, ns, ne

def main():
    data = json.load(open(MAP, encoding='utf-8'))
    items = [it for info in data.values() for it in info['items']]
    print('条目总数', len(items))
    changes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for key, s0, e0, ns, ne in ex.map(refine_item, items):
            ds = round(ns - s0, 3)
            de = round(ne - e0, 3)
            if abs(ds) >= 0.04 or abs(de) >= 0.04:
                changes.append((key, s0, e0, ns, ne, ds, de))
    # 应用校正
    applied = {}
    for key, s0, e0, ns, ne, ds, de in changes:
        applied[key] = (ns, ne)
    cnt = 0
    for info in data.values():
        for it in info['items']:
            if it['key'] in applied:
                it['orig_start'], it['orig_end'] = it['start'], it['end']
                it['start'], it['end'] = applied[it['key']]
                cnt += 1
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('校正条目', cnt, '->', OUT)
    print('\n=== 起点前移最多的 25 条 ===')
    for c in sorted([x for x in changes if x[5] < 0], key=lambda x: x[5])[:25]:
        print('%s  %7.3f->%7.3f (%+.3f)  end %7.3f->%7.3f (%+.3f)' % (c[0], c[1], c[3], c[5], c[2], c[4], c[6]))

if __name__ == '__main__':
    main()
