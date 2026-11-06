#!/usr/bin/env python3
"""Find judge / court videos in the transcript library (10,900+ public court recordings).

  python3 tools/find_case.py topics                         # all topics with counts
  python3 tools/find_case.py judges                         # judges / channels in the library
  python3 tools/find_case.py search --topic "sovereign"     # by topic (fuzzy)
  python3 tools/find_case.py search --judge simpson --topic bond --n 20
  python3 tools/find_case.py search --text "i do not consent"   # exact phrase inside transcripts (slower)
  python3 tools/find_case.py suggest --n 10                 # best unused picks, niche-weighted
  python3 tools/find_case.py hot <video_id>                 # hottest 6-15 min windows inside a long docket
  python3 tools/find_case.py show <video_id> --from 12:30 --to 20:00
  python3 tools/find_case.py use <video_id>                 # mark as used (never suggested again)

Results give the YouTube link with the start time. Feed that to tools/fetch.py with --section
so only the needed part is downloaded. Captions here are YouTube auto-captions: names, case numbers
and sentences can be misheard — always confirm against the video before stating them as fact.
"""
import argparse, csv, gzip, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import license as _lic
_lic.require()                                          # one key = one PC
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'library')
USED = os.path.join(LIB, 'used.json')                      # per-student ledger (git-ignored)

# niche weighting from the competitor study (median-view lift vs channel baseline)
LIFT = {'Cop misconduct / civil rights': 3.0, 'Outburst / contempt': 2.2, 'Sovereign citizen': 1.8,
        'Pro se / self-represented': 1.6, 'Murder / homicide': 1.4, 'Child abuse / children': 1.3,
        'Eviction / housing': 1.3, 'DUI / drunk driving': 1.2, 'Family / custody': 1.2, 'Sentencing': 0.8}
HEAT = {'contempt': 4, 'sovereign': 4, 'jurisdiction': 3, 'interrupt': 3, 'stop talking': 4, 'shut up': 4,
        'outrageous': 4, 'ridiculous': 3, 'nonsense': 3, 'disrespect': 4, 'lying': 3, 'liar': 4, 'yell': 3,
        'handcuff': 4, 'remand': 3, 'take him into custody': 4, 'into custody': 2, 'revoke': 2, 'bond revoked': 3,
        'i do not consent': 4, 'living man': 4, 'no contact': 2, 'escape': 2, 'body cam': 3, 'bodycam': 3,
        'dashcam': 3, 'probable cause': 2, 'lawsuit': 2, 'sanction': 3, 'prison': 1, 'years in': 1, 'deputy': 1}


DESK = os.path.join(ROOT, 'desk', 'data')


def load():
    """backfill library + the newest uploads collected by the daily desk (desk/data, GitHub Actions)."""
    rows = list(csv.DictReader(open(os.path.join(LIB, 'index.csv'), encoding='utf-8')))
    have = {r['video_id'] for r in rows}
    p = os.path.join(DESK, 'index.json')
    if os.path.exists(p):
        for v in json.load(open(p)).get('videos', []):
            if v['id'] in have or v.get('transcript_status') != 'ok' or not v.get('publish_transcript', True): continue
            dur = int(v.get('duration') or 0) or int((v.get('transcript_segments') or 0) * 6)
            rows.append(dict(video_id=v['id'], channel=v.get('channel_name', ''), channel_handle=v.get('channel_handle', '').lstrip('@'),
                             title=v.get('title', ''), url=v['url'], duration=hms(dur), published=v.get('published', '')[:10],
                             views=str(v.get('views') or ''), words='', has_transcript='yes', score='3', tier='NEW',
                             court_type='', judges=v.get('judge', '') or '', themes='|'.join(v.get('topic_labels', [])),
                             sentence_years='', bond_amount='', cop='1' if 'cop_misconduct' in v.get('topics', []) else '',
                             outburst='1' if 'contempt' in ' '.join(v.get('topics', [])) else '', reasons='new upload (daily desk)',
                             suggested_title='', competitor_analog='', analog_views='', shard='desk:' + v.get('transcript_path', '')))
    return rows


