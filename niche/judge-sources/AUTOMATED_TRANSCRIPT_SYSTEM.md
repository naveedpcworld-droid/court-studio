# Automated Court-Transcript System — Architecture & Build Plan

## 1. What you are actually building

Not “a scraper”. You are building a small **media-intelligence pipeline**:

```
Channel registry
    ↓
New-upload detection
    ↓
Metadata capture
    ↓
Transcript acquisition
    ↓
Normalisation + case/judge/topic extraction
    ↓
Rights/quality gate
    ↓
Database + search
    ↓
Student dashboard + daily digest + alerts
```

The current Ego Light library is the **seed/backfill**. It should not be the production ingestion engine. Production should run server-side, on a schedule, without a visible browser.

## 2. First: separate the three source classes

Do not put these in one bucket.

| Tier | Examples | Use |
|---|---|---|
| **A. Official court / judge feed** | Judge Boyd, Judge Oakley, 252nd District, Hernando, 36th District, Judge Simpson/McNally, Judge Middleton | Primary student library, subject to court rules |
| **B. Licensed media** | Court TV, Law & Crime, Courtroom View Network | Student library only with licence/permission |
| **C. Commentary / competitor** | Judge Fleischer TV, Fleischer Files, Judge Fleischer Fans, the other 14 competitor channels | Internal competitor watchlist only; do not redistribute to students without permission |

Every channel in the registry needs a `rights_status`:

- `public_court_feed`
- `licensed`
- `live_only_no_archive`
- `no_recording_order`
- `commentary_internal_only`
- `unknown_do_not_publish`

A channel can be monitored even when its content cannot be published. Monitoring and publishing are separate permissions.

## 3. Legal gate (do this before writing code)

This is the part that kills most projects.

- YouTube’s Terms prohibit unauthorised downloading. Prefer official APIs, captions, embeds and permissions.
- Court TV / Law & Crime content is copyrighted; a transcript is a derivative work. A licence is needed to redistribute it to students.
- Public court feeds can still have rules: “DO NOT RECORD” (e.g. the Jefferson County Criminal District Court channel), sealed cases, minors, victims, expunged records.
- Commentary channels’ narration and edits are their copyright. Use them internally for pattern research, not as student content.
- If students have accounts, you also have student-data/privacy obligations.
- Get a media/legal review before launch. This document is not legal advice.

**Practical rule:** monitor everything; publish only what is explicitly cleared.

## 4. Channel registry and monitoring

### Registry fields

```
channel_id (UC…), platform, handle, title
source_tier (official/media/commentary)
court, jurisdiction, judge(s)
rights_status, publish_allowed
monitor_enabled, backfill_enabled
language, expected_upload_frequency
last_seen_video_id, last_checked_at
```

### How to detect new uploads

1. **YouTube RSS feed** — free, no API quota:
   `https://www.youtube.com/feeds/videos.xml?channel_id=UC...`
   Poll every 10–15 minutes. Parse new `<entry>` items and dedupe by video ID.
2. **WebSub / PubSubHubbub** — near-real-time push. Needs a public HTTPS callback. Better for scale.
3. **YouTube Data API** — `playlistItems` on the channel’s uploads playlist for metadata/backfill; `videos.list` for stats. Quota is 10,000 units/day by default, so do not use `search.list` for routine polling.
4. **Backfill** — `yt-dlp --flat-playlist` or the uploads playlist, then process oldest/newest in batches.

Important: for judge channels, **past live streams are under `/streams`, not `/videos`**. The monitor must watch both.

## 5. Transcript acquisition

Two paths, in this order:

### A. Captions exist
- Fetch manual or auto captions (VTT/SRV/JSON3).
- Normalise into `{start_ms, end_ms, text}` segments.
- This is cheap and fast.
- Auto-captions still need cleanup/verification for names and numbers.

### B. No usable captions
- Download **audio only** (temporary).
- Transcribe with `faster-whisper` large-v3 (GPU preferred, CPU possible).
- Optional speaker diarisation (pyannote) for judge/defendant/attorney labels.
- Add a custom vocabulary list: judge names, court names, “sovereign citizen”, “probable cause”, “bond”, “arraignment”, etc.
- Delete the audio after transcription unless you have rights to retain it.

Do **not** use an LLM to “rewrite” the transcript. Use it only to structure/segment/classify. The transcript must remain verbatim with timestamps.

## 6. Case/judge/topic extraction

Run a structured extraction step on each transcript. Use JSON schema, not free text.

Suggested schema:

```json
{
  "court": "",
  "jurisdiction": "",
  "judge": "",
  "case_name": "",
  "case_number": "",
  "parties": [],
  "charges": [],
  "procedural_stage": "arraignment|bond|plea|trial|sentencing|appeal|other",
  "outcome": "",
  "sentence": "",
  "hearing_date": "",
  "topics": [],
  "legal_issues": [],
  "why_it_matters": "",
  "viral_hooks": [],
  "confidence": 0.0
}
```

Then derive:

