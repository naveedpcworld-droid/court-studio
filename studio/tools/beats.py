"""B-roll beat renderer — turns one narration "beat" from script.json into an MP4 clip (1920x1080 or a
panel size), styled by the template's "skin".

Beat types (fields in script.json -> vo[].beats[]):
  doc        {"title", "subtitle", "text", "highlight": [phrases], "source"}       real document / law excerpt
  article    {"outlet", "date", "headline", "text", "highlight": [...], "image"}   news article card
  photo      {"image", "caption"}                                                  one photo (Ken Burns)
  frame      {"t": seconds, "tile": 0, "caption"}                                  a still from the hearing
  collage    {"images": [...], "caption"}                                          3-4 photos landing one by one
  title      {"text", "sub"}                                                       section / chapter card
  definition {"term", "text", "source"}
  quote      {"text", "by"}
  timeline   {"events": [["Oct 5, 2021", "Arrested for DWI"], ...]}
  charge     {"offense", "law", "penalty"}
  checklist  {"title", "items": [["Sworn statement", true], ["Reason for the stop", false]]}
  broll      {"file"} (video from research.py broll) or {"image"}                  stock footage
Rendered with PIL frame-by-frame and piped into ffmpeg, so it runs the same on Mac and Windows.
"""
import math, os, random, subprocess, textwrap
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance

FPS = 30
FONT_DIRS = ['/System/Library/Fonts/Supplemental', '/System/Library/Fonts', '/Library/Fonts',
             os.path.expanduser('~/Library/Fonts'), 'C:/Windows/Fonts', '/usr/share/fonts/truetype/msttcorefonts',
             '/usr/share/fonts/truetype/dejavu']
FONT_FILES = {
    'Arial Black': ['Arial Black.ttf', 'ariblk.ttf'], 'Arial': ['Arial.ttf', 'arial.ttf'],
    'Arial Bold': ['Arial Bold.ttf', 'arialbd.ttf'], 'Georgia': ['Georgia.ttf', 'georgia.ttf'],
    'Georgia Bold': ['Georgia Bold.ttf', 'georgiab.ttf'], 'Courier New': ['Courier New.ttf', 'cour.ttf'],
    'Courier New Bold': ['Courier New Bold.ttf', 'courbd.ttf'], 'Times New Roman': ['Times New Roman.ttf', 'times.ttf'],
    'Times New Roman Bold': ['Times New Roman Bold.ttf', 'timesbd.ttf'], 'Impact': ['Impact.ttf', 'impact.ttf'],
    'Marker': ['Marker Felt.ttc', 'Noteworthy.ttc', 'segoepr.ttf', 'Comic Sans MS.ttf', 'comic.ttf'],
}
_fc = {}


def font(name, size):
    key = (name, size)
    if key in _fc: return _fc[key]
    for fn in FONT_FILES.get(name, [name]) + FONT_FILES['Arial'] + ['DejaVuSans.ttf']:
        for d in FONT_DIRS:
            p = os.path.join(d, fn)
            if os.path.exists(p):
                try:
                    _fc[key] = ImageFont.truetype(p, size); return _fc[key]
                except OSError:
                    pass
    _fc[key] = ImageFont.load_default(); return _fc[key]


def rgb(c, a=255):
    c = c.lstrip('#'); return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), a)


def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- text layout with phrase highlights
def wrap_words(draw, text, fnt, width):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=fnt) <= width: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


def layout_text(draw, text, fnt, width, x, y, lh):
    """-> list of (word, x0, y0, x1) positions and final y."""
    out = []
    for line in wrap_words(draw, text, fnt, width):
        cx = x
        for w in line.split():
            ww = draw.textlength(w, font=fnt)
            out.append((w, cx, y, cx + ww)); cx += ww + draw.textlength(' ', font=fnt)
        y += lh
    return out, y


def phrase_spans(words, phrases):
    """word index ranges that match each highlight phrase (case/punct insensitive)."""
    norm = lambda s: ''.join(ch for ch in s.lower() if ch.isalnum())
    ws = [norm(w[0]) for w in words]; spans = []
    for ph in phrases or []:
        pw = [norm(p) for p in ph.split() if norm(p)]
        for i in range(len(ws) - len(pw) + 1):
            if ws[i:i + len(pw)] == pw: spans.append((i, i + len(pw))); break
    return spans


