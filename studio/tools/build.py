#!/usr/bin/env python3
"""Step 6 — assemble the edit for one template -> project_T##.json (and print the final length).

  python3 tools/build.py <project> --template T05          # build
  python3 tools/build.py <project> --template T05 --dry    # only print the length estimate

Timeline (same as the competitors + the CapCut tutorial):
  cold open (best 15-30 s clip, real audio) -> hook narration -> hearing with commentary blocks
  inserted at script "at" times -> outro narration.
During every narration the footage that leads up to that moment plays at 0.5x with court audio muted
(templates may also turn it black & white, or punch in full screen on one camera).
Dead air longer than "auto_trim" seconds (default 2.5) is cut; "skip" ranges are removed completely.
The template decides where each camera tile goes (tools/layouts.py), for 1, 2, 3+ cameras.
"""
import argparse, hashlib, json, os, subprocess, sys, textwrap
sys.path.insert(0, os.path.dirname(__file__))
from common import proj_dir, load_json, save_json, dur, load_template, h264_args, FPS, W, H
from layouts import plan

ap = argparse.ArgumentParser()
ap.add_argument('project'); ap.add_argument('--template', default='T01'); ap.add_argument('--dry', action='store_true')
a = ap.parse_args()
d = proj_dir(a.project)
S = load_json(os.path.join(d, 'script.json'))
L = load_json(os.path.join(d, 'layout.json'))
TX = load_json(os.path.join(d, 'tx.json'))
T = load_template(a.template)
tid = T['id'].split('-')[0]
src = os.path.join(d, 'src.mp4')
f = lambda s: int(round(s * FPS))

# ---------------------------------------------------------------- crops (one file per camera tile, native aspect)
rects = []
for Lx in L['layouts'].values():
    for r in Lx['tiles']:
        if r not in rects: rects.append(r)
CROP = {tuple(r): os.path.join(d, 'crop_' + hashlib.md5(json.dumps(r).encode()).hexdigest()[:8] + '.mp4') for r in rects}
AUD = os.path.join(d, 'audio.m4a')
todo = [r for r in rects if not os.path.exists(CROP[tuple(r)])]
if not a.dry and todo:
    print(f'encoding {len(todo)} camera crop(s) (one time) ...', flush=True)
    fc = [f'[0:v]split={len(todo)}' + ''.join(f'[i{k}]' for k in range(len(todo)))]
    outs = []
    for k, (x, y, w, h) in enumerate(todo):
        sc = 'scale=1600:-2' if w / h > 16 / 9 else 'scale=-2:900'
        fc.append(f'[i{k}]crop={w}:{h}:{x}:{y},{sc}[o{k}]')
        outs += ['-map', f'[o{k}]', '-an', *h264_args('7M'), CROP[(x, y, w, h)]]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-filter_complex', ';'.join(fc), *outs], check=True)
if not a.dry and not os.path.exists(AUD):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-c:a', 'aac', '-b:a', '192k', AUD], check=True)

# ---------------------------------------------------------------- overlays (RVE-style project)
ov, _id = [], [0]
def nid(): _id[0] += 1; return _id[0]
def base(t, a0, b0, row, x, y, w, h):
    return dict(id=nid(), type=t, **{'from': f(a0)}, durationInFrames=max(1, f(b0) - f(a0)), row=row,
                left=int(x), top=int(y), width=int(w), height=int(h), isDragging=False, rotation=0)

def shape(a0, b0, x, y, w, h, color, row=3):
    o = base('shape', a0, b0, row, x, y, w, h); o.update(content='rectangle', styles=dict(fill=color, opacity=1)); ov.append(o)

def text(a0, b0, key, content, x, y, an, size, color):
    o = base('text', a0, b0, 2, x, y, 0, 0)
    o.update(content=content, styles=dict(key=key, an=an, fontSize=size, color=color, fontFamily=T.get('text_font', 'Arial Black')))
    ov.append(o)

def sound(path, a0, b0, start, row):
    o = base('sound', a0, b0, row, 0, 0, 0, 0)
    o.update(content=os.path.basename(path), src=path, startFromSound=f(start), styles=dict(volume=1.0)); ov.append(o)

INFO = dict(panel_head=T.get('panel_head', 'CASE FILE'), ticker_tag=T.get('ticker_tag', 'COURT'), vs='VS', letterbox_tag='',
            title=S.get('title', ''))
INFO.update(S.get('info', {}))
LABELS = S.get('labels', {})                     # {"L1": ["JUDGE SIMPSON", "COURTROOM", "PROSECUTOR"]}
capzones = []                                    # (start_s, end_s, cap-dict) -> caption position per moment

