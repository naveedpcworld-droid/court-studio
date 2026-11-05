#!/usr/bin/env python3
"""Step 5 — narrator voice for every commentary block in script.json.

  python3 tools/voice.py <project>                      # provider from script.json / config.env
  python3 tools/voice.py <project> --provider ai33      # override
  python3 tools/voice.py --test ai33 "Testing one two"  # check a key / voice -> /tmp/voice_test.mp3

Providers (pick in script.json "voice_provider", or VOICE_PROVIDER in config.env):
  edge        FREE, no key. Microsoft "Brian Multilingual" (= Clipchamp TTS voice). Default.
              voice = en-US-BrianMultilingualNeural | en-US-AndrewMultilingualNeural | en-US-AvaMultilingualNeural ...
              Needs edge-tts >= 7.3 (older = HTTP 403):  pip3 install -U edge-tts
  ai33        ai33.pro (ElevenLabs voices, cheaper). config.env: AI33_KEY, AI33_VOICE (e.g. elevenlabs_xxxx)
  elevenlabs  ElevenLabs direct. config.env: ELEVENLABS_KEY, ELEVENLABS_VOICE (voice id), ELEVENLABS_MODEL
Also saves word timings (vo_tx.json) for the captions.
"""
import argparse, json, os, subprocess, sys, time, urllib.error, urllib.request, uuid
sys.path.insert(0, os.path.dirname(__file__))
from common import proj_dir, load_json, save_json, dur, STUDIO

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'


def cfg():
    c = {}
    p = os.path.join(STUDIO, 'config.env')
    if os.path.exists(p):
        for ln in open(p):
            if '=' in ln and not ln.strip().startswith('#'):
                k, v = ln.strip().split('=', 1); c[k.strip()] = v.strip().strip('"')
    for k in ('AI33_KEY', 'AI33_VOICE', 'ELEVENLABS_KEY', 'ELEVENLABS_VOICE', 'ELEVENLABS_MODEL', 'VOICE_PROVIDER'):
        if os.environ.get(k): c[k] = os.environ[k]
    return c


C = cfg()


def need(k, prov):
    if not C.get(k): sys.exit(f'{prov}: {k} missing in studio/config.env (see config.env.example)')
    return C[k]


def tts_edge(text, out, voice, rate):
    subprocess.run(['edge-tts', '--voice', voice or 'en-US-BrianMultilingualNeural', '--rate', rate, '--text', text,
                    '--write-media', out], check=True)


def tts_ai33(text, out, voice, speed):
    key = need('AI33_KEY', 'ai33'); voice = voice or need('AI33_VOICE', 'ai33')
    fields = {'text': text, 'voice_id': voice, 'speed': speed}
    bnd = uuid.uuid4().hex; body = b''
    for k, v in fields.items():
        body += f'--{bnd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    body += f'--{bnd}--\r\n'.encode()
    hdr = {'xi-api-key': key, 'User-Agent': UA}
    for i in range(5):
        try:
            r = urllib.request.Request('https://api.ai33.pro/v3/text-to-speech', data=body, method='POST',
                                       headers={**hdr, 'Content-Type': f'multipart/form-data; boundary={bnd}'})
            task = json.load(urllib.request.urlopen(r, timeout=180)).get('task_id'); break
        except urllib.error.HTTPError as e:
            if e.code in (401, 403): sys.exit(f'ai33 key rejected ({e.code})')
            time.sleep(5 * (i + 1))
    else:
        sys.exit('ai33 submit failed')
    url = None
    for _ in range(120):
        time.sleep(3)
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(f'https://api.ai33.pro/v3/task/{task}', headers=hdr), timeout=60)).get('data', {})
        except (urllib.error.URLError, TimeoutError, ValueError):
            continue                                # 5xx / network blip -> keep polling
        if d.get('status') == 'done': url = (d.get('metadata') or {}).get('audio_url'); break
        if d.get('status') == 'failed': sys.exit(f'ai33 task failed: {d}')
    if not url: sys.exit('ai33: no audio url (timeout)')
    open(out, 'wb').write(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=300).read())


def tts_elevenlabs(text, out, voice, speed):
    key = need('ELEVENLABS_KEY', 'elevenlabs'); voice = voice or need('ELEVENLABS_VOICE', 'elevenlabs')
    body = json.dumps({'text': text, 'model_id': C.get('ELEVENLABS_MODEL', 'eleven_multilingual_v2'),
                       'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75, 'speed': float(speed)}}).encode()
    r = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128', data=body,
                               method='POST', headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
    open(out, 'wb').write(urllib.request.urlopen(r, timeout=300).read())


def speak(prov, text, out, voice, S):
    if prov == 'edge': tts_edge(text, out, voice, S.get('rate', '+0%'))
    elif prov == 'ai33': tts_ai33(text, out, voice, str(S.get('speed', '1.0')))
    elif prov == 'elevenlabs': tts_elevenlabs(text, out, voice, S.get('speed', 1.0))
    else: sys.exit(f'unknown voice provider {prov} (edge | ai33 | elevenlabs)')
    if not os.path.exists(out) or os.path.getsize(out) < 2000: sys.exit(f'{prov}: empty audio for {out}')


ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--provider')
ap.add_argument('--test', nargs=2, metavar=('PROVIDER', 'TEXT'))
a = ap.parse_args()
if a.test:
    speak(a.test[0], a.test[1], '/tmp/voice_test.mp3', None, {}); print('ok ->', '/tmp/voice_test.mp3', f'{dur("/tmp/voice_test.mp3"):.1f}s'); sys.exit()

name = a.project
d = proj_dir(name)
S = load_json(os.path.join(d, 'script.json'))
prov = a.provider or S.get('voice_provider') or C.get('VOICE_PROVIDER') or 'edge'
voice = S.get('voice') if prov == 'edge' else S.get('voice_id')     # edge name vs ai33/11labs id
if prov == 'edge' and not voice: voice = 'en-US-BrianMultilingualNeural'
os.makedirs(os.path.join(d, 'vo'), exist_ok=True)
for v in S['vo']:
    out = os.path.join(d, 'vo', v['id'] + '.mp3')
    stamp = out + '.txt'; sig = f'{prov}|{voice}|{v["text"]}'
    if os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == sig:
        continue                                    # unchanged text -> keep existing audio
    speak(prov, v['text'], out, voice, S)
    open(stamp, 'w').write(sig)
    print(f"{v['id']}: {dur(out):.1f}s  ({prov})", flush=True)

from faster_whisper import WhisperModel
m = WhisperModel('small.en', device='cpu', compute_type='int8')
words = {}
for v in S['vo']:
    segs, _ = m.transcribe(os.path.join(d, 'vo', v['id'] + '.mp3'), word_timestamps=True)
    words[v['id']] = [[round(w.start, 2), round(w.end, 2), w.word] for s in segs for w in s.words]
save_json(words, os.path.join(d, 'vo_tx.json'))
total = sum(dur(os.path.join(d, 'vo', v['id'] + '.mp3')) for v in S['vo'])
print(f'{len(S["vo"])} voice blocks, {total:.0f}s of narration ({prov})')
print('NEXT: python3 tools/build.py', name, '--template T01')