# ---------------------------------------------------------------- card builders (return RGBA image + highlight rects)
def card_doc(b, sk, maxw=1300):
    style = sk.get('doc', 'paper')
    pal = {'paper': ('#FBFAF6', '#1A1A1A', '#6B6B6B', 'Times New Roman', 'Times New Roman Bold'),
           'dark': ('#11161F', '#E8EEF8', '#7F8DA6', 'Arial', 'Arial Bold'),
           'typewriter': ('#EFE6CF', '#2B2116', '#6E5E43', 'Courier New', 'Courier New Bold'),
           'clipping': ('#EDE7DA', '#151515', '#555555', 'Georgia', 'Georgia Bold')}[style]
    bg, fg, mute, ff, fb = pal
    W = maxw; pad = 80
    img = Image.new('RGBA', (W, 2400), rgb(bg)); d = ImageDraw.Draw(img)
    y = pad
    if b.get('subtitle'):
        d.text((pad, y), b['subtitle'].upper(), font=font(fb, 26), fill=rgb(mute)); y += 50
    if b.get('title'):
        for ln in wrap_words(d, b['title'], font(fb, 52), W - 2 * pad):
            d.text((pad, y), ln, font=font(fb, 52), fill=rgb(fg)); y += 64
        y += 14; d.line([(pad, y), (W - pad, y)], fill=rgb(mute), width=3); y += 34
    fnt = font(ff, 38 if style != 'typewriter' else 34)
    words, y = layout_text(d, b.get('text', ''), fnt, W - 2 * pad, pad, y, 56)
    for w, x0, y0, x1 in words: d.text((x0, y0), w, font=fnt, fill=rgb(fg))
    if b.get('source'):
        y += 30; d.text((pad, y), b['source'], font=font(ff, 24), fill=rgb(mute)); y += 40
    img = img.crop((0, 0, W, y + pad))
    spans = phrase_spans(words, b.get('highlight'))
    rects = [[(x0 - 6, y0 - 4, x1 + 6, y0 + 50) for (w, x0, y0, x1) in words[a:e]] for a, e in spans]
    return img, rects


def card_article(b, sk, maxw=1300):
    W, pad = maxw, 70
    img = Image.new('RGBA', (W, 2600), rgb('#FFFFFF')); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 64], fill=rgb('#E9ECEF'))
    for i, c in enumerate(['#FF5F57', '#FEBC2E', '#28C840']): d.ellipse([24 + i * 34, 22, 44 + i * 34, 42], fill=rgb(c))
    d.rounded_rectangle([150, 14, W - 40, 50], 16, fill=rgb('#FFFFFF')); d.text((172, 18), b.get('url', b.get('outlet', '')).lower(), font=font('Arial', 22), fill=rgb('#6B7280'))
    y = 100
    d.text((pad, y), b.get('outlet', '').upper(), font=font('Arial Black', 34), fill=rgb(sk.get('accent', '#C8102E'))); y += 56
    for ln in wrap_words(d, b.get('headline', ''), font('Georgia Bold', 56), W - 2 * pad):
        d.text((pad, y), ln, font=font('Georgia Bold', 56), fill=rgb('#111111')); y += 68
    if b.get('date'): d.text((pad, y + 6), b['date'], font=font('Arial', 26), fill=rgb('#6B7280')); y += 56
    if b.get('image') and os.path.exists(b['image']):
        ph = ImageOps.fit(Image.open(b['image']).convert('RGBA'), (W - 2 * pad, int((W - 2 * pad) * 0.5)))
        img.paste(ph, (pad, y + 10)); y += ph.height + 34
    fnt = font('Georgia', 36)
    words, y = layout_text(d, b.get('text', ''), fnt, W - 2 * pad, pad, y + 10, 54)
    for w, x0, y0, x1 in words: d.text((x0, y0), w, font=fnt, fill=rgb('#222222'))
    img = img.crop((0, 0, W, y + pad))
    spans = phrase_spans(words, b.get('highlight'))
    return img, [[(x0 - 5, y0 - 3, x1 + 5, y0 + 46) for (w, x0, y0, x1) in words[a:e]] for a, e in spans]


def load_photo(path, size):
    try:
        im = Image.open(path).convert('RGB')
    except Exception:
        im = Image.new('RGB', size, (40, 40, 40))
    return ImageOps.fit(im, size, Image.LANCZOS)


