# -*- coding: utf-8 -*-
"""分块转写音频，避免整段载入内存。用法：
python transcribe_audio.py <mp3> <out.jsonl> [start_sec] [end_sec] [chunk_sec]
"""
import json, os, subprocess, sys, tempfile

MP3 = sys.argv[1]
OUT = sys.argv[2]
START = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
END = float(sys.argv[4]) if len(sys.argv) > 4 else 1e9
CHUNK = float(sys.argv[5]) if len(sys.argv) > 5 else 180.0
MODEL = os.environ.get('WHISPER_MODEL', 'base')
THREADS = int(os.environ.get('WHISPER_THREADS', '2'))

from faster_whisper import WhisperModel

model = WhisperModel(MODEL, device='cpu', compute_type='int8',
                     cpu_threads=THREADS, num_workers=1)

tmpdir = tempfile.mkdtemp(prefix='it_audio_')
n = 0
with open(OUT, 'w', encoding='utf-8') as f:
    t = START
    while t < END:
        wav = os.path.join(tmpdir, 'c%04d.wav' % n)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(t), '-t', str(CHUNK),
                        '-i', MP3, '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', wav],
                       check=True)
        try:
            segs, info = model.transcribe(
                wav, language=None, beam_size=1, vad_filter=True,
                vad_parameters={'min_silence_duration_ms': 300},
                word_timestamps=os.environ.get('WORD_TS', '0') == '1',
            )
            count = 0
            for s in segs:
                words = [{'w': w.word, 's': round(t + w.start, 3), 'e': round(t + w.end, 3)}
                         for w in (s.words or []) if w.start is not None and w.end is not None]
                rec = {'start': round(t + s.start, 3), 'end': round(t + s.end, 3),
                       'text': s.text.strip(),
                       'language': getattr(s, 'language', None),
                       'p': round(getattr(s, 'avg_logprob', 0) or 0, 3),
                       'words': words}
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                count += 1
            f.flush()
            print('chunk %d  %.0f-%.0f  lang=%s  segs=%d' %
                  (n, t, t + CHUNK, info.language, count), flush=True)
        except Exception as e:
            print('ERROR chunk %d %s' % (n, e), flush=True)
        os.remove(wav)
        t += CHUNK
        n += 1
print('DONE', OUT, flush=True)
