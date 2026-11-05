# Library

- `index.csv` — one row per recording: channel, title, url, duration, published, views, `has_transcript`,
  `score`/`tier` (A best → D), `themes`, `judges`, `sentence_years`, `cop`, `outburst`, `reasons`,
  `competitor_analog` (+views), `shard`.
- `transcripts/<channel>.jsonl.gz` — one JSON per line: `{"id": "<video id>", "t": [[seconds, "caption text"], ...]}`
- `coverage-report.csv`, `missing-transcripts.csv` — which videos had no YouTube captions.
- `used.json` — your own "already made" list (created by `find_case.py use`, not committed).

Source: public YouTube auto-captions of official court/judge channels, collected 3 Nov 2026.
New uploads after that come from `../desk/data/` (daily). Use `../tools/find_case.py`, not these files directly.
