# -*- coding: utf-8 -*-
"""抽查句尾后续语音是意语尾词(被切)还是英文翻译(不能切)。空 prompt 客观识别。"""
import os, subprocess, sys, tempfile
from faster_whisper import WhisperModel

MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'tiny')
model = WhisperModel(MODEL_DIR, device='cpu', compute_type='int8',
                     cpu_threads=1, num_workers=1)

# (lo, hi, 说明)  —— 覆盖 end 前后
probes = [
    (1282.0, 1283.8, 'gt02 Quale macchina desidera? end=1282.56'),
    (2259.5, 2261.4, 'gt03 Vorrei quattro biglietti end=2260.12'),
    (4828.0, 4830.0, 'gt05 Un te per favore end=4828.69'),
    (7312.0, 7314.0, 'gt08 Il museo e gratuito end=7312.78'),
]
for lo, hi, tag in probes:
    tmp = tempfile.mkdtemp(prefix='tail_')
    wav = os.path.join(tmp, 's.wav')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '%.3f' % lo,
                    '-t', '%.3f' % (hi - lo), '-i', MP3,
                    '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', wav], check=True)
    segs, _ = model.transcribe(wav, language='it', beam_size=5,
                               vad_filter=False, word_timestamps=True,
                               condition_on_previous_text=False)
    print('=== %s ===' % tag)
    for s in segs:
        ws = [(round(lo + w.start, 2), round(lo + w.end, 2), w.word.strip())
              for w in (s.words or []) if w.start is not None]
        print('  %7.2f-%7.2f %r' % (lo + s.start, lo + s.end, s.text.strip()))
        print('     words:', ws)
    sys.stdout.flush()