- **What** — case type, charges, legal issue
- **Who** — judge, court, parties
- **When** — hearing date, upload date, procedural stage
- **Why** — why this matters / the conflict
- **Outcome** — sentence, bond, dismissal, plea, verdict
- **Content tags** — cop misconduct, sovereign citizen, DUI, domestic, child, sentencing, etc.

Use a controlled taxonomy, not hundreds of free-text tags. Keep a `taxonomy_version`.

## 7. Storage and search

Minimum schema:

```
channels
videos
transcripts
transcript_segments
cases
video_topics
judges
courts
subscriptions
digest_runs
```

Recommended:

- **Postgres** for metadata and relations
- **pgvector** for “find similar cases”
- **S3 / Cloudflare R2** for transcript files and thumbnails
- **Meilisearch / OpenSearch** for fast full-text search (optional at MVP)
- **Redis + RQ/Celery** for the job queue

Do not store video files. Store only metadata, thumbnails, transcripts and short evidence clips if rights allow.

## 8. Student delivery

### Core views

- “New today”
- Filter by judge / court / case type / topic / stage / source tier
- Search: “sovereign citizen”, “DUI”, “bond revoked”, “Judge Boyd”
- Case page: summary, key quotes, timestamps, source link, confidence, categories
- “Why it matters” box
- “Original source” link
- Save / follow judge or topic

### Daily update

- 6–7 am digest: new transcripts, top 5 cases, new judge activity.
- Email + WhatsApp/Telegram + in-app notifications.
- Personal subscriptions: judge, court, topic, keyword.
- Admin approval gate for anything `rights_status != publish_allowed`.

### Access control

- Student accounts/cohorts.
- No public redistribution of licensed media.
- Audit log of who accessed what.
- Takedown/correction workflow.

## 9. Recommended stack

### Custom (recommended for 20+ channels and students)

- Python **FastAPI**
- **Postgres** + pgvector
- **Redis** + **RQ** or Celery
- **yt-dlp** for backfill/captions
- **faster-whisper** for ASR
- **ffmpeg**
- Claude/OpenAI with JSON-schema output for extraction
- Next.js/React dashboard
- Resend (email), Twilio (WhatsApp), Telegram bot
- Fly.io / Railway / Hetzner + S3/R2
- Sentry + healthchecks

### No-code / low-code (fast pilot, weaker at scale)

- Make.com or Zapier
- Airtable
- Supadata/Apify/YouTube transcript API
- OpenAI/Claude
- Softr/Glide front end

This can validate demand in days, but per-video costs, rights controls and reliability become problems at scale.

## 10. MVP plan

### Week 1 — foundation
- Pick 8–10 launch channels: 4 official courts, 2 media, 2 commentary (internal).
- Build the rights matrix.
- Create channel/video/transcript schema.
- Set up RSS polling + dedupe.

### Week 2 — transcript pipeline
- Caption download + normaliser.
- Whisper fallback + queue/retries.
- Store transcript and segments.
- Manual QA on 20 videos.

### Week 3 — intelligence
- Structured case/judge/topic extraction.
- Controlled taxonomy.
- Search/filter dashboard.
- Confidence scoring and review queue.

### Week 4 — students
- Daily digest.
- Accounts/cohorts.
- “New today”, saved topics, source links.
- Admin publish gate.

### Weeks 5–6 — scale
- Add 20–50 channels.
- Backfill.
- Cost/accuracy review.
- Add WhatsApp/Telegram.
- Add similar-case search.

## 11. Cost model (rough)

Depends mostly on **hours of audio**, not channel count.

- RSS/WebSub monitoring: free
- YouTube metadata API: free within quota
- Captions: cheap
- Whisper GPU: the main variable; 1 hour of audio is minutes on a decent GPU
- LLM extraction: cents per video at current small-model pricing
- Storage: transcripts are small; thumbnails/audio temporary
- Server/DB: tens of dollars/month at MVP

Start with captions wherever possible; run Whisper only for the no-caption minority. That cuts cost dramatically.

## 12. What to do this week

1. Decide the **publishing rights policy**.
2. Choose 8–10 launch channels; keep commentary channels in a separate internal list.
3. Get a YouTube API key, an LLM API key, and a small GPU/worker.
4. Build the registry + RSS poller + dedupe first. No AI yet.
5. Add captions, then Whisper fallback.
6. Add the JSON extraction + dashboard.
7. Run for 14 days; measure cost, accuracy, misses, rights incidents.
8. Only then add students and daily digests.

## 13. What I need from you to build the MVP

- Which 8–10 channels to launch (I recommend: Boyd, Oakley, 36th, Hernando, Court TV, Law & Crime, plus 2 commentary channels for internal comparison).
- Are you allowed to redistribute Court TV/Law & Crime transcripts to students?
- Student count and preferred delivery: web / email / WhatsApp / Telegram.
- Budget for GPU/API.
- Whether you want a custom app or a no-code pilot.

With those answers, the next step is a working pilot: channel registry → new-upload detection → transcript → case card → daily digest.
