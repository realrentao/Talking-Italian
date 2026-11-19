# -*- coding: utf-8 -*-
"""针对 gt01 对话段用 initial_prompt 定向转写，拿词级时间戳。
用法: python transcribe_dialogue.py <lo> <hi> <out.jsonl>
"""
import json, os, subprocess, sys, tempfile
from faster_whisper import WhisperModel

LO = float(sys.argv[1]); HI = float(sys.argv[2]); OUT = sys.argv[3]
MP3 = r'D:/Get Talking Keep talking Italian/Get Talking Italian in Ten Days.mp3'
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'tiny')

# 给出这段对话的意大利语原文作为提示，引导 tiny 识别
PROMPT = ("Conversazione in italiano tra John e un tassista. "
          "Buongiorno. Buongiorno, devo andare all'albergo Regina Margherita. "
          "In quale via? In via Pace. A quale numero e l'albergo? "
          "Al numero otto, credo. Va bene, al numero otto di via Pace. "
          "Ecco l'albergo Regina Margherita. Sono dieci euro. "
          "Bene, grazie. Ecco a lei. Grazie, arrivederci.")

model = WhisperModel(MODEL_DIR, device='cpu', compute_type='int8',
                     cpu_threads=1, num_workers=1)
tmp = tempfile.mkdtemp(prefix='dlg_')
wav = os.path.join(tmp, 'seg.wav')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '%.3f' % LO,
                '-t', '%.3f' % (HI - LO), '-i', MP3,
                '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', wav], check=True)

segs, info = model.transcribe(
    wav, language='it', initial_prompt=PROMPT, beam_size=5,
    vad_filter=False, word_timestamps=True,
    condition_on_previous_text=False,
)
rows = []
with open(OUT, 'w', encoding='utf-8') as f:
    for s in segs:
        words = []
        for w in (s.words or []):
            if w.start is None or w.end is None:
                continue
            words.append({'w': w.word, 's': round(LO + w.start, 3), 'e': round(LO + w.end, 3)})
        rec = {'start': round(LO + s.start, 3), 'end': round(LO + s.end, 3),
               'text': s.text.strip(), 'words': words}
        rows.append(rec)
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        print('%7.2f-%7.2f %r' % (rec['start'], rec['end'], rec['text']))
print('SEGS', len(rows), '->', OUT)
