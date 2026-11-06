#!/usr/bin/env python3
"""Auto B-roll for B-templates — real MOVING footage + images under every narration block.

  python3 tools/autobroll.py <project>            # fetch clips/images for every block + write beats
  python3 tools/autobroll.py <project> --news     # also real news-report clips about the case (YouTube)
  python3 tools/autobroll.py <project> --force    # rebuild beats even where you wrote them by hand

Write in script.json for EVERY vo block (hook, p1.., outro) 2-4 search terms of what the narration talks about:
   "broll_q": ["detroit police traffic stop", "michigan driver license card", "judge gavel courtroom"]
and once for the project (with --news):  "news_q": "Destiny Graves sovereign citizen Detroit court"
Each block then gets ~1 beat per 5 s of narration, mixed: stock VIDEO, hearing replay (court), photo, news clip,
collage, docs you wrote. At least half the beats MOVE (video/news/court). Images stay STILL (owner rule).
Your own hand-made beats (doc/article/charge/timeline...) are kept and the auto beats are added around them.
broll_q = PLACES and THINGS (city skyline, police car, license card, courthouse, documents) — NEVER "sovereign citizen
man" / "judge" / "defendant": a random face looks like the real person (misleading). Real people = only `court`/`frame` beats.
LOOK at research/broll_sheet.jpg after: wrong place / wrong person / off-topic -> delete the file and run again.
Needs PEXELS_API_KEY (videos) and SERPER_API_KEY (images) in config.env — both free.
"""
import glob, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import proj_dir, load_json, save_json, dur
from PIL import Image, ImageDraw, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
MOVING = ('broll', 'court', 'news')


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:50]


def research(proj, *args):
    subprocess.run([sys.executable, os.path.join(HERE, 'research.py'), proj, *args])


def first_frame(path):
    if path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        return Image.open(path).convert('RGB')
    jpg = path[:-4] + '.jpg'
    if not os.path.exists(jpg):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '2', '-i', path, '-frames:v', '1', '-q:v', '4', jpg])
    return Image.open(jpg).convert('RGB') if os.path.exists(jpg) else Image.new('RGB', (320, 180), (60, 0, 0))


def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    proj = a[0]; news = '--news' in a; force = '--force' in a
    d = proj_dir(proj); R = os.path.join(d, 'research'); os.makedirs(R, exist_ok=True)
    sp = os.path.join(d, 'script.json'); S = load_json(sp)
    shutil.copy(sp, os.path.join(d, 'script.before-autobroll.json'))
    info = S.get('info', {})

    newsclips = []
    if news:
        q = S.get('news_q') or ' '.join(x for x in (info.get('case_title'), info.get('court'), 'news') if x)
        research(proj, 'newsclip', q, '--n', '3')
        newsclips = sorted(glob.glob(os.path.join(R, 'clips', slug(q) + '-*.mp4')))
    credits = {}
    for e in load_json(os.path.join(R, 'sources.json'), []):
        credits[e.get('file')] = e.get('credit', '')

    sheet, ni = [], 0
    for v in S['vo']:
        qs = v.get('broll_q') or []
        if not qs:
            qs = [x for x in (info.get('charge'), 'courtroom judge gavel') if x]
            print(f"[{v['id']}] no broll_q — using generic {qs}. Write specific broll_q for better clips!")
        vids, imgs = [], []
        for q in qs:
            if not glob.glob(os.path.join(R, 'broll', slug(q) + '-*.mp4')): research(proj, 'broll', q, '--n', '2')
            if not glob.glob(os.path.join(R, 'img', slug(q) + '-*')): research(proj, 'images', q, '--n', '2')
            vids += sorted(glob.glob(os.path.join(R, 'broll', slug(q) + '-*.mp4')))
            imgs += sorted(f for f in glob.glob(os.path.join(R, 'img', slug(q) + '-*')) if not f.endswith('.txt'))
        p = os.path.join(d, 'vo', v['id'] + '.mp3')
        dd = dur(p) if os.path.exists(p) else len(v['text'].split()) / 2.6
        n = max(3, round(dd / 5))
        hand = [] if force else [b for b in v.get('beats', []) if b.get('type') not in MOVING + ('photo', 'collage')]
        src_t = float(v.get('at', v.get('broll', 0)))
        pool = {'broll': list(vids), 'photo': list(imgs), 'news': newsclips[ni:ni + 1]}
        if pool['news']: ni += 1
        pattern = ['broll', 'court', 'photo', 'broll', 'news', 'collage', 'broll', 'court', 'photo']
        beats, k, ci = [], 0, 0
        while len(beats) + len(hand) < n and k < 40:
            kind = pattern[k % len(pattern)]; k += 1
            if kind == 'broll' and pool['broll']:
                f = pool['broll'].pop(0); beats.append(dict(type='broll', file=os.path.relpath(f, R)))
            elif kind == 'news' and pool['news']:
                f = pool['news'].pop(0); ch = credits.get(os.path.relpath(f, R), '')
                beats.append(dict(type='broll', file=os.path.relpath(f, R), caption=('SOURCE: ' + ch) if ch else 'NEWS REPORT'))
            elif kind == 'photo' and pool['photo']:
                f = pool['photo'].pop(0); beats.append(dict(type='photo', image=os.path.relpath(f, R)))
            elif kind == 'collage' and len(pool['photo']) >= 3:
                beats.append(dict(type='collage', images=[os.path.relpath(pool['photo'].pop(0), R) for _ in range(3)]))
            elif kind == 'court':
                beats.append(dict(type='court', t=max(0.0, src_t - 8 * ci))); ci += 1
            elif not any(pool.values()) and k > len(pattern):
                beats.append(dict(type='court', t=max(0.0, src_t - 8 * ci))); ci += 1
        # hand-made beats (docs, charge, timeline...) go in the middle; the block opens on moving footage
        mid = len(beats) // 2
        v['beats'] = beats[:1] + hand + beats[1:] if hand else beats[:mid] + beats[mid:]
        mv = sum(b['type'] in MOVING for b in v['beats'])
        print(f"[{v['id']}] {dd:.0f}s -> {len(v['beats'])} beats ({mv} moving, {len(hand)} hand-made)")
        for i, b in enumerate(v['beats']):
            f = b.get('file') or b.get('image') or (b.get('images') or [None])[0]
            if f: sheet.append((f"{v['id']}:{i} {b['type']}", os.path.join(R, f)))
    save_json(S, sp)

    cols, tw, th = 5, 384, 216; rows = max(1, (len(sheet) + cols - 1) // cols)
    im = Image.new('RGB', (cols * tw, rows * (th + 30)), (15, 15, 15)); dr = ImageDraw.Draw(im)
    for i, (lab, f) in enumerate(sheet):
        x, y = (i % cols) * tw, (i // cols) * (th + 30)
        try: im.paste(ImageOps.fit(first_frame(f), (tw - 6, th)), (x + 3, y))
        except Exception: pass
        dr.text((x + 6, y + th + 6), lab[:48], fill=(255, 220, 0))
    out = os.path.join(R, 'broll_sheet.jpg'); im.save(out, quality=85)
    print('saved script.json (backup: script.before-autobroll.json)\nLOOK:', out)
    print('NEXT: python3 tools/build.py', proj, '--template B05   (or any B template)')


if __name__ == '__main__':
    main()
