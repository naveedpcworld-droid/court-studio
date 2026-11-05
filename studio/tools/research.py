#!/usr/bin/env python3
"""Research for B-roll / legal-explainer videos — find REAL material and keep every source.

  python3 tools/research.py <project> web     "Texas Code of Criminal Procedure article 14.06"   # pages + full text
  python3 tools/research.py <project> news    "Byron Laws DWI Harris County"                     # news articles + text
  python3 tools/research.py <project> wiki    "Gerstein v. Pugh"                                  # Wikipedia article text
  python3 tools/research.py <project> images  "Harris County Criminal Justice Center" --n 6       # photos -> research/img/
  python3 tools/research.py <project> broll   "police officer paperwork"                          # stock video (Pexels) or photo
  python3 tools/research.py <project> frames  120 245 610                                         # stills from the hearing
  python3 tools/research.py <project> sources                                                     # -> research/SOURCES.md

Everything lands in projects/<project>/research/ (text/*.txt with the URL on line 1, img/, broll/) and
is logged in research/sources.json. Use ONLY these texts for quotes, numbers, dates and law excerpts.
Keys (config.env in the studio folder): SERPER_API_KEY (serper.dev, 2,500 free searches),
PEXELS_API_KEY (pexels.com/api, free). Without keys: wiki + frames still work.
"""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from common import proj_dir, STUDIO

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'}


def env():
    cfg = {}
    p = os.path.join(STUDIO, 'config.env')
    if os.path.exists(p):
        for ln in open(p):
            if '=' in ln and not ln.strip().startswith('#'):
                k, v = ln.strip().split('=', 1); cfg[k.strip()] = v.strip().strip('"')
    cfg.update({k: v for k, v in os.environ.items() if k in ('SERPER_API_KEY', 'PEXELS_API_KEY')})
    return cfg


CFG = env()
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:50]