def used():
    return set(json.load(open(USED))) if os.path.exists(USED) else set()


def hms(s):
    s = int(s); return f'{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}' if s >= 3600 else f'{s // 60}:{s % 60:02d}'


def parse_t(x):
    p = [int(v) for v in x.split(':')]; return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1] if len(p) == 2 else p[0]


def minutes(d):
    try: return parse_t(d) / 60
    except Exception: return 0


def transcript(row):
    if not row.get('shard'): return None
    if row['shard'].startswith('desk:'):
        d = json.load(open(os.path.join(ROOT, 'desk', row['shard'][5:])))
        return [[int(x['start']), x['text']] for x in d.get('segments', [])]
    with gzip.open(os.path.join(LIB, 'transcripts', row['shard']), 'rt', encoding='utf-8') as f:
        for ln in f:
            if ln.startswith('{"id": "%s"' % row['video_id']):
                return json.loads(ln)['t']
    return None


def niche_score(r):
    base = float(r['score'] or 0)
    th = [t for t in r['themes'].split('|') if t]
    lift = max([LIFT.get(t, 1.0) for t in th] or [1.0])
    return round(base * lift + (2 if r['outburst'] == '1' else 0) + (2 if r['cop'] == '1' else 0), 1)


def match(r, a):
    hay = (r['themes'] + ' ' + r['title']).lower()
    if a.topic and not all(w in hay for w in a.topic.lower().split()): return False
    if a.judge and a.judge.lower() not in (r['judges'] + ' ' + r['title'] + ' ' + r['channel']).lower(): return False
    if a.channel and a.channel.lower() not in (r['channel'] + r['channel_handle']).lower(): return False
    if minutes(r['duration']) < a.min_minutes: return False
    return r['has_transcript'] == 'yes'


def show_row(i, r, extra=''):
    print(f"{i:>3}. [{r['tier'] or '-'}|{niche_score(r):>5}] {r['title'][:80]}\n"
          f"     {r['channel']} · {r['duration']} · {r['published']} · {r['views']} views\n"
          f"     topics: {r['themes'] or '-'}  judges: {r['judges'] or '-'}\n"
          f"     {r['url']}  (id {r['video_id']})" + (f"\n     why: {r['reasons']}" if r['reasons'] else '')
          + (f"\n     like: \"{r['competitor_analog'][:70]}\" ({r['analog_views']} views)" if r['competitor_analog'] else '') + extra)


