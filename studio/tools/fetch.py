#!/usr/bin/env python3
"""Step 1 — get the source hearing and transcribe it (word timestamps).

  python3 tools/fetch.py <project> <youtube-url | local-video> [--model small.en]
  python3 tools/fetch.py <project> <youtube-url> --section 600 1200   # only that part (from find_case.py hot)

Writes projects/<project>/src_full.mp4 + tx_full.json and prints the length.
Long videos (1-3 hours) take a while to transcribe: ~10-15 min per hour of audio with small.en,
use --model base.en to go ~2x faster.
"""
import argparse, json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import proj_dir, dur, save_json

ap = argparse.ArgumentParser()
ap.add_argument('project'); ap.add_argument('source')
ap.add_argument('--model', default='small.en')
ap.add_argument('--section', nargs=2, type=float, metavar=('START', 'END'), help='seconds; download only this part')
a = ap.parse_args()
d = proj_dir(a.project)
src = os.path.join(d, 'src_full.mp4')

if not os.path.exists(src):
    if a.source.startswith('http'):
        meta = subprocess.run(['yt-dlp', '--no-warnings', '--skip-download', '--print',
                               '%(title)s\t%(channel)s\t%(view_count)s\t%(duration)s', a.source],
                              capture_output=True, text=True).stdout.strip()
        open(os.path.join(d, 'source.txt'), 'w').write(a.source + '\n' + meta + '\n')
        sec = ['--download-sections', f'*{a.section[0]:.0f}-{a.section[1]:.0f}', '--force-keyframes-at-cuts'] if a.section else []
        subprocess.run(['yt-dlp', '-q', '--no-warnings', '-f', 'bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b',
                        '--merge-output-format', 'mp4', *sec, '-o', src, a.source], check=True)
        if a.section:
            open(os.path.join(d, 'source.txt'), 'a').write(f'section {a.section[0]:.0f}-{a.section[1]:.0f} s of the original\n')
    else:
        shutil.copy(a.source, src)
        open(os.path.join(d, 'source.txt'), 'w').write(os.path.abspath(a.source) + '\n')
print('source:', src, f'{dur(src) / 60:.1f} min', flush=True)

txp = os.path.join(d, 'tx_full.json')
if not os.path.exists(txp):
    from faster_whisper import WhisperModel
    print(f'transcribing with {a.model} ...', flush=True)
    m = WhisperModel(a.model, device='cpu', compute_type='int8', cpu_threads=os.cpu_count() or 4)
    segs, _ = m.transcribe(src, word_timestamps=True)
    out = []
    for s in segs:
        out.append({'s': round(s.start, 2), 'e': round(s.end, 2), 't': s.text.strip(),
                    'w': [[round(w.start, 2), round(w.end, 2), w.word] for w in (s.words or [])]})
        if len(out) % 50 == 0:
            print(f'  {s.end / 60:.1f} min transcribed', flush=True)
    save_json(out, txp)
# plain-text transcript for reading
with open(os.path.join(d, 'transcript_full.txt'), 'w') as f:
    for s in json.load(open(txp)):
        f.write(f"[{int(s['s'] // 60):02d}:{s['s'] % 60:04.1f}] {s['t']}\n")
print('transcript:', os.path.join(d, 'transcript_full.txt'))
print('NEXT: python3 tools/cases.py', a.project)
