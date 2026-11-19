# -*- coding: utf-8 -*-
"""定向转写 gt01 plus 组距离句型。
用法: python transcribe_distance.py <lo> <hi> <out.jsonl>
"""
import json, os, subprocess, sys, tempfile
from faster_whisper import WhisperModel

LO = float(sys.argv[1]); HI = float(sys.argv[2]); OUT = sys.argv[3]
MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'tiny')

PROMPT = ("Esercizio di italiano: è vicino? È lontano? È abbastanza lontano. "
          "Quanto ci vuole? Dieci minuti a piedi. Dieci minuti in macchina. "
          "È troppo lontano a piedi.")

model = WhisperModel(MODEL_DIR, device='cpu', compute_type='int8',
                     cpu_threads=1, num_workers=1)
tmp = tempfile.mkdtemp(prefix='dist_')
wav = os.path.join(tmp, 'seg.wav')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '%.3f' % LO,
                '-t', '%.3f' % (HI - LO), '-i', MP3,
                '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', wav], check=True)
segs, _ = model.transcribe(
    wav, language='it', initial_prompt=PROMPT, beam_size=5,
    vad_filter=False, word_timestamps=True, condition_on_previous_text=False)
with open(OUT, 'w', encoding='utf-8') as f:
    for s in segs:
        words = []
        for w in (s.words or []):
            if w.start is None or w.end is None: continue
            words.append({'w': w.word, 's': round(LO + w.start, 3), 'e': round(LO + w.end, 3)})
        rec = {'start': round(LO + s.start, 3), 'end': round(LO + s.end, 3),
               'text': s.text.strip(), 'words': words}
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        print('%7.2f-%7.2f %r' % (rec['start'], rec['end'], rec['text']))
        for w in words: print('    %7.3f-%7.3f %r' % (w['s'], w['e'], w['w']))
print('DONE')
