"""Template layout families -> where every camera tile goes on the 1920x1080 canvas.

plan(T, n, mode) returns a dict:
  slots : [{'tile': i, 'rect': (x,y,w,h), 'zoom': 1.0, 'border': (px, color) | None, 'shadow': bool,
            'label': (x, y, align) | None}]
  boxes : [(x, y, w, h, color)]           solid shapes (frames, panels, bars) — color may be '#RRGGBB@0.6'
  texts : [{'key': ..., 'x', 'y', 'an', 'size', 'color', 'box'}]   static text slots (filled from script.json)
  bg    : 'image' (template bg.jpg) | 'blur' (blurred copy of tile 0 fills the canvas)
  cap   : {'y': baseline-bottom px, 'align': 'center'|'left', 'x': left margin}
n = number of camera tiles on screen at that moment (1 = one camera / full frame).
mode = 'normal' or 'vo' (narration moments; some families change layout while the narrator talks).
Any tile can be any aspect (portrait phone video, wide courtroom): slots fill with "cover" and the
renderer switches to "contain + blurred fill" automatically when the aspect is too different.
"""
W, H = 1920, 1080


def _strip(T, n, mode):
    fr = T.get('frame', {}); th = fr.get('thickness', 8); col = fr.get('color', '#FFFFFF')
    cap = T['caption']; pos = cap.get('position', 'on'); band = cap.get('band', 170)
    style = fr.get('style', 'lines'); gap = T.get('gap', 8); cw = T.get('cam_w', 900); ch = round(cw * 9 / 16)
    sw = 2 * cw + gap; sx = (W - sw) // 2
    sy = (H - ch - band) // 2 if pos == 'below' else (H - ch + band) // 2 if pos == 'above' else (H - ch) // 2
    shadow = T.get('shadow', False)
    out = dict(slots=[], boxes=[], texts=[], bg='image')

    def border(x, y, w, h):
        return [(x - th, y - th, w + 2 * th, th, col), (x - th, y + h, w + 2 * th, th, col),
                (x - th, y, th, h, col), (x + w, y, th, h, col)]

    if n == 1 or (mode == 'vo' and T.get('vo_style') == 'focus'):
        if pos == 'below': fh = sy + ch - 70; fy = 70
        elif pos == 'above': fy = sy; fh = H - 70 - sy
        else: fh = round(T.get('full_w', 1440) * 9 / 16); fy = (H - fh) // 2
        fh = min(fh, round((W - 120) * 9 / 16)); fw = round(fh * 16 / 9); fx = (W - fw) // 2
        if mode == 'vo' and T.get('vo_style') == 'focus':          # Verdictly: narrator over a full-screen punch-in
            fx, fy, fw, fh = 0, 0, W, H
        out['slots'].append(dict(tile=T.get('vo_focus_tile', 1) if (mode == 'vo' and n > 1) else 0,
                                 rect=(fx, fy, fw, fh), zoom=1.15 if mode == 'vo' and T.get('vo_style') == 'focus' else 1.0,
                                 shadow=shadow, label=(fx + 24, fy + 20, 7)))
        if not (mode == 'vo' and T.get('vo_style') == 'focus'):
            if style == 'lines': out['boxes'] += [(fx, fy - th, fw, th, col), (fx, fy + fh, fw, th, col)]
            elif style in ('outer', 'box'): out['boxes'] += border(fx, fy, fw, fh)
        cap_y = (fy + fh - cap.get('inset', 14)) if pos == 'on' else (fy + fh + th + band - 40) if pos == 'below' else fy - th - 40
        if mode == 'vo' and T.get('vo_style') == 'focus': cap_y = H - 70
        out['cap'] = dict(y=cap_y, align='center', x=fx)
        return out
    cams = [(sx, sy, cw, ch), (sx + cw + gap, sy, cw, ch)]
    for i in range(2):
        out['slots'].append(dict(tile=i, rect=cams[i], shadow=shadow, label=(cams[i][0] + 18, cams[i][1] + 14, 7)))
    if n >= 3:
        x, y, cw2, ch2 = cams[1]; pw, ph = round(cw2 * 0.34), round(ch2 * 0.34)
        out['slots'].append(dict(tile=2, rect=(x + cw2 - pw - 16, y + 16, pw, ph), border=(4, col if style != 'none' else '#FFFFFF')))
    if style == 'lines':
        out['boxes'] += [(sx, sy - th, sw, th, col), (sx, sy + ch, sw, th, col)]
    elif style == 'outer':
        out['boxes'] += border(sx, sy, sw, ch)
    elif style == 'box':
        out['boxes'] += border(*cams[0]) + border(*cams[1])
    if T.get('divider') and gap > 0:
        out['boxes'].append((sx + cw, sy, gap, ch, T['divider'].get('color', col)))
    cap_y = (sy + ch - cap.get('inset', 14)) if pos == 'on' else (sy + ch + th + band - 40) if pos == 'below' else sy - th - 40
    out['cap'] = dict(y=cap_y, align='center', x=sx)
    return out


