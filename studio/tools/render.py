#!/usr/bin/env python3
"""Step 7 — render project_T##.json to MP4 (ffmpeg), a preview frame, or a short sample.

  python3 tools/render.py <project> --template T05              # -> projects/<project>/final_T05.mp4
  python3 tools/render.py <project> --template T05 --still 95   # -> preview_T05.jpg (frame at 95 s)
  python3 tools/render.py <project> --template T05 --sample 45  # -> sample_T05.mp4 (first 45 s)

Each segment is composed in layer order (background, shadows, cameras, frames/panels), segments are
concatenated, then audio (court + narration, -14 LUFS) and the text layer (captions, name tags, panels,
tags) are burned in with ASS subtitles.
"""
import argparse, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import proj_dir, load_json, load_template, h264_args, filt_path, cat_path, FPS, W, H

ap = argparse.ArgumentParser()
ap.add_argument('project'); ap.add_argument('--template', default='T01')
ap.add_argument('--still', type=float); ap.add_argument('--sample', type=float)
ap.add_argument('--out')
a = ap.parse_args()
d = proj_dir(a.project)
T = load_template(a.template); tid = T['id'].split('-')[0]
P = load_json(os.path.join(d, f'project_{tid}.json'))
FF = ['ffmpeg', '-v', 'error', '-y']
bg = os.path.join(T['dir'], T['bg'])

vis = [o for o in P['overlays'] if o['type'] in ('video', 'shape')]
groups = {}
for o in vis: groups.setdefault(o['from'], []).append(o)
order = sorted(groups)


def col(c):
    c, _, al = c.partition('@')
    return '0x' + c.lstrip('#') + (('@' + al) if al else '')


def compose_cmd(fr, n, out, offset=0.0, still=False):
    items = sorted(groups[fr], key=lambda o: -o['row'])          # back to front
    vids = [o for o in items if o['type'] == 'video']
    sp = vids[0]['speed'] if vids else 1.0
    cmd = FF + ['-loop', '1', '-framerate', str(FPS), '-i', bg]
    fc, last, k = [f'[0:v]scale={W}:{H},setsar=1[bg]'], 'bg', 0
    for o in items:
        if o['type'] == 'shape':
            fc.append(f"[{last}]drawbox=x={o['left']}:y={o['top']}:w={o['width']}:h={o['height']}:color={col(o['styles']['fill'])}:t=fill[c{k}]")
            last = f'c{k}'; k += 1; continue
        i = len([x for x in cmd if x == '-i'])
        st = o['videoStartTime'] + offset * sp
        cmd += ['-ss', f'{st:.3f}', '-t', f'{n / FPS * sp + 0.5:.3f}', '-i', o['src']]
        w, h, s = o['width'], o['height'], o['styles']
        chain = f'[{i}:v]setpts=(PTS-STARTPTS)/{sp},fps={FPS}'
        z = s.get('zoom', 1.0)
        if z and z > 1.0: chain += f',crop=iw/{z}:ih/{z}'
        if s.get('gray'): chain += ',hue=s=0'
        if s.get('objectFit') == 'contain':
            fc.append(chain + f',split[a{k}][b{k}]')
            fc.append(f'[a{k}]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=24:2,eq=brightness=-0.15[ab{k}]')
            fc.append(f'[b{k}]scale={w}:{h}:force_original_aspect_ratio=decrease[bb{k}]')
            fc.append(f'[ab{k}][bb{k}]overlay=(W-w)/2:(H-h)/2[v{k}]')
        else:
            fc.append(chain + f',scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}[v{k}]')
        fc.append(f"[{last}][v{k}]overlay={o['left']}:{o['top']}:eof_action=repeat[c{k}]")
        last = f'c{k}'; k += 1
    fc.append(f'[{last}]format=yuv420p[out]')
    cmd += ['-filter_complex', ';'.join(fc), '-map', '[out]', '-frames:v', str(1 if still else n)]
    cmd += (['-q:v', '3'] if still else [*h264_args('12M'), '-r', str(FPS)]) + [out]
    return cmd


