"""Shared helpers for Courtroom Studio: paths, ffmpeg/ffprobe, templates, frame geometry."""
import json, os, platform, subprocess, sys

STUDIO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(STUDIO, 'templates')
PROJECTS = os.path.join(STUDIO, 'projects')
W, H, FPS = 1920, 1080, 30

sys.path.insert(0, os.path.join(os.path.dirname(STUDIO), 'tools'))
import license as _lic                                   # one key = one PC (teacher deta hai)
_lic.require()


def proj_dir(name):
    d = os.path.join(PROJECTS, name)
    os.makedirs(d, exist_ok=True)
    return d


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def dur(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def video_size(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                          '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip()
    w, h = out.split(',')[:2]
    return int(w), int(h)


def h264_args(bitrate='8M'):
    """Hardware encoder on macOS, libx264 elsewhere."""
    if platform.system() == 'Darwin':
        return ['-c:v', 'h264_videotoolbox', '-b:v', bitrate]
    return ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20']


def load_json(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        sys.exit(f'missing: {path}')
    return json.load(open(path))


def save_json(obj, path):
    json.dump(obj, open(path, 'w'), indent=1)


def list_templates():
    return sorted(d for d in os.listdir(TEMPLATES) if os.path.isfile(os.path.join(TEMPLATES, d, 'template.json')))


def load_template(tid):
    """tid can be 'T3' or the full folder name 'T3-american-flag'."""
    for d in list_templates():
        norm = lambda x: (x[:1].upper(), x[1:].lstrip('0')) if x[:1].isalpha() else ('T', x.lstrip('0'))
        if d == tid or norm(d.split('-')[0]) == norm(tid):
            t = json.load(open(os.path.join(TEMPLATES, d, 'template.json')))
            t['dir'] = os.path.join(TEMPLATES, d)
            t['id'] = d
            return t
    sys.exit(f'unknown template {tid}; available: {", ".join(list_templates())}')


def hexcol(c):
    return '0x' + c.lstrip('#')


def geom(t):
    """Frame geometry for a template.

    Returns dict:
      cams:  [(x,y,w,h), (x,y,w,h)]  two-camera strip
      full:  (x,y,w,h)               single / full-screen camera
      boxes_strip, boxes_full: [(x,y,w,h,color)] solid frame pieces
      cap_bottom: y of the caption baseline area bottom (px from top)
    """
    fr = t['frame']; cap = t['caption']
    th = fr.get('thickness', 8); col = fr.get('color', '#FFFFFF')
    cw = t.get('cam_w', 900); ch = round(cw * 9 / 16); gap = t.get('gap', 8)
    sw = 2 * cw + gap; sx = (W - sw) // 2
    band = cap.get('band', 170)            # room reserved for captions outside the frame
    pos = cap.get('position', 'on')
    if pos == 'below':
        sy = (H - ch - band) // 2
    elif pos == 'above':
        sy = (H - ch + band) // 2
    else:
        sy = (H - ch) // 2
    cams = [(sx, sy, cw, ch), (sx + cw + gap, sy, cw, ch)]

    # full-screen camera box
    if pos == 'below':
        fh = sy + ch - 70; fy = 70
    elif pos == 'above':
        fy = sy; fh = H - 70 - sy
    else:
        fh = round(t.get('full_w', 1440) * 9 / 16); fy = (H - fh) // 2
    fh = min(fh, round((W - 120) * 9 / 16)); fw = round(fh * 16 / 9); fx = (W - fw) // 2
    full = (fx, fy, fw, fh)

    def border(x, y, w, h):
        return [(x - th, y - th, w + 2 * th, th, col), (x - th, y + h, w + 2 * th, th, col),
                (x - th, y, th, h, col), (x + w, y, th, h, col)]

    style = fr.get('style', 'lines')
    bs, bf = [], []
    if style == 'lines':
        bs = [(sx, sy - th, sw, th, col), (sx, sy + ch, sw, th, col)]
        bf = [(fx, fy - th, fw, th, col), (fx, fy + fh, fw, th, col)]
    elif style == 'outer':
        bs = border(sx, sy, sw, ch); bf = border(fx, fy, fw, fh)
    elif style == 'box':
        bs = border(*cams[0]) + border(*cams[1]); bf = border(fx, fy, fw, fh)
    div = t.get('divider')
    if div and gap > 0:
        bs.append((sx + cw, sy, gap, ch, div.get('color', col)))

    if pos == 'on':
        cap_bottom = sy + ch - cap.get('inset', 14)
    elif pos == 'below':
        cap_bottom = sy + ch + th + band - 40
    else:
        cap_bottom = sy - th - 40
    return dict(cams=cams, full=full, boxes_strip=bs, boxes_full=bf, cap_bottom=cap_bottom,
                cap_margin=sx, strip=(sx, sy, sw, ch))


def filt_path(p):
    """path usable inside an ffmpeg filter argument (Windows: C:\\x -> C\\:/x)."""
    p = os.path.abspath(p).replace('\\', '/')
    return "'" + p.replace(':', '\\:').replace("'", "\\'") + "'"


def cat_path(p):
    """path for an ffmpeg concat list file (forward slashes, quotes escaped)."""
    return os.path.abspath(p).replace('\\', '/').replace("'", "'\\''")


def tool_cmd(name, module=None):
    """CLI that may only exist as a python module (Windows PATH issues): yt-dlp, edge-tts."""
    import shutil
    exe = shutil.which(name)
    return [exe] if exe else [sys.executable, '-m', module or name.replace('-', '_')]


def target_len(hearing_sec):
    """Default final length for a hearing (seconds). Owner rule: never shrink a long hearing to 8-10 min.
    <=20 min -> ~all of it (+narration) | 1 hr -> ~40 min | 2 hr -> ~60-65 min | longer -> ~1 hr + a bit."""
    m = hearing_sec / 60.0
    if m <= 20: r = 1.0
    elif m <= 60: r = 1.0 - (m - 20) / 40 * 0.33          # 20 min -> 100%, 60 min -> 67% (= 40 min)
    elif m <= 120: r = 0.67 - (m - 60) / 60 * 0.15        # 60 min -> 40 min, 120 min -> 62 min
    else: return (62 + (m - 120) * 0.25) * 60
    return m * r * 60
