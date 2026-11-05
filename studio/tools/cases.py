#!/usr/bin/env python3
"""Step 2 — split a long court stream into individual cases and pick one.

  python3 tools/cases.py <project>                 # list cases -> cases.txt (read it, pick the best)
  python3 tools/cases.py <project> --pick 3        # cut case 3 -> src.mp4 + tx.json + transcript.txt
  python3 tools/cases.py <project> --range 612 1490   # cut any time range (seconds) instead
  python3 tools/cases.py <project> --all           # whole video is one case

Case boundaries come from docket calls in the transcript ("State versus ...", "case number",
"in the matter of", "next case", file numbers like 24-CR-1234). Each case gets a "heat" score
from conflict words (contempt, custody, sovereign, warrant, ...) to help choose.
"""
import argparse, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import proj_dir, save_json, load_json, h264_args

CALL = re.compile(r"\b((state|people|commonwealth|city|county|united states|government)( of [a-z]+)?,? (versus|vs\.?|v\.?)\s+[a-z]"
                  r"|case (number|no\.?)\b|in the matter of\b|file number\b|next (case|matter|up)\b|calling (the )?(case|matter)\b"
                  r"|\b\d{2}[\s-]?(cr|cf|cm|gf|tr|fh|ct|dv|sc|cv)[\s-]?\d{2,})", re.I)
HEAT = ['contempt', 'custody', 'jail', 'remand', 'warrant', 'revoke', 'sovereign', 'jurisdiction', 'outrageous',
        'interrupt', 'stop talking', 'deputy', 'handcuff', 'bond', 'sentence', 'years', 'prison', 'lying', 'liar',
        'disrespect', 'arrest', 'attorney of fact', 'living man', 'trust', 'consent', 'ridiculous', 'nonsense',
        'probation violation', 'no contact', 'victim', 'escape', 'take him', 'cuff', 'shut', 'yell']

ap = argparse.ArgumentParser()
ap.add_argument('project')
ap.add_argument('--pick', type=int); ap.add_argument('--range', nargs=2, type=float); ap.add_argument('--all', action='store_true')
ap.add_argument('--min-gap', type=float, default=45, help='min seconds between two case calls')
a = ap.parse_args()
d = proj_dir(a.project)
TX = load_json(os.path.join(d, 'tx_full.json'))
total = TX[-1]['e'] if TX else 0


def find_cases():
    starts = [0.0]
    for s in TX:
        if CALL.search(s['t']) and s['s'] - starts[-1] >= a.min_gap:
            starts.append(max(0.0, s['s'] - 1.0))
    cases = []
    for i, st in enumerate(starts):
        en = starts[i + 1] if i + 1 < len(starts) else total
        segs = [s for s in TX if st <= s['s'] < en]
        text = ' '.join(s['t'] for s in segs)
        low = text.lower()
        heat = sum(low.count(k) for k in HEAT)
        words = len(text.split())
        cases.append(dict(n=i + 1, start=round(st, 1), end=round(en, 1), minutes=round((en - st) / 60, 1),
                          words=words, heat=heat, opening=' '.join(s['t'] for s in segs[:4])[:300],
                          hot_lines=[f"[{int(s['s'] // 60):02d}:{int(s['s'] % 60):02d}] {s['t']}" for s in segs
                                     if any(k in s['t'].lower() for k in HEAT)][:8]))
    return cases


def cut(st, en):
    src = os.path.join(d, 'src_full.mp4'); out = os.path.join(d, 'src.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{st:.2f}', '-to', f'{en:.2f}', '-i', src,
                    *h264_args('10M'), '-c:a', 'aac', '-b:a', '192k', out], check=True)
    tx = []
    for s in TX:
        if st <= s['s'] < en:
            tx.append({'s': round(s['s'] - st, 2), 'e': round(min(s['e'], en) - st, 2), 't': s['t'],
                       'w': [[round(w0 - st, 2), round(min(w1, en) - st, 2), w] for w0, w1, w in s['w'] if st <= w0 < en]})
    save_json(tx, os.path.join(d, 'tx.json'))
    with open(os.path.join(d, 'transcript.txt'), 'w') as f:
        for s in tx:
            f.write(f"[{s['s']:7.1f}] {s['t']}\n")
    save_json({'from': st, 'to': en}, os.path.join(d, 'case.json'))
    print(f'cut {st:.1f}-{en:.1f}s ({(en - st) / 60:.1f} min) -> src.mp4, tx.json, transcript.txt (times in seconds)')
    print('NEXT: python3 tools/layout.py', a.project)


if a.all:
    cut(0, total)
elif a.range:
    cut(*a.range)
elif a.pick:
    cs = load_json(os.path.join(d, 'cases.json'))
    c = cs[a.pick - 1]; cut(c['start'], c['end'])
else:
    cs = find_cases()
    save_json(cs, os.path.join(d, 'cases.json'))
    with open(os.path.join(d, 'cases.txt'), 'w') as f:
        f.write(f'{len(cs)} case(s) found in {total / 60:.1f} min. heat = conflict words (higher = more drama)\n')
        top = sorted([c for c in cs if c['minutes'] >= 3], key=lambda c: -c['heat'])[:8]
        f.write('SHORTLIST (>= 3 min, by heat) — read these in the transcript, heat is only a hint: '
                + ', '.join(f"#{c['n']} ({c['minutes']}m, heat {c['heat']})" for c in top) + '\n\n')
        for c in cs:
            f.write(f"CASE {c['n']}  {int(c['start'] // 60)}:{int(c['start'] % 60):02d} - {int(c['end'] // 60)}:{int(c['end'] % 60):02d}"
                    f"  ({c['minutes']} min, {c['words']} words, heat {c['heat']})\n  opening: {c['opening']}\n")
            for h in c['hot_lines']:
                f.write(f'    {h}\n')
            f.write('\n')
    print(open(os.path.join(d, 'cases.txt')).read()[:6000])
    print('Read cases.txt, choose the case with a clear conflict + payoff, then: python3 tools/cases.py',
          a.project, '--pick N   (or --all if it is one case)')