def _news(T, n, mode):
    """TV news desk: footage box left, case-info panel right, title ticker bottom."""
    acc = T.get('accent', '#E8B21E')
    bx, by, bw, bh = 40, 40, 1300, 731
    out = dict(slots=[dict(tile=0, rect=(bx, by, bw, bh), label=(bx + 24, by + 22, 7))], bg='image', texts=[],
               boxes=[(bx - 6, by - 6, bw + 12, 6, acc), (bx - 6, by + bh, bw + 12, 6, acc), (bx - 6, by, 6, bh, acc),
                      (bx + bw, by, 6, bh, acc),
                      (1370, 40, 510, 737, '#0B1426@0.88'), (1370, 40, 510, 8, acc),
                      (0, 800, W, 92, '#0B1426@0.92'), (0, 800, 300, 92, acc)])
    if n >= 2:
        out['slots'].append(dict(tile=1, rect=(bx + bw - 440 - 20, by + bh - 248 - 20, 440, 248), border=(5, acc),
                                 label=(bx + bw - 440, by + bh - 260, 7)))
    out['texts'] = [dict(key='panel_head', x=1400, y=80, an=7, size=34, color=acc),
                    dict(key='case_title', x=1400, y=140, an=7, size=40, color='#FFFFFF', wrap=True),
                    dict(key='court', x=1400, y=330, an=7, size=30, color='#BFD3FF', wrap=True),
                    dict(key='charge', x=1400, y=470, an=7, size=32, color='#FFFFFF', wrap=True),
                    dict(key='judge', x=1400, y=650, an=7, size=34, color=acc),
                    dict(key='ticker_tag', x=150, y=846, an=5, size=38, color='#0B1426'),
                    dict(key='title', x=330, y=846, an=4, size=36, color='#FFFFFF')]
    out['cap'] = dict(y=by + bh - 24, align='center', x=bx)
    return out


def _spotlight(T, n, mode):
    """One big camera + a column of smaller cameras on the right."""
    acc = T.get('accent', '#FFFFFF')
    if n == 1:
        r = (240, 70, 1440, 810)
        out = dict(slots=[dict(tile=0, rect=r, border=(6, acc), shadow=True, label=(r[0] + 24, r[1] + 20, 7))],
                   boxes=[], texts=[], bg='image')
        out['cap'] = dict(y=r[1] + r[3] + 120, align='center', x=r[0])
        return out
    main = (50, 90, 1360, 765)
    out = dict(slots=[dict(tile=0, rect=main, border=(6, acc), shadow=True, label=(main[0] + 24, main[1] + 20, 7))],
               boxes=[], texts=[], bg='image')
    for k in range(1, min(n, 4)):
        r = (1450, 90 + (k - 1) * 262, 420, 236)
        out['slots'].append(dict(tile=k, rect=r, border=(4, acc), shadow=True, label=(r[0] + 14, r[1] + 10, 7)))
    out['cap'] = dict(y=main[1] + main[3] + 125, align='center', x=main[0])
    return out


def _fullbleed(T, n, mode):
    """Edge-to-edge footage, no background. 2 cameras = two full-height halves."""
    acc = T.get('accent', '#FFFFFF')
    out = dict(slots=[], boxes=[], texts=[], bg='image')
    if n == 1:
        out['slots'].append(dict(tile=0, rect=(0, 0, W, H), label=(40, 36, 7)))
    else:
        out['slots'] += [dict(tile=0, rect=(0, 0, 956, H), label=(40, 36, 7)),
                         dict(tile=1, rect=(964, 0, 956, H), label=(1004, 36, 7))]
        out['boxes'].append((956, 0, 8, H, acc))
        if n >= 3:
            out['slots'].append(dict(tile=2, rect=(760, 40, 400, 225), border=(5, acc)))
    out['boxes'].append((0, H - 230, W, 230, '#000000@0.35'))
    out['cap'] = dict(y=H - 90, align='center', x=60)
    return out


def _cinema(T, n, mode):
    """2.39:1 letterbox — captions live in the bottom black bar."""
    top, bh = 138, 804
    out = dict(slots=[], boxes=[], texts=[], bg='image')
    if n == 1:
        out['slots'].append(dict(tile=0, rect=(0, top, W, bh), label=(60, top + 30, 7)))
    else:
        out['slots'] += [dict(tile=0, rect=(0, top, 954, bh), label=(60, top + 30, 7)),
                         dict(tile=1, rect=(966, top, 954, bh), label=(1026, top + 30, 7))]
        out['boxes'].append((954, top, 12, bh, '#000000'))
        if n >= 3:
            out['slots'].append(dict(tile=2, rect=(1460, top + 30, 420, 236), border=(3, '#FFFFFF')))
    out['cap'] = dict(y=H - 40, align='center', x=60)
    out['texts'].append(dict(key='letterbox_tag', x=60, y=70, an=4, size=34, color='#C9A227'))
    return out


