#!/usr/bin/env python3
"""Step 3 — detect the camera tiles of the court stream and where to crop.

  python3 tools/layout.py <project>

Court streams are Zoom-style grids on black: 1 camera (full screen), 2 cameras side by side, or
3+ tiles (e.g. two on top + one below). Uploaders also put text in the black bars. This finds the
camera tiles in every part of the video (the grid changes when people join/leave) and saves:
  layout.json  {"layouts": {"L0": {"tiles": [[x,y,w,h], ...]}, ...}, "modes": [["L0", start, end], ...]}
  layout_check.jpg  one frame per layout with the crop boxes in red — OPEN IT AND CHECK.
If a box is wrong, edit layout.json by hand (source-video pixels) and re-run build.py.
How tiles are used: 1 -> full-screen frame · 2 -> side-by-side strip · 3+ -> strip of the first two
+ the third as a small picture-in-picture in the corner of the right camera.
"""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from common import proj_dir, video_size, save_json, dur

name = sys.argv[1]
d = proj_dir(name)
src = os.path.join(d, 'src.mp4')
SW, SH = video_size(src)
w, h, RATE = 960, 540, 1
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-vf', f'fps={RATE},scale={w}:{h}:flags=neighbor,format=gray',
                      '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
A = np.frombuffer(raw, np.uint8).reshape(-1, h, w)
T = len(A)
from scipy import ndimage


def segs_where(mask1d, minlen):
    out, st = [], None
    for i, m in enumerate(list(mask1d) + [False]):
        if m and st is None: st = i
        if not m and st is not None:
            if i - st >= minlen: out.append([st, i])
            st = None
    return out


def change_points(prof, jump=0.3, k=4):
    """indices where a fill profile steps up/down sharply (tile edges without a black gap)."""
    pts = []
    for i in range(k, len(prof) - k):
        if abs(prof[i + k] - prof[i - k]) > jump and (not pts or i - pts[-1] > 2 * k):
            pts.append(i)
    return pts


def split_by(span, pts, minlen):
    a, b = span; cuts = [a] + [p for p in pts if a + minlen < p < b - minlen] + [b]
    return [[cuts[i], cuts[i + 1]] for i in range(len(cuts) - 1) if cuts[i + 1] - cuts[i] >= minlen]


def seam_split(fr, box, depth=0):
    """Split a block of touching Zoom tiles along straight seams that cross the WHOLE block
    (median edge strength), recursively. A real camera rarely has such a full-width line."""
    x0, y0, x1, y1 = box
    if depth > 3 or (x1 - x0) < 0.15 * w or (y1 - y0) < 0.15 * h:
        return [box]
    blk = fr[y0:y1, x0:x1].astype(np.float32)
    best = None
    for axis in (1, 0):                                  # 1: vertical seam (columns), 0: horizontal seam (rows)
        D = np.median(np.abs(np.diff(blk, axis=axis)), axis=1 - axis if axis == 0 else 0)
        n = len(D)
        for frac in (1 / 3, 1 / 2, 2 / 3):              # Zoom grids split at halves / thirds only
            lo, hi = int((frac - 0.025) * n), int((frac + 0.025) * n) + 1
            k = lo + int(np.argmax(D[lo:hi]))
            score = D[k] / (np.median(D) + 1)
            if D[k] > 14 and score > 6 and (best is None or score > best[0]):
                best = (score, axis, k)
    if not best:
        return [box]
    _, axis, k = best
    if axis == 1:
        parts = [(x0, y0, x0 + k, y1), (x0 + k + 1, y0, x1, y1)]
    else:
        parts = [(x0, y0, x1, y0 + k), (x0, y0 + k + 1, x1, y1)]
    return [b for p in parts for b in seam_split(fr, p, depth + 1)]