def hot_windows(lines, top=3, win=600):
    """sliding window over captions -> windows with the most conflict words."""
    if not lines: return []
    end = lines[-1][0]; out = []
    for st in range(0, max(1, int(end - win / 2)), 60):
        seg = [t for s, t in lines if st <= s < st + win]
        txt = ' '.join(seg).lower()
        h = sum(txt.count(k) * w for k, w in HEAT.items())
        out.append((h, st, min(end, st + win), txt))
    out.sort(reverse=True); pick = []
    for h, a, b, txt in out:
        if h and all(abs(a - p[1]) >= win * 0.8 for p in pick): pick.append((h, a, b, txt))
        if len(pick) >= top: break
    return pick


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('arg', nargs='?')
    ap.add_argument('--topic'); ap.add_argument('--judge'); ap.add_argument('--channel'); ap.add_argument('--text')
    ap.add_argument('--n', type=int, default=10); ap.add_argument('--min-minutes', type=float, default=5)
    ap.add_argument('--from', dest='t0'); ap.add_argument('--to', dest='t1'); ap.add_argument('--all', action='store_true')
    a = ap.parse_args(); R = load(); U = used()

    if a.cmd == 'topics':
        from collections import Counter
        c = Counter(t for r in R if r['has_transcript'] == 'yes' for t in r['themes'].split('|') if t)
        for t, n in c.most_common(): print(f'{n:>6}  {t}   (niche lift {LIFT.get(t, 1.0)}x)')
    elif a.cmd == 'judges':
        from collections import Counter
        ch = Counter(r['channel'] for r in R if r['has_transcript'] == 'yes')
        print('CHANNELS:'); [print(f'{n:>6}  {c}') for c, n in ch.most_common()]
        j = Counter(t for r in R for t in r['judges'].split('|') if len(t) > 3)
        print('\nJUDGES named in transcripts:'); [print(f'{n:>6}  {c}') for c, n in j.most_common(40)]
    elif a.cmd in ('search', 'suggest'):
        rows = [r for r in R if match(r, a) and (a.all or r['video_id'] not in U)]
        if a.text:
            ph = a.text.lower(); hits = []
            by_shard = {}
            for r in rows: by_shard.setdefault(r['shard'], {})[r['video_id']] = r
            for sh, vids in by_shard.items():
                if not sh: continue
                if sh.startswith('desk:'):
                    for vid, r in vids.items():
                        ts = [t0 for t0, t in transcript(r) or [] if ph in t.lower()]
                        if ts: hits.append((len(ts), r, ts))
                    continue
                with gzip.open(os.path.join(LIB, 'transcripts', sh), 'rt', encoding='utf-8') as f:
                    for ln in f:
                        d = json.loads(ln)
                        if d['id'] not in vids: continue
                        ts = [s for s, t in d['t'] if ph in t.lower()]
                        if ts: hits.append((len(ts), vids[d['id']], ts))
            hits.sort(key=lambda x: (-x[0], -niche_score(x[1])))
            for i, (n, r, ts) in enumerate(hits[:a.n], 1):
                show_row(i, r, f"\n     \"{a.text}\" x{n} at " + ', '.join(hms(t) for t in ts[:6])
                         + f"\n     jump: {r['url']}&t={ts[0]}s")
            print(f'\n{len(hits)} videos contain "{a.text}"')
            return
        rows.sort(key=niche_score, reverse=True)
        if a.cmd == 'suggest':                             # spread across channels / topics
            seen, pick = {}, []
            for r in rows:
                k = (r['channel_handle'], (r['themes'].split('|') or [''])[0])
                if seen.get(k, 0) >= 1: continue
                seen[k] = 1; pick.append(r)
                if len(pick) >= a.n: break
            rows = pick
        for i, r in enumerate(rows[:a.n], 1): show_row(i, r)
        print(f'\n{len(rows)} shown. Next: python3 tools/find_case.py hot <id>  (to find the case inside a long docket)')
    elif a.cmd == 'hot':
        r = next((x for x in R if x['video_id'] == a.arg), None) or sys.exit('unknown id')
        lines = transcript(r); show_row(0, r)
        for h, s0, s1, txt in hot_windows(lines):
            seg = [(s, t) for s, t in lines if s0 <= s < s1]
            hot = [f'[{hms(s)}] {t}' for s, t in seg if any(k in t.lower() for k in HEAT)][:6]
            print(f'\n  WINDOW {hms(s0)} - {hms(s1)}  heat {h}   ->  fetch.py <project> "{r["url"]}" --section {s0} {s1}')
            for x in hot: print('     ', x[:160])
    elif a.cmd == 'show':
        r = next((x for x in R if x['video_id'] == a.arg), None) or sys.exit('unknown id')
        t0 = parse_t(a.t0) if a.t0 else 0; t1 = parse_t(a.t1) if a.t1 else 10 ** 9
        for s, t in transcript(r) or []:
            if t0 <= s <= t1: print(f'[{hms(s)}] {t}')
    elif a.cmd == 'use':
        U.add(a.arg); json.dump(sorted(U), open(USED, 'w')); print('marked used:', a.arg)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