def _bigpip(T, n, mode):
    """Wide courtroom camera full screen, the other camera as a big picture-in-picture."""
    acc = T.get('accent', '#FFFFFF')
    out = dict(slots=[dict(tile=0, rect=(0, 0, W, H), label=(40, 36, 7))], boxes=[], texts=[], bg='image')
    if n >= 2:
        r = (1150, 590, 720, 405)
        out['slots'].append(dict(tile=1, rect=r, border=(6, acc), shadow=True, label=(r[0] + 16, r[1] + 12, 7)))
    if n >= 3:
        r = (1390, 60, 480, 270)
        out['slots'].append(dict(tile=2, rect=r, border=(5, acc), shadow=True, label=(r[0] + 14, r[1] + 10, 7)))
    out['boxes'].append((0, H - 200, 1120, 200, '#000000@0.45'))
    out['cap'] = dict(y=H - 70, align='left', x=70)
    return out


def _gallery(T, n, mode):
    """Every camera tile on screen in an even grid (Zoom hearings with many people)."""
    acc = T.get('accent', '#FFFFFF')
    n2 = max(1, min(n, 6))
    cols = 1 if n2 == 1 else 2 if n2 <= 4 else 3
    rows = (n2 + cols - 1) // cols
    gx, gy, gw, gh = 60, 40, 1800, 840
    cw = min((gw - (cols - 1) * 24) / cols, ((gh - (rows - 1) * 24) / rows) * 16 / 9)
    ch = cw * 9 / 16
    tot_h = rows * ch + (rows - 1) * 24; y0 = gy + (gh - tot_h) / 2
    out = dict(slots=[], boxes=[], texts=[], bg='image')
    for i in range(n2):
        r_, c_ = divmod(i, cols)
        in_row = min(cols, n2 - r_ * cols)
        row_w = in_row * cw + (in_row - 1) * 24
        x = (W - row_w) / 2 + c_ * (cw + 24); y = y0 + r_ * (ch + 24)
        rect = tuple(int(v) for v in (x, y, cw, ch))
        out['slots'].append(dict(tile=i, rect=rect, border=(4, acc), shadow=True, label=(rect[0] + 12, rect[1] + rect[3] - 12, 1)))
    out['cap'] = dict(y=H - 46, align='center', x=60)
    return out


def _versus(T, n, mode):
    """Two full-height halves with colored edges, name plates and a VS badge."""
    a, b = T.get('left_color', '#1E6BFF'), T.get('right_color', '#E52222')
    out = dict(slots=[], boxes=[], texts=[], bg='image')
    if n == 1:
        out['slots'].append(dict(tile=0, rect=(0, 0, W, H), label=(40, 36, 7)))
        out['cap'] = dict(y=H - 80, align='center', x=60)
        return out
    out['slots'] += [dict(tile=0, rect=(0, 0, 950, H)), dict(tile=1, rect=(970, 0, 950, H))]
    out['boxes'] += [(950, 0, 20, H, '#000000'), (0, 0, 950, 10, a), (970, 0, 950, 10, b),
                     (0, 10, 950, 86, a + '@0.85'), (970, 10, 950, 86, b + '@0.85'),
                     (900, 470, 120, 120, '#FFFFFF'), (906, 476, 108, 108, '#111111'),
                     (0, H - 210, W, 210, '#000000@0.45')]
    out['texts'] += [dict(key='label0', x=475, y=54, an=5, size=46, color='#FFFFFF'),
                     dict(key='label1', x=1445, y=54, an=5, size=46, color='#FFFFFF'),
                     dict(key='vs', x=960, y=531, an=5, size=58, color='#FFD000')]
    if n >= 3:
        out['slots'].append(dict(tile=2, rect=(760, 130, 400, 225), border=(4, '#FFFFFF')))
    out['cap'] = dict(y=H - 70, align='center', x=60)
    return out


def _lawpanel(T, n, mode):
    """Law-class: court footage left, a 'THE LAW' notes panel on the right that explains the current
    legal point while the hearing plays (notes come from script.json "notes")."""
    acc = T.get('accent', '#1565C0')
    main = (40, 70, 1240, 698)
    out = dict(slots=[dict(tile=0, rect=main, border=(5, acc), shadow=True, label=(main[0] + 20, main[1] + 18, 7))],
               boxes=[(1310, 70, 570, 698, '#FFFFFF'), (1310, 70, 570, 86, acc)], texts=[], bg='image')
    if n >= 2:
        r = (main[0] + main[2] - 400 - 18, main[1] + main[3] - 225 - 18, 400, 225)
        out['slots'].append(dict(tile=1, rect=r, border=(4, '#FFFFFF'), label=(r[0] + 12, r[1] + 10, 7)))
    out['texts'] = [dict(key='panel_head', x=1340, y=113, an=4, size=40, color='#FFFFFF'),
                    dict(key='note', x=1340, y=200, an=7, size=40, color='#1B2430', wrap=True)]
    out['cap'] = dict(y=main[1] + main[3] + 150, align='center', x=main[0])
    return out


FAMILIES = dict(strip=_strip, news=_news, spotlight=_spotlight, fullbleed=_fullbleed, cinema=_cinema,
                bigpip=_bigpip, gallery=_gallery, versus=_versus, lawpanel=_lawpanel)


def plan(T, n, mode='normal'):
    p = FAMILIES[T.get('layout', 'strip')](T, n, mode)
    p.setdefault('cap', dict(y=H - 60, align='center', x=60))
    return p