def wrap(s, n=22):
    return '\\N'.join(textwrap.wrap(s, n)) if s else ''

def pieces(a0, b0):
    out = []
    for m, ma, mb in L['modes']:
        lo, hi = max(a0, ma), min(b0, mb)
        if hi - lo > 0.04: out.append((m, lo, hi))
    return out

FOCUS = [tuple(x) for x in S.get('focus', [])]            # [[src_start, src_end, tile], ...] full-screen one camera
if T.get('speaker_follow') and not FOCUS:
    FOCUS = [tuple(x) for x in L.get('speakers', []) if x[2] >= 0 and x[1] - x[0] >= 4]
NOTES = sorted([tuple(x) for x in S.get('notes', [])])     # [[src_time, "text"], ...] for the law panel

def note_at(sec):
    cur = ''
    for t0, txt in NOTES:
        if t0 <= sec: cur = txt
    return cur

def focus_at(sec):
    return next((k for a0, b0, k in FOCUS if a0 <= sec < b0), None)

def place(t, t2, lid, pa, speed, mode, focus=None, note=''):
    tiles = L['layouts'][lid]['tiles']
    labels = LABELS.get(lid, S.get('labels_default', []))
    if focus is not None and focus < len(tiles):           # one camera full-frame (speaker follow / Claude's focus)
        tiles = [tiles[focus]]; labels = [labels[focus]] if focus < len(labels) else []
    p = plan(T, len(tiles), mode)
    vo = mode == 'vo'
    for s in p['slots']:
        if s['tile'] >= len(tiles): continue
        tile = tiles[s['tile']]; x, y, w, h = s['rect']
        if s.get('shadow'):
            shape(t, t2, x + 14, y + 18, w, h, '#000000@0.45', row=6)
        o = base('video', t, t2, 5, x, y, w, h)
        ta, sa = tile[2] / tile[3], w / h
        fit = 'cover' if (T.get('force_cover') or 0.8 <= ta / sa <= 1.25) else 'contain'
        o.update(content=CROP[tuple(tile)], src=CROP[tuple(tile)], videoStartTime=round(pa, 3), speed=speed,
                 styles=dict(objectFit=fit, volume=0, opacity=1, zoom=s.get('zoom', 1.0),
                             gray=bool(vo and T.get('vo_style') in ('bw', 'focus_bw'))))
        ov.append(o)
        if s.get('border'):
            bw_, bc = s['border']
            for bx in [(x - bw_, y - bw_, w + 2 * bw_, bw_), (x - bw_, y + h, w + 2 * bw_, bw_), (x - bw_, y, bw_, h), (x + w, y, bw_, h)]:
                shape(t, t2, *bx, bc)
        if s.get('label') and T.get('name_tags') and s['tile'] < len(labels) and labels[s['tile']]:
            lx, ly, an = s['label']
            text(t, t2, 'label', labels[s['tile']].upper(), lx, ly, an, T.get('tag_size', 30), T.get('tag_color', '#FFFFFF'))
    for bx in p['boxes']: shape(t, t2, *bx)
    for tx in p['texts']:
        k = tx['key']
        if k.startswith('label'):
            val = labels[int(k[-1])] if int(k[-1]) < len(labels) else ''
        elif k == 'note':
            val = note
        else:
            val = INFO.get(k, '')
        if val:
            txt = val if k == 'note' else val.upper()
            text(t, t2, k, wrap(txt, 24 if k == 'note' else 26) if tx.get('wrap') else txt, tx['x'], tx['y'], tx['an'], tx['size'], tx['color'])
    capzones.append((t, t2, p['cap']))

def footage(t, a0, b0, speed=1.0, mode='normal'):
    for m, pa, pb in pieces(a0, b0):
        # sub-split at focus / note boundaries so the layout can change mid-piece
        pts = sorted({pa, pb} | {x for f_ in FOCUS for x in f_[:2] if pa < x < pb} | {x for x, _ in NOTES if pa < x < pb})
        for qa, qb in zip(pts, pts[1:]):
            if qb - qa < 0.04: continue
            t2 = t + (qb - qa) / speed
            place(t, t2, m, qa, speed, mode, focus=focus_at(qa + 0.01) if mode == 'normal' else None, note=note_at(qa + 0.01))
            t = t2
    return t

caps = []
def court_words(t, a0, b0):
    for s in TX:
        for w0, w1, w in s['w']:
            if a0 <= w0 < b0: caps.append((t + w0 - a0, t + min(w1, b0) - a0, w.strip()))