def card_photo(path, sk, size=(1280, 720), caption=None, tilt=0):
    style = sk.get('photo', 'clean')
    ph = load_photo(path, size)
    if sk.get('photo_bw'): ph = ImageOps.grayscale(ph).convert('RGB')
    if style == 'polaroid':
        bw, bot = 34, 150
        card = Image.new('RGBA', (size[0] + 2 * bw, size[1] + bw + bot), rgb('#FAFAF5'))
        card.paste(ph, (bw, bw))
        if caption:
            d = ImageDraw.Draw(card)
            d.text((card.width // 2, size[1] + bw + bot // 2), caption, font=font('Marker', 58), fill=rgb('#222222'), anchor='mm')
        return card.rotate(tilt, expand=True, resample=Image.BICUBIC)
    if style == 'tv':
        card = Image.new('RGBA', (size[0] + 16, size[1] + 16 + (84 if caption else 0)), rgb(sk.get('accent', '#E8B21E')))
        card.paste(ph, (8, 8))
        if caption:
            d = ImageDraw.Draw(card); d.rectangle([8, size[1] + 8, size[0] + 8, size[1] + 92], fill=rgb('#0B1426'))
            d.text((32, size[1] + 50), caption.upper(), font=font('Arial Black', 38), fill=rgb('#FFFFFF'), anchor='lm')
        return card
    card = Image.new('RGBA', (size[0] + 12, size[1] + 12), rgb('#FFFFFF')); card.paste(ph, (6, 6))
    return card


# ---------------------------------------------------------------- scene helpers
def background(sk, W, H):
    p = sk.get('bg_path')
    if p and os.path.exists(p):
        bg = ImageOps.fit(Image.open(p).convert('RGB'), (W, H))
        if sk.get('bg_blur'): bg = bg.filter(ImageFilter.GaussianBlur(sk['bg_blur']))
        if sk.get('bg_dim'): bg = ImageEnhance.Brightness(bg).enhance(sk['bg_dim'])
        return bg.convert('RGBA')
    return Image.new('RGBA', (W, H), rgb(sk.get('bg_color', '#15181E')))


def shadow_for(card, blur=24, alpha=150, off=(18, 26)):
    sh = Image.new('RGBA', (card.width + 120, card.height + 120), (0, 0, 0, 0))
    m = card.split()[3].point(lambda v: alpha if v > 0 else 0)
    sh.paste((0, 0, 0, 255), (60 + off[0], 60 + off[1]), m)
    return sh.filter(ImageFilter.GaussianBlur(blur))


def place(canvas, img, cx, cy, shadow=True):
    if shadow:
        sh = shadow_for(img); canvas.alpha_composite(sh, (int(cx - sh.width / 2), int(cy - sh.height / 2)))
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


def grain(im, amount=18, seed=0):
    rnd = random.Random(seed)
    n = Image.effect_noise((im.width // 2, im.height // 2), amount).resize(im.size).convert('L')
    return Image.blend(im.convert('RGB'), Image.merge('RGB', (n, n, n)), 0.08).convert('RGBA')


class Writer:
    def __init__(self, out, W, H, dur):
        self.n = max(1, int(round(dur * FPS)))
        enc = (['-c:v', 'h264_videotoolbox', '-b:v', '10M'] if os.uname().sysname == 'Darwin'
               else ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19'])
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                   '-r', str(FPS), '-i', '-', *enc, '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)

    def put(self, im): self.p.stdin.write(im.convert('RGB').tobytes())

    def close(self): self.p.stdin.close(); self.p.wait()


# ---------------------------------------------------------------- the renderer
def render(beat, sk, out, dur, W=1920, H=1080, hl_at=None, assets=None):
    """Render one beat to `out` (mp4). sk = template skin dict. hl_at = seconds into the beat when the
    narrator says the highlighted phrase (highlight sweep starts there)."""
    tp = beat['type']; wr = Writer(out, W, H, dur); n = wr.n
    bg = background(sk, W, H)
    hl_col = rgb(sk.get('highlight', '#FFE14D'), 255)
    hl0 = hl_at if hl_at is not None else dur * 0.25
    accent = sk.get('accent', '#E8B21E'); film = sk.get('film', False)

    def finish(fr, k):
        if film: fr = grain(fr, seed=k)
        if sk.get('vignette'):
            v = Image.new('L', (W, H), 0); dv = ImageDraw.Draw(v); dv.ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.35], fill=255)
            v = v.filter(ImageFilter.GaussianBlur(160)); fr = Image.composite(fr, Image.new('RGBA', (W, H), (0, 0, 0, 255)), v)
        if sk.get('letterbox'):
            d = ImageDraw.Draw(fr); bh = int(H * 0.128); d.rectangle([0, 0, W, bh], fill=(0, 0, 0)); d.rectangle([0, H - bh, W, H], fill=(0, 0, 0))
        return fr

    if tp in ('doc', 'article'):
        card, rects = (card_doc if tp == 'doc' else card_article)(beat, sk, maxw=int(min(1300, W * 0.72)) if W >= 1400 else int(W * 0.86))
        scale = min(1.0, (H * 1.55) / card.height) if sk.get('doc_closeup') else min(1.0, (H * 0.86) / card.height, (W * 0.8) / card.width)
        tilt = sk.get('doc_tilt', -2.5 if tp == 'doc' else 0)
        # highlight layer (full) — revealed left-to-right, phrase by phrase
        hl_layer = Image.new('RGBA', card.size, (0, 0, 0, 0)); dh = ImageDraw.Draw(hl_layer)
        flat = [r for grp in rects for r in grp]
        for r in flat: dh.rectangle(r, fill=hl_col)
        total_w = sum(r[2] - r[0] for r in flat) or 1
        cy_focus = (flat[0][1] + flat[-1][3]) / 2 if flat else card.height / 2
        for k in range(n):
            t = k / FPS
            prog = ease((t - hl0) / max(0.8, min(2.2, dur * 0.35)))
            c = card.copy()
            if flat and prog > 0:
                reveal = prog * total_w; m = Image.new('L', card.size, 0); dm = ImageDraw.Draw(m)
                for r in flat:
                    wdt = r[2] - r[0]
                    if reveal <= 0: break
                    dm.rectangle([r[0], r[1], r[0] + min(wdt, reveal), r[3]], fill=255); reveal -= wdt
                # marker = multiply blend, so the ink stays dark under the highlight
                mk = Image.new('RGB', card.size, (255, 255, 255)); mk.paste(hl_col[:3], (0, 0), m)
                c = Image.merge('RGBA', (*ImageChops.multiply(c.convert('RGB'), mk).split(), c.split()[3]))
            z = scale                                                   # STILL: no zoom / pan / bob
            cc = c.resize((int(c.width * z), int(c.height * z)), Image.LANCZOS).rotate(tilt, expand=True, resample=Image.BICUBIC)
            fr = bg.copy()
            place(fr, cc, W / 2, H / 2, shadow=sk.get('doc') != 'dark')
            wr.put(finish(fr, k))
    elif tp in ('photo', 'frame', 'broll') and not beat.get('file'):
        path = beat.get('image') or (assets or {}).get('frame')
        style = sk.get('photo', 'clean')
        if style == 'clean':
            src = load_photo(path, (int(W * 1.12), int(H * 1.12)))
            if sk.get('photo_bw'): src = ImageOps.grayscale(src).convert('RGB')
            fr0 = ImageOps.fit(src, (W, H), Image.LANCZOS).convert('RGBA')          # STILL
            if beat.get('caption'):
                d = ImageDraw.Draw(fr0); d.rectangle([0, H - 110, W, H], fill=(0, 0, 0, 160))
                d.text((60, H - 55), beat['caption'].upper(), font=font(sk.get('font_bold', 'Arial Black'), 40), fill=rgb('#FFFFFF'), anchor='lm')
            for k in range(n):
                wr.put(finish(fr0, k) if film else fr0)
        else:
            card = card_photo(path, sk, (int(W * 0.56), int(W * 0.56 * 9 / 16)), beat.get('caption'), tilt=random.Random(path).uniform(-5, 5))
            fr0 = bg.copy(); place(fr0, card, W / 2, H / 2)                     # STILL
            for k in range(n):
                fr = fr0.copy(); cc = card
                if style == 'polaroid':
                    d = ImageDraw.Draw(fr); d.ellipse([W / 2 - 16, H / 2 - cc.height / 2 - 6, W / 2 + 16, H / 2 - cc.height / 2 + 26], fill=rgb('#C62828'))
                wr.put(finish(fr, k))
    elif tp == 'collage':
        imgs = beat['images'][:4]; slots = [(-0.24, -0.18, -6), (0.24, -0.16, 5), (-0.2, 0.2, 4), (0.22, 0.2, -4)]
        cards = [card_photo(p, dict(sk, photo='polaroid' if sk.get('photo') == 'polaroid' else 'clean'), (int(W * 0.36), int(W * 0.36 * 9 / 16)), None, slots[i][2]) for i, p in enumerate(imgs)]
        step = dur * 0.6 / max(1, len(cards))
        for k in range(n):
            t = k / FPS; fr = bg.copy()
            for i, c in enumerate(cards):
                p = ease((t - i * step) / 0.4)
                if p <= 0: continue
                cc = c.copy()
                if p < 1: cc.putalpha(cc.split()[3].point(lambda v, p=p: int(v * p)))   # appear in place, no motion
                place(fr, cc, W / 2 + slots[i][0] * W, H / 2 + slots[i][1] * H)
            if beat.get('caption'):
                d = ImageDraw.Draw(fr); d.text((W / 2, H - 70), beat['caption'].upper(), font=font(sk.get('font_bold', 'Arial Black'), 44), fill=rgb('#FFFFFF'), anchor='mm', stroke_width=4, stroke_fill=(0, 0, 0))
            wr.put(finish(fr, k))
    elif tp == 'broll' and beat.get('file'):
        wr.close()
        vf = f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setpts=PTS-STARTPTS'
        if sk.get('photo_bw'): vf += ',hue=s=0'
        if film: vf += ',noise=alls=12:allf=t'
        if sk.get('letterbox'): vf += f",drawbox=0:0:{W}:{int(H * 0.128)}:black:t=fill,drawbox=0:{H - int(H * 0.128)}:{W}:{int(H * 0.128)}:black:t=fill"
        enc = (['-c:v', 'h264_videotoolbox', '-b:v', '10M'] if os.uname().sysname == 'Darwin' else ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19'])
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-stream_loop', '-1', '-i', beat['file'], '-t', f'{dur:.3f}', '-vf', vf, '-r', str(FPS), '-an', *enc, '-pix_fmt', 'yuv420p', out], check=True)
        return
    else:
        # text cards: title / definition / quote / timeline / charge / checklist
        TF, TB = sk.get('font', 'Arial'), sk.get('font_bold', 'Arial Black')
        fg, mute, panel = rgb(sk.get('card_fg', '#FFFFFF')), rgb(sk.get('card_mute', '#B8C2D3')), rgb(sk.get('card_bg', '#0B1426'), 225)
        for k in range(n):
            t = k / FPS; fr = bg.copy(); d = ImageDraw.Draw(fr); a = ease(t / 0.5)
            if tp == 'title':
                if sk.get('title_style') == 'chapter':
                    d.text((W / 2, H / 2 - 40), beat.get('sub', '').upper(), font=font(TF, 34), fill=rgb(accent, int(255 * a)), anchor='mm')
                    d.text((W / 2, H / 2 + 30), beat['text'], font=font(TB, 96), fill=(255, 255, 255, int(255 * a)), anchor='mm')
                    lw = int(420 * a); d.line([(W / 2 - lw / 2, H / 2 + 110), (W / 2 + lw / 2, H / 2 + 110)], fill=rgb(accent), width=3)
                else:
                    bw_ = int((W * 0.62) * ease(t / 0.35)); d.rectangle([0, H / 2 - 110, bw_, H / 2 + 110], fill=rgb(accent))
                    if t > 0.25:
                        d.text((90, H / 2 - 30), beat['text'].upper(), font=font(TB, 92), fill=rgb(sk.get('title_fg', '#0B1426')), anchor='lm')
                        if beat.get('sub'): d.text((94, H / 2 + 60), beat['sub'], font=font(TF, 40), fill=rgb(sk.get('title_fg', '#0B1426')), anchor='lm')
            elif tp == 'definition':
                x0, y0, x1, y1 = W * 0.14, H * 0.24, W * 0.86, H * 0.76
                d.rounded_rectangle([x0, y0, x1, y1], 26, fill=panel)
                d.rectangle([x0, y0, x0 + 14, y1], fill=rgb(accent))
                d.text((x0 + 70, y0 + 70), beat['term'].upper(), font=font(TB, 64), fill=rgb(accent), anchor='lm')
                ws, _ = layout_text(d, beat.get('text', ''), font(TF, 42), x1 - x0 - 140, x0 + 70, y0 + 140, 60)
                vis = int(len(ws) * ease((t - 0.3) / max(0.6, dur * 0.4)))
                for w, wx, wy, _ in ws[:vis]: d.text((wx, wy), w, font=font(TF, 42), fill=fg)
                if beat.get('source'): d.text((x0 + 70, y1 - 50), beat['source'], font=font(TF, 26), fill=mute, anchor='lm')
            elif tp == 'quote':
                qf = font(sk.get('quote_font', 'Georgia Bold'), 66)
                d.text((W * 0.12, H * 0.2), '\u201C', font=font('Georgia Bold', 220), fill=rgb(accent, int(255 * a)))
                ws, yend = layout_text(d, beat['text'], qf, W * 0.72, W * 0.16, H * 0.33, 88)
                vis = int(len(ws) * ease((t - 0.2) / max(0.6, dur * 0.5)))
                for w, wx, wy, _ in ws[:vis]: d.text((wx, wy), w, font=qf, fill=fg)
                if beat.get('by') and t > dur * 0.4: d.text((W * 0.16, yend + 40), '\u2014 ' + beat['by'], font=font(TF, 40), fill=rgb(accent))
            elif tp == 'timeline':
                ev = beat['events'][:5]; y = H * 0.56; d.line([(W * 0.08, y), (W * 0.08 + W * 0.84 * ease(t / 0.8), y)], fill=rgb(accent), width=6)
                for i, (date, what) in enumerate(ev):
                    p = ease((t - 0.4 - i * dur * 0.6 / max(1, len(ev))) / 0.4)
                    if p <= 0: continue
                    x = W * 0.1 + i * (W * 0.8 / max(1, len(ev) - 1 if len(ev) > 1 else 1))
                    d.ellipse([x - 18, y - 18, x + 18, y + 18], fill=rgb(accent))
                    d.text((x, y - 70), date, font=font(TB, 36), fill=(255, 255, 255, int(255 * p)), anchor='mm')
                    for j, ln in enumerate(textwrap.wrap(what, 18)[:3]):
                        d.text((x, y + 60 + j * 44), ln, font=font(TF, 34), fill=(*fg[:3], int(255 * p)), anchor='mm')
            elif tp == 'charge':
                x0, y0, x1, y1 = W * 0.18, H * 0.2, W * 0.82, H * 0.8
                d.rectangle([x0, y0, x1, y1], fill=panel); d.rectangle([x0, y0, x1, y0 + 90], fill=rgb(sk.get('charge_bar', '#B71C1C')))
                d.text((W / 2, y0 + 45), sk.get('charge_label', 'THE CHARGE'), font=font(TB, 46), fill=rgb('#FFFFFF'), anchor='mm')
                rows = [('OFFENSE', beat.get('offense', '')), ('LAW', beat.get('law', '')), ('PENALTY', beat.get('penalty', ''))]
                for i, (lab, val) in enumerate(rows):
                    p = ease((t - 0.3 - i * 0.6) / 0.4)
                    if p <= 0: continue
                    yy = y0 + 150 + i * 150
                    d.text((x0 + 60, yy), lab, font=font(TB, 30), fill=rgb(accent, int(255 * p)))
                    for j, ln in enumerate(wrap_words(d, val, font(TF, 40), x1 - x0 - 120)[:2]):
                        d.text((x0 + 60, yy + 42 + j * 48), ln, font=font(TF, 40), fill=(*fg[:3], int(255 * p)))
            elif tp == 'checklist':
                d.text((W * 0.14, H * 0.2), beat.get('title', '').upper(), font=font(TB, 60), fill=rgb(accent))
                for i, (item, ok) in enumerate(beat['items'][:5]):
                    p = ease((t - 0.4 - i * dur * 0.6 / max(1, len(beat['items']))) / 0.35)
                    yy = H * 0.34 + i * 120
                    d.rounded_rectangle([W * 0.14, yy, W * 0.14 + 80, yy + 80], 12, outline=fg, width=5)
                    d.text((W * 0.14 + 120, yy + 40), item, font=font(TF, 48), fill=fg, anchor='lm')
                    if p > 0:
                        col = rgb('#2EAD4B' if ok else '#E53935')
                        if ok: d.line([(W * 0.14 + 14, yy + 42), (W * 0.14 + 34, yy + 64), (W * 0.14 + 14 + 56 * p, yy + 64 - 50 * p)], fill=col, width=10)
                        else:
                            d.line([(W * 0.14 + 16, yy + 16), (W * 0.14 + 16 + 48 * p, yy + 16 + 48 * p)], fill=col, width=10)
                            d.line([(W * 0.14 + 64, yy + 16), (W * 0.14 + 64 - 48 * p, yy + 16 + 48 * p)], fill=col, width=10)
            wr.put(finish(fr, k))
    wr.close()
