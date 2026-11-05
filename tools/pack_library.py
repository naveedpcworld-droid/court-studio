#!/usr/bin/env python3
"""Maintainer tool: pack the Ego-Light transcript library into GitHub-sized files.
  python3 tools/pack_library.py <court-transcript-library dir>
-> library/index.csv (one row per video: metadata + topic/judge tags + opportunity score)
-> library/transcripts/<channel>[-N].jsonl.gz  (each line: {"id","t":[[sec,text],...]})
"""
import csv, gzip, json, os, re, sys
SRC = sys.argv[1]; OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'library')
LIMIT = 40 * 1024 * 1024
opp = {r['video_id']: r for r in csv.DictReader(open(os.path.join(SRC, 'competitor-analysis/analysis/original_opportunities.csv'), encoding='utf-8-sig'))}
cat = list(csv.DictReader(open(os.path.join(SRC, 'catalog.csv'), encoding='utf-8-sig')))
TS = re.compile(r'^\[(\d+(?::\d+){1,2})\]\s*(.*)')
def sec(s):
    p = [int(x) for x in s.split(':')]; return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]
rows, shards = [], {}
def writer(ch):
    st = shards.get(ch)
    if st is None or st['f'].tell() > LIMIT:
        n = 1 if st is None else st['n'] + 1
        if st: st['gz'].close(); st['f'].close()
        name = f'{ch}.jsonl.gz' if n == 1 else f'{ch}-{n}.jsonl.gz'
        f = open(os.path.join(OUT, 'transcripts', name), 'wb')
        st = shards[ch] = dict(n=n, f=f, gz=gzip.GzipFile(fileobj=f, mode='wb', compresslevel=9), name=name)
    return st
for r in cat:
    vid, ch = r['video_id'], r['channel_handle']
    o = opp.get(vid, {})
    row = dict(video_id=vid, channel=r['channel'], channel_handle=ch, title=r['video_title'], url=r['video_url'],
               duration=r['duration'], published=r['published'], views=r['views'], words=r['words'],
               has_transcript='yes' if r['transcript_status'] == 'Available' else 'no',
               score=o.get('score', ''), tier=o.get('tier', ''), court_type=o.get('court_type', ''),
               judges=o.get('judges', ''), themes=o.get('themes', ''), sentence_years=o.get('sentence_years', ''),
               bond_amount=o.get('bond_amount', ''), cop=o.get('cop', ''), outburst=o.get('outburst', ''),
               reasons=o.get('reasons', ''), suggested_title=o.get('suggested_title', ''),
               competitor_analog=o.get('analog_title', ''), analog_views=o.get('analog_views', ''), shard='')
    p = os.path.join(SRC, r['transcript_file']) if r.get('transcript_file') else ''
    if row['has_transcript'] == 'yes' and p and os.path.exists(p):
        lines = []
        for ln in open(p, encoding='utf-8', errors='replace'):
            m = TS.match(ln.strip())
            if m: lines.append([sec(m.group(1)), m.group(2)])
        if lines:
            st = writer(ch); st['gz'].write((json.dumps({'id': vid, 't': lines}, ensure_ascii=False) + '\n').encode()); row['shard'] = st['name']
    rows.append(row)
for st in shards.values(): st['gz'].close(); st['f'].close()
with open(os.path.join(OUT, 'index.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), 'videos,', sum(1 for r in rows if r['shard']), 'with transcripts,', len(set(r['shard'] for r in rows if r['shard'])), 'shards')
