#!/usr/bin/env python3
"""Make your OWN template (students). Never edits the built-in T/B templates.

  python3 tools/new_template.py "red-court" --from T02 \\
      --set accent=#E53935 caption.position=below caption.style=box frame.color=#E53935 \\
      --bg my_background.jpg --project <any project with src.mp4> [--at 60]

- Your templates are named S01-..., S02-... (S = student) so they never clash with new T/B templates
  that come in a `git pull` update.
- --from   which template to start from (structure/layout comes from it). Default T01.
- --set    change any template.json field; dot for nested fields (caption.size=64). Numbers / true / false / null work.
- --bg     your own background picture (any size -> fitted to 1920x1080).
- --project  makes preview.jpg from that project so you can SEE it (runs build + render --still).
Then use it like any template:  build.py <project> --template S01   /   render.py <project> --template S01
"""
import argparse, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import TEMPLATES, list_templates, load_template, proj_dir
from PIL import Image, ImageOps


def val(s):
    try:
        return json.loads(s)
    except ValueError:
        return s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('--from', dest='base', default='T01')
    ap.add_argument('--set', nargs='*', default=[]); ap.add_argument('--bg'); ap.add_argument('--project')
    ap.add_argument('--at', type=float, default=60)
    a = ap.parse_args()
    base = load_template(a.base)
    nums = [int(m.group(1)) for d in list_templates() for m in [re.match(r'S(\d+)', d)] if m]
    slug = re.sub(r'[^a-z0-9]+', '-', a.name.lower()).strip('-') or 'my-style'
    tid = f'S{max(nums, default=0) + 1:02d}-{slug}'
    out = os.path.join(TEMPLATES, tid); os.makedirs(out)
    for f in os.listdir(base['dir']):
        if f in ('bg.jpg',) or f.endswith(('.png', '.ttf', '.otf')):
            shutil.copy(os.path.join(base['dir'], f), out)
    t = {k: v for k, v in base.items() if k not in ('dir', 'id')}
    t['name'] = a.name; t['based_on'] = base['id']
    for kv in a.set:
        if '=' not in kv: sys.exit(f'--set needs key=value, got {kv}')
        k, v = kv.split('=', 1); node = t; parts = k.split('.')
        for p in parts[:-1]: node = node.setdefault(p, {})
        node[parts[-1]] = val(v)
    if a.bg:
        ImageOps.fit(Image.open(a.bg).convert('RGB'), (1920, 1080), Image.LANCZOS).save(os.path.join(out, 'bg.jpg'), quality=92)
        t['bg'] = 'bg.jpg'
    json.dump(t, open(os.path.join(out, 'template.json'), 'w'), indent=1)
    print('created', out)
    if a.project:
        short = tid.split('-')[0]; here = os.path.dirname(__file__)
        subprocess.run([sys.executable, os.path.join(here, 'build.py'), a.project, '--template', short], check=True)
        subprocess.run([sys.executable, os.path.join(here, 'render.py'), a.project, '--template', short, '--still', str(a.at)], check=True)
        pv = os.path.join(proj_dir(a.project), f'preview_{tid}.jpg')
        if not os.path.exists(pv):
            pv = next((os.path.join(proj_dir(a.project), f) for f in os.listdir(proj_dir(a.project)) if f.startswith('preview_') and short in f), None)
        if pv: shutil.copy(pv, os.path.join(out, 'preview.jpg')); print('LOOK:', os.path.join(out, 'preview.jpg'))
    print(f'use it:  python3 tools/build.py <project> --template {tid.split("-")[0]}')


if __name__ == '__main__':
    main()
