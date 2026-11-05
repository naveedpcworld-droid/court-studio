#!/usr/bin/env python3
"""Step 5 — narrator voice for every commentary block in script.json.

  python3 tools/voice.py <project>

Voice = Microsoft "Brian Multilingual" (same voice as Clipchamp text-to-speech) via edge-tts.
Change it with "voice" in script.json (e.g. en-US-AndrewMultilingualNeural, en-US-AvaMultilingualNeural).
Needs edge-tts >= 7.3 (older versions get HTTP 403):  pip3 install -U edge-tts
Also saves word timings (vo_tx.json) for the captions.
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import proj_dir, load_json, save_json, dur

name = sys.argv[1]
d = proj_dir(name)
S = load_json(os.path.join(d, 'script.json'))
voice = S.get('voice', 'en-US-BrianMultilingualNeural')
os.makedirs(os.path.join(d, 'vo'), exist_ok=True)
for v in S['vo']:
    out = os.path.join(d, 'vo', v['id'] + '.mp3')
    stamp = out + '.txt'
    if os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == voice + v['text']:
        continue                                    # unchanged text -> keep existing audio
    subprocess.run(['edge-tts', '--voice', voice, '--rate', S.get('rate', '+0%'), '--text', v['text'],
                    '--write-media', out], check=True)
    open(stamp, 'w').write(voice + v['text'])
    print(f"{v['id']}: {dur(out):.1f}s", flush=True)

from faster_whisper import WhisperModel
m = WhisperModel('small.en', device='cpu', compute_type='int8')
words = {}
for v in S['vo']:
    segs, _ = m.transcribe(os.path.join(d, 'vo', v['id'] + '.mp3'), word_timestamps=True)
    words[v['id']] = [[round(w.start, 2), round(w.end, 2), w.word] for s in segs for w in s.words]
save_json(words, os.path.join(d, 'vo_tx.json'))
total = sum(dur(os.path.join(d, 'vo', v['id'] + '.mp3')) for v in S['vo'])
print(f'{len(S["vo"])} voice blocks, {total:.0f}s of narration')
print('NEXT: python3 tools/build.py', name, '--template T1')