# ---------------------------------------------------------------- text layer -> ASS
def ass_color(hx):
    hx = hx.lstrip('#'); return f'&H00{hx[4:6]}{hx[2:4]}{hx[0:2]}&'.upper()


def ts(msv):
    cs = int(round(msv / 10)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); s, cs = divmod(cs, 100)
    return f'{h}:{m:02d}:{s:02d}.{cs:02d}'


C = T['caption']
cap = next(o for o in P['overlays'] if o['type'] == 'caption')
zones = cap.get('zones', [])
cstyle = C.get('style', 'karaoke')
box = cstyle == 'box'
head = ['[Script Info]', 'ScriptType: v4.00+', f'PlayResX: {W}', f'PlayResY: {H}', 'WrapStyle: 0', '',
        '[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, '
        'Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
        f"Style: Cap,{C['font']},{C['size']},{ass_color(C['color'])},{ass_color(C['color'])},"
        f"{ass_color(C.get('box_color', '#000000') if box else C.get('outline', '#000000'))},&H96000000&,-1,0,0,0,100,100,1,0,"
        f"{3 if box else 1},{C.get('box_pad', 14) if box else C.get('outline_w', 4)},{0 if box else C.get('shadow', 3)},2,60,60,60,1",
        f"Style: Txt,{T.get('text_font', 'Arial Black')},40,&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H96000000&,-1,0,0,0,100,100,0,0,1,3,2,7,0,0,0,1",
        '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
HI = '{\\c' + ass_color(C['highlight']) + '}'; NO = '{\\c' + ass_color(C['color']) + '}'
up = (lambda s: s.upper()) if C.get('upper', True) else (lambda s: s)


def zone_at(sec):
    for z0, z1, z in zones:
        if z0 <= sec < z1: return z
    return zones[-1][2] if zones else dict(y=H - 60, align='center', x=60)


def pos_tag(sec):
    z = zone_at(sec)
    if z.get('align') == 'left':
        return '{\\an1\\pos(%d,%d)}' % (z['x'], z['y'])
    return '{\\an2\\pos(%d,%d)}' % (W // 2, z['y'])


def cap_events():
    if C.get('off'): return
    for c in cap['captions']:
        ws = c['words']
        for k, w in enumerate(ws):
            s0 = w['startMs'] if k else c['startMs']
            s1 = ws[k + 1]['startMs'] if k + 1 < len(ws) else c['endMs']
            if s1 <= s0: continue
            if cstyle == 'pop':                       # one big word at a time with a little bounce
                txt = '{\\fscx70\\fscy70\\t(0,90,\\fscx100\\fscy100)}' + HI + up(w['word'])
            else:
                txt = ' '.join((HI + up(x['word']) + NO) if i == k else up(x['word']) for i, x in enumerate(ws))
            yield s0, s1, 'Cap', pos_tag(s0 / 1000) + txt


def text_events():
    for o in P['overlays']:
        if o['type'] != 'text': continue
        s = o['styles']
        hx = s['color'].lstrip('#'); dark = (int(hx[0:2], 16) * 299 + int(hx[2:4], 16) * 587 + int(hx[4:6], 16) * 114) / 1000 < 110
        tag = '{\\an%d\\pos(%d,%d)\\fs%d\\c%s\\fn%s%s}' % (s['an'], o['left'], o['top'], s['fontSize'], ass_color(s['color']), s['fontFamily'],
                                                    '\\bord0\\shad0' if dark else '')
        yield int(o['from'] / FPS * 1000), int((o['from'] + o['durationInFrames']) / FPS * 1000), 'Txt', tag + o['content']


def write_ass(path, lo=0, hi=10 ** 12, shift=0, still=False):
    lines = list(head)
    for s0, s1, st, txt in list(text_events()) + list(cap_events()):
        if still:
            if s0 <= lo < s1: lines.append(f'Dialogue: 0,0:00:00.00,0:00:05.00,{st},,0,0,0,,{txt}')
            continue
        if s1 <= lo or s0 >= hi: continue
        lines.append(f'Dialogue: 0,{ts(max(0, s0 - shift))},{ts(min(hi, s1) - shift)},{st},,0,0,0,,{txt}')
    open(path, 'w').write('\n'.join(lines) + '\n')


if a.still is not None:
    fr0 = int(a.still * FPS)
    fr = max(x for x in order if x <= fr0)
    tmp = os.path.join(d, '_still.png')
    subprocess.run(compose_cmd(fr, 1, tmp, offset=(fr0 - fr) / FPS, still=True), check=True)
    assp = os.path.join(d, '_still.ass')
    ms0 = int(a.still * 1000)
    write_ass(assp, lo=ms0, still=True)
    out = a.out or os.path.join(d, f'preview_{tid}.jpg')
    subprocess.run(FF + ['-i', tmp, '-vf', f'ass={filt_path(assp)}', '-frames:v', '1', '-q:v', '3', out], check=True)
    os.remove(tmp); os.remove(assp)
    print('saved', out); sys.exit()

LIMIT = int(a.sample * FPS) if a.sample else P['durationInFrames']
order = [fr for fr in order if fr < LIMIT]
seg = os.path.join(d, f'_seg_{tid}' + ('_sample' if a.sample else '')); os.makedirs(seg, exist_ok=True)
lst = []
for i, fr in enumerate(order):
    n = min(max(o['durationInFrames'] for o in groups[fr]), LIMIT - fr)
    out = os.path.join(seg, f's{i:03d}.mp4'); lst.append(out)
    if not os.path.exists(out):
        subprocess.run(compose_cmd(fr, n, out), check=True)
    print(f'  video {i + 1}/{len(order)}', flush=True)
open(os.path.join(seg, 'list.txt'), 'w').write(''.join(f"file '{cat_path(p)}'\n" for p in lst))
vonly = os.path.join(seg, 'video.mp4')
subprocess.run(FF + ['-f', 'concat', '-safe', '0', '-i', os.path.join(seg, 'list.txt'), '-c', 'copy', vonly], check=True)

snds = sorted([o for o in P['overlays'] if o['type'] == 'sound' and o['from'] < LIMIT], key=lambda o: o['from'])
cmd, fc = FF[:], []
for j, o in enumerate(snds):
    st = o.get('styles', {}); dsec = o['durationInFrames'] / FPS
    cmd += (['-stream_loop', '-1'] if st.get('loop') else []) + ['-ss', f'{o["startFromSound"] / FPS:.3f}', '-t', f'{dsec:.3f}', '-i', o['src']]
    ms_ = int(o['from'] / FPS * 1000)
    af = f'[{j}:a]aresample=48000,aformat=channel_layouts=stereo'
    if st.get('volume', 1.0) != 1.0: af += f",volume={st['volume']}"
    if st.get('fadeIn'): af += f",afade=t=in:d={st['fadeIn']}"
    if st.get('fadeOut'): af += f",afade=t=out:st={max(0, dsec - st['fadeOut']):.2f}:d={st['fadeOut']}"
    fc.append(af + f',adelay={ms_}|{ms_}[a{j}]')
fc.append(''.join(f'[a{j}]' for j in range(len(snds))) + f'amix=inputs={len(snds)}:normalize=0:dropout_transition=0,'
          'loudnorm=I=-14:TP=-1.5:LRA=11[aout]')
mix = os.path.join(seg, 'audio.wav')
subprocess.run(cmd + ['-filter_complex', ';'.join(fc), '-map', '[aout]', '-c:a', 'pcm_s16le', mix], check=True)
print('  audio mixed', flush=True)

assp = os.path.join(seg, 'text.ass')
write_ass(assp, hi=int(LIMIT / FPS * 1000))
final = a.out or os.path.join(d, (f'sample_{tid}.mp4' if a.sample else f'final_{tid}.mp4'))
subprocess.run(FF + ['-i', vonly, '-i', mix, '-vf', f'ass={filt_path(assp)}', *h264_args('8M'), '-pix_fmt', 'yuv420p',
                     '-c:a', 'aac', '-b:a', '192k', '-shortest', *(['-t', str(a.sample)] if a.sample else []),
                     '-movflags', '+faststart', final], check=True)
shutil.rmtree(seg)
print('DONE', final)