def tiles_of(fr):
    """Camera tiles in one gray frame -> list of (x0,y0,x1,y1).
    XY-cut on the non-black mask: horizontal bands (split where row fill jumps, e.g. a narrower tile
    below two wide ones), then tiles inside each band (split on black gaps / fill jumps, and a too-wide
    block of touching cameras is split at its strongest vertical edge)."""
    mask = fr > 20
    rf = np.convolve(mask.mean(axis=1), np.ones(5) / 5, mode='same')
    rr, cc = mask.mean(axis=1)[int(0.02 * h):int(0.98 * h)], mask.mean(axis=0)[int(0.02 * w):int(0.98 * w)]
    if (rr < 0.1).sum() == 0 and (cc < 0.1).sum() == 0:              # (ignore 1-2 px black padding at edges)
        # no black line anywhere: one camera filling the frame, or Zoom tiles touching each other
        def trim(b):                                    # drop black margins inside a piece
            x0, y0, x1, y1 = b; sub = mask[y0:y1, x0:x1]
            cs = np.where(sub.mean(axis=0) > 0.3)[0]; rs = np.where(sub.mean(axis=1) > 0.3)[0]
            return (x0 + cs[0], y0 + rs[0], x0 + cs[-1] + 1, y0 + rs[-1] + 1) if len(cs) and len(rs) else None
        grid = [t for t in (trim(b) for b in seam_split(fr, (0, 0, w, h))) if t and (t[2] - t[0]) * (t[3] - t[1]) >= 0.03 * w * h]
        if len(grid) < 2 or not all(1.2 <= (b[2] - b[0]) / max(1, b[3] - b[1]) <= 2.2 for b in grid):
            return [(0, 0, w, h)]                       # pieces are not camera-shaped -> it was one camera
        big = sorted(grid, key=lambda t: -(t[2] - t[0]) * (t[3] - t[1]))
        top = sorted([t for t in grid if t[1] < 0.1 * h], key=lambda t: t[0])
        pair = top[:2] if len(top) >= 2 else big[:2]
        return pair + [t for t in big if t not in pair][:7]
    bands = []
    for sp in segs_where(rf > 0.05, int(0.12 * h)):
        bands += split_by(sp, change_points(rf[sp[0]:sp[1]], 0.25) and [sp[0] + q for q in change_points(rf[sp[0]:sp[1]], 0.25)], int(0.12 * h))
    out = []
    for r0, r1 in bands:
        cf = np.convolve(mask[r0:r1].mean(axis=0), np.ones(5) / 5, mode='same')
        for c0, c1 in segs_where(cf > 0.5, int(0.12 * w)):
            rr = segs_where(mask[r0:r1, c0:c1].mean(axis=1) > 0.5, int(0.1 * h))
            if not rr: continue
            y0, y1 = r0 + rr[0][0], r0 + rr[-1][1]
            if (c1 - c0) / max(1, y1 - y0) > 2.4:             # two touching cameras
                E = np.abs(np.diff(fr[y0:y1, c0:c1].astype(np.float32), axis=1)).mean(axis=0)
                lo, hi = int(0.35 * (c1 - c0)), int(0.65 * (c1 - c0))
                xs = c0 + lo + int(np.argmax(E[lo:hi]))
                parts = [(c0, xs), (xs + 1, c1)] if E[xs - c0] > 3 * np.median(E) else [(c0, c1)]
            else:
                parts = [(c0, c1)]
            for x0, x1 in parts:
                bw, bh = x1 - x0, y1 - y0
                if bw * bh >= 0.012 * w * h and 0.4 <= bw / bh <= 2.6:
                    out.append((x0, y0, x1, y1))
    # main cameras = the row that holds two tiles (left->right); everything else -> picture-in-picture
    rows = {}
    for t in out: rows.setdefault(t[1] // int(0.1 * h), []).append(t)
    def good(pr):
        (a0, a1, a2, a3), (b0, b1, b2, b3) = pr
        return min(a2 - a0, b2 - b0) >= 0.3 * w and 0.8 <= (a3 - a1) / max(1, b3 - b1) <= 1.25
    pair = next((p for p in (sorted(r, key=lambda t: t[0])[:2] for k, r in sorted(rows.items()) if len(r) >= 2)
                 if good(p)), None)
    fills = (rf > 0.05).mean() >= 0.8 and (mask.mean(axis=0) > 0.05).mean() >= 0.85
    if not pair and fills and all((t[3] - t[1]) >= 0.75 * h for t in out):   # frame is filled edge to edge
        grid = [b for b in seam_split(fr, (0, 0, w, h)) if (b[2] - b[0]) * (b[3] - b[1]) >= 0.03 * w * h]
        if len(grid) < 2:
            return [(0, 0, w, h)]                       # one camera
        out = grid                                      # touching Zoom tiles
        rows = {}
        for t in out: rows.setdefault(t[1] // int(0.1 * h), []).append(t)
        pair = next((p for p in (sorted(r, key=lambda t: t[0])[:2] for k, r in sorted(rows.items()) if len(r) >= 2)
                     if good(p)), None)
    rest = sorted([t for t in out if not pair or t not in pair], key=lambda t: -(t[2] - t[0]) * (t[3] - t[1]))
    return ((pair or []) + rest)[:9]                # main pair first (left->right), then others by size


def sig(ts):
    return tuple(tuple(v // 40 for v in t) for t in ts)


sigs = [sig(tiles_of(A[i])) for i in range(T)]
segs = []
for i, s in enumerate(sigs):
    if segs and segs[-1][0] == s: segs[-1][2] = i + 1
    else: segs.append([s, i, i + 1])
merged = []
for s in segs:
    if merged and (s[2] - s[1] < 4 * RATE or merged[-1][0] == s[0]): merged[-1][2] = s[2]
    else: merged.append(s)
segs = merged

inset = 0.015
def to_src(t, full_frame=False):
    x0, y0, x1, y1 = t[0] * SW / w, t[1] * SH / h, t[2] * SW / w, t[3] * SH / h
    if full_frame:                                   # one camera filling the frame: trim uploader text bands
        y0 = max(y0, SH * 0.08); x0 = max(x0, SW * 0.04); x1 = min(x1, SW * 0.96)
    dx, dy = (x1 - x0) * inset, (y1 - y0) * inset
    x0, x1, y0, y1 = x0 + dx, x1 - dx, y0 + dy, y1 - dy
    bw, bh = x1 - x0, y1 - y0
    return [int(x0) // 2 * 2, int(y0) // 2 * 2, int(bw) // 2 * 2, int(bh) // 2 * 2]

layouts, modes, raw_boxes = {}, [], {}
for s, a0, a1 in segs:
    boxes = [tiles_of(A[k]) for k in range(a0, a1)]
    boxes = [b for b in boxes if sig(b) == s] or boxes
    n = min(len(b) for b in boxes) if boxes else 0
    med = [tuple(int(np.median([b[i][j] for b in boxes if len(b) > i])) for j in range(4)) for i in range(n)]
    if not med: med = [(0, 0, w, h)]
    # reuse an existing layout when the tiles are (almost) the same
    lid = next((k for k, m in raw_boxes.items() if len(m) == len(med) and
                all(abs(p - q) <= 0.04 * w for t1, t2 in zip(m, med) for p, q in zip(t1, t2))), None)
    if lid is None:
        full = len(med) == 1 and (med[0][3] - med[0][1]) >= 0.8 * h
        lid = f'L{len(layouts)}'; raw_boxes[lid] = med
        layouts[lid] = {'tiles': [to_src(t, full) for t in med]}
    modes.append([lid, round(a0 / RATE, 2), round(a1 / RATE, 2)])
modes[-1][2] = round(dur(src), 2)
# merge consecutive equal ids
mm = []
for m in modes:
    if mm and mm[-1][0] == m[0]: mm[-1][2] = m[2]
    else: mm.append(m)

# ---------------------------------------------------------------- active speaker (Zoom green border)
def green_score(fr, tile):
    """how much of the thin line just outside the tile's top/bottom edge is Zoom-green."""
    x, y, w_, h_ = tile; pad = int(0.02 * max(w_, h_)) + 4
    best = 0.0
    for band in (fr[max(0, y - pad):y + 2, x:x + w_], fr[y + h_ - 2:min(SH, y + h_ + pad), x:x + w_]):
        if band.size == 0: continue
        g = (band[..., 1] > 60) & (band[..., 1] - np.maximum(band[..., 0], band[..., 2]) > 30)
        best = max(best, g.mean(axis=1).max() if len(g) else 0)
    return best

speakers = []
proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-vf', 'fps=1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                        stdout=subprocess.PIPE)
sec = 0
while True:
    buf = proc.stdout.read(SW * SH * 3)
    if len(buf) < SW * SH * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3).astype(np.int16)
    lid = next((m[0] for m in mm if m[1] <= sec < m[2]), mm[-1][0])
    tiles = layouts[lid]['tiles']
    sc = [green_score(fr, t) for t in tiles] if len(tiles) >= 2 else []
    act = int(np.argmax(sc)) if sc and max(sc) > 0.35 else -1
    if speakers and speakers[-1][2] == act and speakers[-1][1] == sec: speakers[-1][1] = sec + 1
    else: speakers.append([sec, sec + 1, act])
    sec += 1
proc.wait()
# drop flicker < 3 s
clean = []
for s_ in speakers:
    if clean and (s_[1] - s_[0] < 3 or clean[-1][2] == s_[2]): clean[-1][1] = s_[1]
    else: clean.append(s_)

lay = {'size': [SW, SH], 'layouts': layouts, 'modes': mm}
# only trust it if the green border really moves between tiles (some streams keep it on the room mic)
lay['speakers'] = clean if len({k for a, b, k in clean if k >= 0}) >= 2 else []   # [start, end, tile] from the Zoom green border

save_json(lay, os.path.join(d, 'layout.json'))

shots = []
for lid, L in layouts.items():
    seg = max((m for m in mm if m[0] == lid), key=lambda m: m[2] - m[1])
    t = (seg[1] + seg[2]) / 2
    p = os.path.join(d, f'_chk.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', src, '-frames:v', '1', p], check=True)
    im = Image.open(p).convert('RGB'); dr = ImageDraw.Draw(im)
    for k, b in enumerate(L['tiles']):
        dr.rectangle([b[0], b[1], b[0] + b[2], b[1] + b[3]], outline=(255, 0, 0), width=6)
        dr.text((b[0] + 12, b[1] + 8), f'{k + 1}', fill=(255, 0, 0))
    tot = sum(m[2] - m[1] for m in mm if m[0] == lid)
    dr.text((16, 12), f'{lid}: {len(L["tiles"])} tile(s), {tot / 60:.1f} min on screen', fill=(255, 255, 0))
    shots.append(im.resize((960, int(960 * SH / SW)))); os.remove(p)
sheet = Image.new('RGB', (960, sum(s.height for s in shots)))
y = 0
for s in shots: sheet.paste(s, (0, y)); y += s.height
sheet.save(os.path.join(d, 'layout_check.jpg'), quality=85)
for lid, L in layouts.items():
    tot = sum(m[2] - m[1] for m in mm if m[0] == lid)
    print(f'{lid}: {len(L["tiles"])} tile(s)  {tot / 60:.1f} min')
act_t = sum(b - a for a, b, k in clean if k >= 0)
print(f'active speaker known for {act_t / 60:.1f} min ({len(clean)} switches)')
print(f'{len(mm)} layout switches. CHECK: {os.path.join(d, "layout_check.jpg")}')
print('NEXT: write script.json, then python3 tools/voice.py', name)
