#!/usr/bin/env python3
"""Thumbnail — real faces from the hearing, made into a competitor-style thumbnail by ChatGPT.

  python3 tools/thumbnail.py <project> frames                  # best face frames per camera -> thumbs/frames/ + sheet.jpg
  python3 tools/thumbnail.py <project> frames --at 520 540 615   # frames at exact seconds (when the defendant talks)
  python3 tools/thumbnail.py <project> make --left thumbs/frames/c1_03.jpg --right thumbs/frames/c0_05.jpg \\
          --text "NO NAME?!" --sub "SOVEREIGN CITIZEN" [--arrow right] [--style split|single|reaction]
  python3 tools/thumbnail.py <project> fix "make the yellow word bigger, arrow points at his face"

1. `frames` samples the hearing, crops every camera tile, scores frames by face size + sharpness
   (OpenCV if installed, sharpness only otherwise) and saves the top picks + a numbered contact sheet.
   LOOK at sheet.jpg and pick the judge frame and the defendant frame (strong expression, eyes open).
2. `make` sends those frames to ChatGPT (../thumbnail-gpt, your own logged-in ChatGPT window) with the
   competitor thumbnail formula: two-panel split, faces upscaled + cleaned, 2-5 word slang quote in
   bold white/yellow caps with black outline, red arrow, high contrast. Result -> thumbs/thumb_N.jpg (1920x1080).
3. Judge it yourself (spelling, faces still the same people, arrow, readable on a phone). Wrong -> `fix`.
First time: cd ../thumbnail-gpt && npm install && node open.js  -> log in to ChatGPT in that window once.
"""
import argparse, glob, json, os, socket, subprocess, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from common import proj_dir, load_json, dur, STUDIO
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import numpy as np

TOOL = os.path.join(os.path.dirname(STUDIO), 'thumbnail-gpt')
PORT = json.load(open(os.path.join(TOOL, 'config.json'))).get('port', 9334) if os.path.exists(os.path.join(TOOL, 'config.json')) else 9334


_CC = []