skips = [tuple(x) for x in S.get('skip', [])]
if S.get('keep'):                                   # main points only: everything outside "keep" ranges is cut
    k_ = sorted(tuple(x) for x in S['keep']); h0_, h1_ = S['hearing']; prev = h0_
    for ka, kb in k_:
        if ka > prev: skips.append((prev, ka))
        prev = max(prev, kb)
    if prev < h1_: skips.append((prev, h1_))
thr = S.get('auto_trim', 2.5)
if thr:
    ws = [w for s in TX for w in s['w']]
    for (p0, p1, _), (n0, _, _) in zip(ws, ws[1:]):
        if n0 - p1 > thr: skips.append((p1 + 0.4, n0 - 0.4))

t = 0.0
def clip(a0, b0, tag=None):
    global t
    t_start = t
    parts = [(a0, b0)]
    for sa, sb in skips:
        parts = [q for pa, pb in parts for q in ((pa, min(pb, sa)), (max(pa, sb), pb)) if q[1] - q[0] > 0.05]
    for pa, pb in parts:
        sound(AUD, t, t + pb - pa, pa, 7)
        court_words(t, pa, pb)
        t = footage(t, pa, pb)
    if tag: text(t_start, t, 'tag', tag, 60, 50, 7, T.get('tag_big', 54), T.get('tag_color', '#FFD000'))

# ---------------------------------------------------------------- B-roll beats (research visuals during narration)
import beats as B
SKIN = dict(T.get('skin', {}))
if SKIN.get('bg'): SKIN['bg_path'] = os.path.join(T['dir'], SKIN['bg'])
BEATDIR = os.path.join(d, 'beats'); os.makedirs(BEATDIR, exist_ok=True)
MUSIC = os.path.join(os.path.dirname(T['dir']), '..', 'assets', 'music', T['music']) if T.get('music') else None

def resolve(pth):
    if not pth: return pth
    for base_ in (os.path.join(d, 'research'), d):
        q = os.path.join(base_, pth)
        if os.path.exists(q): return q
    return pth

def frame_image(bt):
    """still of one camera at a hearing time (the defendant's 'photo')."""
    tt = float(bt['t']); lid = next((m for m, a0, b0 in L['modes'] if a0 <= tt < b0), L['modes'][-1][0])
    tiles = L['layouts'][lid]['tiles']; x, y, w, h = tiles[min(bt.get('tile', 0), len(tiles) - 1)]
    out = os.path.join(BEATDIR, f"frame_{tt:.1f}_{bt.get('tile', 0)}.jpg")
    if not os.path.exists(out):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{tt:.2f}', '-i', src, '-frames:v', '1',
                        '-vf', f'crop={w}:{h}:{x}:{y}', '-q:v', '2', out], check=True)
    return out

def beat_clip(bt, dd, hl_at):
    bt = dict(bt)
    for k_ in ('image', 'file'):
        if bt.get(k_): bt[k_] = resolve(bt[k_])
    if bt.get('images'): bt['images'] = [resolve(x) for x in bt['images']]
    if bt['type'] == 'frame': bt['image'] = frame_image(bt)
    key = hashlib.md5(json.dumps([bt, SKIN, round(dd, 2), round(hl_at or -1, 2), T['id']], sort_keys=True).encode()).hexdigest()[:12]
    out = os.path.join(BEATDIR, f"{bt['type']}_{key}.mp4")
    if not a.dry and not os.path.exists(out):
        B.render(bt, SKIN, out, dd, hl_at=hl_at)
    return out

def word_time(words, phrase, after=0.0):
    norm = lambda x: ''.join(ch for ch in x.lower() if ch.isalnum())
    pw = [norm(p_) for p_ in phrase.split() if norm(p_)]
    ws = [(w0, norm(w)) for w0, w1, w in words]
    for i in range(len(ws) - len(pw) + 1):
        if ws[i][0] >= after - 0.05 and [x for _, x in ws[i:i + len(pw)]] == pw:
            return ws[i][0]
    return None

