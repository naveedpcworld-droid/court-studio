#!/usr/bin/env python3
"""OPTIONAL — fetch the newest court uploads into YOUR copy of the library (runs on your own computer).

  python3 tools/update.py              # check all channels in desk/channels.yml, add new videos + transcripts
  python3 tools/update.py --max-new 20 # cap how many new videos this run
  python3 tools/update.py --channel "@judgestephanieboyd4233"

Nothing here touches the original GitHub repo. New transcripts land in desk/data/ and are picked up by
tools/find_case.py at once. Don't want updates? Just never run this — the library still works.
Want it automatic on GitHub instead? See UPDATES.md (your own copy + AUTO_UPDATE variable).
"""
import argparse, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESK = os.path.join(ROOT, 'desk')

ap = argparse.ArgumentParser()
ap.add_argument('--max-new', type=int, default=40); ap.add_argument('--channel', default='')
a = ap.parse_args()

missing = []
for mod, pkg in (('yaml', 'PyYAML'), ('yt_dlp', 'yt-dlp'), ('youtube_transcript_api', 'youtube-transcript-api')):
    try: __import__(mod)
    except ImportError: missing.append(pkg)
if missing:
    print('installing', ' '.join(missing), '...')
    r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', *missing])
    if r.returncode:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--user', '--break-system-packages', *missing], check=True)

def run(*cmd):
    print('>', ' '.join(cmd), flush=True)
    return subprocess.run([sys.executable, '-m', *cmd], cwd=DESK).returncode

cmd = ['pipeline.ingest', '--max-new', str(a.max_new)] + (['--channel', a.channel] if a.channel else [])
rc = run(*cmd)
run('pipeline.refresh', '--limit', '30')          # retry transcripts that were not ready last time
run('pipeline.build_site')                        # desk/site (optional local dashboard)

import json
p = os.path.join(DESK, 'data', 'index.json')
n = len(json.load(open(p)).get('videos', [])) if os.path.exists(p) else 0
print(f'\ndone. daily-desk videos now: {n}. Search them: python3 tools/find_case.py search --topic ... (new ones show tier NEW)')
sys.exit(rc)