def _cascade():
    if not _CC:
        try:
            import cv2
            _CC.append(cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'))
        except Exception:                                   # no OpenCV / build without objdetect
            _CC.append(None)
    return _CC[0]


def faces(img):
    cc = _cascade()
    if cc is None: return []
    import cv2
    g = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    return list(cc.detectMultiScale(g, 1.15, 6, minSize=(48, 48)))


def sharp(img):
    a = np.asarray(img.convert('L'), dtype=np.float32)
    return float(np.var(a[1:, :] - a[:-1, :]) + np.var(a[:, 1:] - a[:, :-1]))


def cmd_frames(d, n_per=6, at=None):
    L = load_json(os.path.join(d, 'layout.json')); src = os.path.join(d, 'src.mp4')
    out = os.path.join(d, 'thumbs', 'frames'); os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(out, '*.jpg')): os.remove(f)
    total = dur(src); step = max(2.0, total / 180)
    cand = {}
    times = [float(x) for x in at] if at else None       # --at: exact moments (e.g. when the defendant speaks)
    t = times.pop(0) if times else 1.0
    while t < total - 1:
        lid = next((m[0] for m in L['modes'] if m[1] <= t < m[2]), L['modes'][-1][0])
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', src, '-frames:v', '1', '-f', 'image2pipe',
                              '-vcodec', 'png', '-'], capture_output=True).stdout
        if raw:
            from io import BytesIO
            im = Image.open(BytesIO(raw)).convert('RGB')
            for k, (x, y, w, h) in enumerate(L['layouts'][lid]['tiles'][:3]):
                tile = im.crop((x, y, x + w, y + h))
                fs = faces(tile)
                fa = max((fw * fh for fx, fy, fw, fh in fs), default=0) / float(w * h)
                score = sharp(tile) * (1 + 25 * fa) * (1.0 if fs or not faces_ok() else 0.3)
                cand.setdefault(k, []).append((score, t, tile))
        if at is not None:
            if not times: break
            t = times.pop(0)
        else:
            t += step
    sheet_items = []
    for k, lst in cand.items():
        lst.sort(key=lambda z: -z[0]); pick = []
        for sc, tt, tile in lst:
            if all(abs(tt - p[1]) > (1 if at else 15) for p in pick): pick.append((sc, tt, tile))
            if len(pick) >= (99 if at else n_per): break
        for i, (sc, tt, tile) in enumerate(pick, 1):
            p = os.path.join(out, f'c{k}_{i:02d}.jpg'); tile.save(p, quality=95)
            sheet_items.append((f'c{k}_{i:02d}  t={int(tt)}s', tile))
    cols = 4; tw = 480; rows = (len(sheet_items) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw, rows * 300), (20, 20, 20)); dr = ImageDraw.Draw(sheet)
    for i, (lab, tile) in enumerate(sheet_items):
        th = ImageOps.fit(tile, (tw - 8, 260)); x, y = (i % cols) * tw + 4, (i // cols) * 300 + 4
        sheet.paste(th, (x, y)); dr.rectangle([x, y + 260, x + tw - 8, y + 292], fill=(0, 0, 0)); dr.text((x + 8, y + 266), lab, fill=(255, 230, 0))
    sp = os.path.join(d, 'thumbs', 'sheet.jpg'); sheet.save(sp, quality=85)
    print(f'{len(sheet_items)} frames ->', out, '\nLOOK:', sp, '(c0 = camera 1, c1 = camera 2 ...)')


def faces_ok():
    return _cascade() is not None


def holder_up():
    s = socket.socket(); s.settimeout(1)
    try:
        s.connect(('127.0.0.1', PORT)); return True
    except OSError:
        return False
    finally:
        s.close()


def ensure_holder():
    if not os.path.isdir(os.path.join(TOOL, 'node_modules')):
        print('installing thumbnail tool (npm install) ...', flush=True)
        subprocess.run(['npm', 'install', '--silent'], cwd=TOOL, check=True)
    if holder_up(): return
    print('opening the ChatGPT window (thumbnail-gpt/open.js) ...', flush=True)
    subprocess.Popen(['node', 'open.js'], cwd=TOOL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(40):
        time.sleep(1)
        if holder_up(): time.sleep(4); return
    sys.exit('ChatGPT window did not open. Run: cd thumbnail-gpt && node open.js  (log in once)')


def prompt_for(a, two):
    arrow = {'left': 'the person on the LEFT', 'right': 'the person on the RIGHT'}.get(a.arrow, 'the person on the RIGHT')
    words = a.text.strip()
    hi = a.highlight or words.split()[-1]
    if a.style == 'single' or not two:
        layout = ('Layout: ONE large close-up of the person in the attached photo, filling the right two-thirds of the frame, '
                  'dark dramatic courtroom background on the left where the text goes.')
        arrow = 'the person'
    elif a.style == 'reaction':
        layout = ('Layout: the person in photo 2 large in the foreground (right side, shocked or angry expression), the person in '
                  'photo 1 smaller in a bordered box top-left, like a live TV inset.')
    else:
        layout = ('Layout: a two-panel split screen with a thin white vertical divider. LEFT panel = the person in photo 1 '
                  f'({a.left_role}), RIGHT panel = the person in photo 2 ({a.right_role}). Tight head-and-shoulders close-ups, faces large.')
    sub = f' Under it, a small red label box with white text "{a.sub.upper()}".' if a.sub else ''
    return (
        'Please generate an image for me: a YouTube thumbnail, landscape 16:9 (1792x1024), for a courtroom commentary video. '
        'Use the attached real photos of the people. Keep each person\'s real face, identity, skin tone, hair and clothing '
        'EXACTLY the same — do not replace or beautify them — but upscale and restore them: sharp, high detail, clean lighting, '
        f'no blur, no compression noise, photorealistic (not cartoon, not illustration). {layout} '
        f'Big bold UPPERCASE text across the top in a heavy condensed sans-serif font (like Impact): "{words.upper()}" — white letters, '
        f'the word "{hi.upper()}" in bright yellow, thick black outline and drop shadow, very readable on a phone.{sub} '
        f'A thick bright red arrow pointing at the face of {arrow}. High contrast, saturated, dramatic, viral YouTube style. '
        'Spell every word exactly as written. No other text, no logos, no watermarks, no captions.')


def finish(src_png, d):
    out_dir = os.path.join(d, 'thumbs'); n = len(glob.glob(os.path.join(out_dir, 'thumb_*.jpg'))) + 1
    im = ImageOps.fit(Image.open(src_png).convert('RGB'), (1920, 1080), Image.LANCZOS)
    p = os.path.join(out_dir, f'thumb_{n}.jpg'); im.save(p, quality=93); return p


def run_tool(script, args_):
    r = subprocess.run(['node', script, *args_], cwd=TOOL, capture_output=True, text=True, timeout=900)
    lines = [l for l in r.stdout.splitlines() if l.startswith(('SAVED', 'NOIMG', 'ERR'))]
    saved = [l[6:].strip() for l in lines if l.startswith('SAVED') and not l.strip().endswith('_2k.jpg')]
    if not saved:
        sys.exit('no image: ' + ' | '.join(lines or [r.stdout[-300:], r.stderr[-300:]]))
    return saved[0] if os.path.isabs(saved[0]) else os.path.join(TOOL, saved[0])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('cmd'); ap.add_argument('note', nargs='?')
    ap.add_argument('--left'); ap.add_argument('--right'); ap.add_argument('--text', default='')
    ap.add_argument('--highlight'); ap.add_argument('--sub', default=''); ap.add_argument('--arrow', default='right')
    ap.add_argument('--style', default='split'); ap.add_argument('--at', nargs='+', help='seconds to grab frames at'); ap.add_argument('--left-role', default='the judge')
    ap.add_argument('--right-role', default='the defendant')
    a = ap.parse_args(); d = proj_dir(a.project); os.makedirs(os.path.join(d, 'thumbs'), exist_ok=True)
    if a.cmd == 'frames':
        cmd_frames(d, at=a.at)
    elif a.cmd == 'make':
        if not a.text: sys.exit('--text "2-5 WORD SLANG QUOTE" needed')
        refs = [os.path.abspath(os.path.join(d, p) if not os.path.isabs(p) and not os.path.exists(p) else p) for p in (a.left, a.right) if p]
        ensure_holder()
        pr = prompt_for(a, len(refs) >= 2)
        open(os.path.join(d, 'thumbs', 'last_prompt.txt'), 'w').write(pr)
        tmp = os.path.join(d, 'thumbs', f'raw_{int(time.time())}.png')
        args_ = sum([['--ref', r] for r in refs], []) + ['--out', tmp, pr]
        print('ChatGPT is generating (1-3 min) ...', flush=True)
        print('SAVED', finish(run_tool('gen_one.js', args_), d))
    elif a.cmd == 'fix':
        ensure_holder()
        print('sending correction in the same ChatGPT chat ...', flush=True)
        print('SAVED', finish(run_tool('thumb.js', ['--change', a.note]), d))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