VOTX = load_json(os.path.join(d, 'vo_tx.json'), {})
def narration(v, src_end):
    global t
    p = os.path.join(d, 'vo', v['id'] + '.mp3'); dd = dur(p)
    sound(p, t, t + dd, 0, 8)
    if MUSIC and os.path.exists(MUSIC):
        o = base('sound', t, t + dd, 9, 0, 0, 0, 0)
        o.update(content='music', src=os.path.abspath(MUSIC), startFromSound=0,
                 styles=dict(volume=T.get('music_vol', 0.12), loop=True, fadeIn=0.8, fadeOut=1.2)); ov.append(o)
    words = VOTX.get(v['id'], [])
    for w0, w1, w in words: caps.append((t + w0, t + w1, w.strip()))
    bl = v.get('beats') if T.get('broll') else None
    if not bl:
        footage(t, max(0.0, src_end - dd * 0.5), src_end, speed=0.5, mode='vo')
    else:
        # beat start times: "at" phrase in the narration, otherwise evenly spaced
        starts = []
        for i, bt in enumerate(bl):
            st = word_time(words, bt['at'], starts[-1] if starts else 0) if bt.get('at') else None
            starts.append(st if st is not None else dd * i / len(bl))
        starts[0] = 0.0
        for i in range(1, len(starts)): starts[i] = max(starts[i], starts[i - 1] + 2.5)
        for i, bt in enumerate(bl):
            s0 = starts[i]; s1 = starts[i + 1] if i + 1 < len(bl) else dd
            if s1 - s0 < 0.5: continue
            if bt['type'] == 'court':                       # hearing footage inside narration (B&W/slow per template)
                ce = float(bt.get('t', src_end)); footage(t + s0, max(0.0, ce - (s1 - s0) * 0.5), ce, speed=0.5, mode='vo')
                continue
            hl = None
            if bt.get('highlight'):
                ht = word_time(words, bt['highlight'][0], s0)
                hl = (ht - s0) if ht is not None and ht < s1 else None
            path = beat_clip(bt, s1 - s0, hl)
            o = base('video', t + s0, t + s1, 5, 0, 0, W, H)
            o.update(content=path, src=path, videoStartTime=0, speed=1.0, styles=dict(objectFit='cover', volume=0, opacity=1))
            ov.append(o)
            capzones.append((t + s0, t + s1, dict(y=H - 70, align='center', x=60)))
    if T.get('vo_tag'): text(t, t + dd, 'tag', T['vo_tag'], 60, 50, 7, T.get('tag_big', 54), T.get('tag_color', '#FFD000'))
    t += dd

vos = S['vo']
hook = next((v for v in vos if v['id'] == 'hook'), None)
outro = next((v for v in vos if v['id'] == 'outro'), None)
mids = sorted([v for v in vos if 'at' in v and v['id'] not in ('hook', 'outro')], key=lambda v: v['at'])
HL = [tuple(x) for x in S.get('highlights', [])] or ([tuple(S['cold_open'])] if S.get('cold_open') else [])
_saved = skips; skips = []                          # highlights are played whole
for i, (ha, hb) in enumerate(HL):                    # hook montage: 2-4 hottest moments back to back
    clip(ha, hb, tag=T.get('cold_tag') if i == 0 else None)
skips = _saved
if hook: narration(hook, hook['broll'] + dur(os.path.join(d, 'vo', 'hook.mp3')) * 0.5)
h0, h1 = S['hearing']
cuts = [h0] + [v['at'] for v in mids] + [h1]
for i in range(len(cuts) - 1):
    clip(cuts[i], cuts[i + 1])
    if i < len(mids): narration(mids[i], cuts[i + 1])
if outro: narration(outro, outro['broll'] + dur(os.path.join(d, 'vo', 'outro.mp3')) * 0.5)

print(f"template {T['id']}: final length {int(t // 60)}:{int(t % 60):02d}  "
      f"({len(mids)} commentary blocks + hook/outro, {len(skips)} cuts)")
if a.dry: sys.exit()

o = base('image', 0, t, 9, 0, 0, W, H)
o.update(src=os.path.join(T['dir'], T['bg']), content='bg', styles=dict(objectFit='cover', opacity=1)); ov.append(o)

caps.sort()
groups, cur, mw = [], [], T['caption'].get('max_words', 4)
for c in caps:
    if cur and (len(cur) >= mw or c[0] - cur[-1][1] > 0.6): groups.append(cur); cur = []
    if c[2]: cur.append(c)
if cur: groups.append(cur)
ms = lambda s: int(round(s * 1000))
captions = [dict(text=' '.join(w for _, _, w in g), startMs=ms(g[0][0]), endMs=max(ms(g[-1][1]), ms(g[0][0]) + 400),
                 timestampMs=None, confidence=None,
                 words=[dict(word=w, startMs=ms(x0), endMs=ms(x1), confidence=1) for x0, x1, w in g]) for g in groups]
o = base('caption', 0, t, 1, 0, 0, W, H)
o.update(captions=captions, styles=T['caption'], zones=[[round(a0, 3), round(b0, 3), c] for a0, b0, c in capzones]); ov.append(o)

proj = dict(overlays=ov, durationInFrames=f(t), fps=FPS, width=W, height=H, template=T['id'])
save_json(proj, os.path.join(d, f'project_{tid}.json'))
print('saved', f'project_{tid}.json', '| NEXT: python3 tools/render.py', a.project, '--template', tid)