def http(url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def serper(kind, q, num=10):
    key = CFG.get('SERPER_API_KEY')
    if not key: sys.exit('SERPER_API_KEY missing in config.env')
    body = json.dumps({'q': q, 'num': num}).encode()
    return json.loads(http(f'https://google.serper.dev/{kind}', body, {'X-API-KEY': key, 'Content-Type': 'application/json'}))


def page_text(url):
    try:
        raw = http(url, timeout=40)
    except Exception:
        return ''
    if raw[:5] == b'%PDF-':                                  # court filings / manuals are usually PDFs
        try:
            import io, pypdf
            rd = pypdf.PdfReader(io.BytesIO(raw))
            return '\n'.join((pg.extract_text() or '') for pg in rd.pages[:60]).strip()
        except Exception:
            return ''
    try:
        import trafilatura
        return (trafilatura.extract(raw.decode('utf-8', 'replace'), include_comments=False, include_tables=False) or '').strip()
    except Exception:
        return ''


def log_source(d, entry):
    p = os.path.join(d, 'sources.json')
    src = json.load(open(p)) if os.path.exists(p) else []
    if not any(s.get('url') == entry.get('url') and s.get('file') == entry.get('file') for s in src):
        src.append(entry); json.dump(src, open(p, 'w'), indent=1)


def save_text(d, name, url, title, txt):
    os.makedirs(os.path.join(d, 'text'), exist_ok=True)
    f = os.path.join(d, 'text', name + '.txt')
    open(f, 'w').write(f'{url}\n{title}\n\n{txt}\n')
    log_source(d, dict(kind='text', title=title, url=url, file=os.path.relpath(f, d)))
    return f


def main():
    proj, cmd = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    n = 6
    if '--n' in args: i = args.index('--n'); n = int(args[i + 1]); args = args[:i] + args[i + 2:]
    q = ' '.join(args)
    d = os.path.join(proj_dir(proj), 'research'); os.makedirs(d, exist_ok=True)

    if cmd in ('web', 'news'):
        res = serper('search' if cmd == 'web' else 'news', q)
        items = res.get('organic' if cmd == 'web' else 'news', [])[:n]
        print(f'{len(items)} results for: {q}')
        for k, it in enumerate(items):
            url, title = it.get('link'), it.get('title', '')
            print(f"[{k + 1}] {title}\n    {url}\n    {it.get('snippet', '')[:200]}")
            if k < 4:
                txt = page_text(url)
                if len(txt) > 400:
                    f = save_text(d, f'{cmd}-{slug(q)}-{k + 1}', url, title + (f" — {it.get('source', '')} {it.get('date', '')}" if cmd == 'news' else ''), txt)
                    print(f'    -> {os.path.relpath(f, d)} ({len(txt)} chars)')
    elif cmd == 'wiki':
        t = urllib.parse.quote(q.replace(' ', '_'))
        try:
            js = json.loads(http(f'https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&redirects=1&format=json&titles={t}'))
            pg = next(iter(js['query']['pages'].values()))
            txt = pg.get('extract', '')
            url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(pg.get('title', q).replace(' ', '_'))}"
            if txt:
                f = save_text(d, f'wiki-{slug(q)}', url, pg.get('title', q), txt); print('->', os.path.relpath(f, d), len(txt), 'chars')
            else:
                print('no Wikipedia article for', q)
        except Exception as e:
            print('wiki failed:', e)
    elif cmd == 'images':
        os.makedirs(os.path.join(d, 'img'), exist_ok=True)
        res = serper('images', q, num=20).get('images', [])
        got = 0
        for it in res:
            if got >= n: break
            url = it.get('imageUrl', '')
            if it.get('imageWidth', 0) < 700: continue
            try:
                data = http(url, timeout=20)
                if len(data) < 40000: continue
                ext = '.png' if url.lower().endswith('.png') else '.jpg'
                f = os.path.join(d, 'img', f'{slug(q)}-{got + 1}{ext}'); open(f, 'wb').write(data)
                from PIL import Image
                Image.open(f).verify()
                got += 1
                log_source(d, dict(kind='image', title=it.get('title', ''), url=it.get('link', url), image=url, file=os.path.relpath(f, d)))
                print(f'-> {os.path.relpath(f, d)}  ({it.get("imageWidth")}x{it.get("imageHeight")})  {it.get("source", "")}')
            except Exception:
                continue
        print(f'{got} images saved. LOOK at them before using (right place / right person?)')
    elif cmd == 'broll':
        os.makedirs(os.path.join(d, 'broll'), exist_ok=True)
        key = CFG.get('PEXELS_API_KEY'); done = False
        if key:
            try:
                js = json.loads(http(f'https://api.pexels.com/videos/search?query={urllib.parse.quote(q)}&per_page=8&orientation=landscape',
                                     headers={'Authorization': key}))
                for v in js.get('videos', []):
                    fs = sorted([x for x in v['video_files'] if x.get('width') and 1280 <= x['width'] <= 1920], key=lambda x: -x['width'])
                    if not fs or v.get('duration', 0) < 4: continue
                    f = os.path.join(d, 'broll', f'{slug(q)}.mp4'); open(f, 'wb').write(http(fs[0]['link'], timeout=60))
                    log_source(d, dict(kind='broll', title=q, url=v.get('url'), credit='Pexels / ' + v.get('user', {}).get('name', ''), file=os.path.relpath(f, d)))
                    print('->', os.path.relpath(f, d), v.get('duration'), 's  (Pexels:', v.get('user', {}).get('name'), ')'); done = True; break
            except Exception as e:
                print('pexels failed:', e)
        if not done:
            print('no stock video (no PEXELS_API_KEY or nothing found) — saving photos instead')
            sys.argv = sys.argv[:2] + ['images', q, '--n', '2']; main()
    elif cmd == 'frames':
        os.makedirs(os.path.join(d, 'img'), exist_ok=True)
        src = os.path.join(proj_dir(proj), 'src.mp4')
        for t in args:
            f = os.path.join(d, 'img', f'frame-{float(t):07.1f}.jpg')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', t, '-i', src, '-frames:v', '1', '-q:v', '2', f], check=True)
            print('->', os.path.relpath(f, d))
    elif cmd == 'sources':
        src = json.load(open(os.path.join(d, 'sources.json'))) if os.path.exists(os.path.join(d, 'sources.json')) else []
        lines = ['# Sources', '']
        for s in src:
            if s['kind'] == 'text': lines.append(f"- {s['title']}: {s['url']}")
        lines += ['', '## Images / B-roll', ''] + [f"- {s.get('title', '')}: {s.get('url', '')} {s.get('credit', '')}" for s in src if s['kind'] != 'text']
        open(os.path.join(d, 'SOURCES.md'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
