# B-roll / research templates (B01–B05) — Claude ke liye workflow

Ye templates sirf "rang" nahi: narration ke waqt screen pe **asli research visuals** aate hain
(law ka text + highlight, news article, asli jagah ki photo, charge card, timeline, checklist, quote,
stock B-roll — sab STILL, koi zoom/pan nahi; music nahi) aur hearing ke dauran **speaker-follow** / panels. Video ki taqat **research** hai —
viewer ko law samajh aana chahiye (Audit the Court ke 1.68M views isi wajah se).

| # | Look | Kab |
|---|---|---|
| B01 Case File Explainer | case-file desk bg, paper docs + yellow marker, B&W narration, speaker-follow, **no captions** | default legal explainer |
| B02 Newsroom Investigation | news desk + CASE FILE panel + ticker, dark doc cards, TV photo boxes | case news mein aaya ho |
| B03 Evidence Board | cork board, polaroids with pins, typewriter docs | crime / backstory heavy |
| B04 Law Class | whiteboard, court + **THE LAW notes panel** (script `notes`), checklists | law samjhana main point |
| B05 Documentary | letterbox, film grain, B&W photos, chapter cards, close-up highlights | serious / emotional |

## 1. Research (pehle, script se pehle)
Transcript parho → 3-6 sawal nikaalo: kaunsa charge? kaunsa law/statute? kaunsa Supreme Court case /
legal principle? local process (jaise Harris County DIMS)? koi lawsuit / news? case ka anjaam?
```bash
python3 tools/research.py <p> web    "Texas Penal Code 49.04 DWI 0.15"        # statute text (PDF bhi)
python3 tools/research.py <p> wiki   "Gerstein v. Pugh"                       # landmark case
python3 tools/research.py <p> news   "<defendant name> <county> <charge>"     # news articles
python3 tools/research.py <p> images "Harris County Criminal Justice Center" --n 4
python3 tools/research.py <p> broll  "police officer writing report"          # Pexels stock video
python3 tools/research.py <p> sources                                         # SOURCES.md -> description
```
Sab `projects/<p>/research/` mein (text/, img/, broll/, sources.json).
**HARD RULES:**
- Document beats ka `text` **research/text/** ki files se word-for-word copy karo. Apne alfaaz kabhi
  "quote" bana ke document ki shakal mein mat dikhao. Numbers/dates/case numbers sirf sources se.
- Har image **khud dekho** (Read) — sahi jagah / sahi insaan? Pakka na ho to mat use karo.
  Defendant ki photo internet se mat dhoondo (ghalat insaan ka khatra) — `frame` beat (hearing ka still) use karo.
- News na mile to `article` beat mat banao.
- Description mein `SOURCES.md` ke links + stock credits daalo.

## 2. script.json — B-template fields
Har `vo` block mein `beats` (screen pe kya aaye, kis lafz pe):
```json
{"id": "p1", "at": 52.5, "text": "... In Gerstein versus Pugh, the Supreme Court ...",
 "beats": [
   {"type": "title", "text": "The Law", "sub": "Why probable cause matters"},
   {"type": "doc", "subtitle": "Supreme Court of the United States", "title": "Gerstein v. Pugh, 420 U.S. 103 (1975)",
    "text": "<exact text from research>", "highlight": ["<phrase from text>"], "source": "Source: ...", "at": "In Gerstein"},
   {"type": "court", "t": 52.0, "at": "So probable cause"}
 ]}
```
- `at` = narration ka woh lafz jahan beat shuru ho (pehla beat hamesha 0 pe). Har beat >= ~2.5 sec.
- `highlight` ka pehla phrase **narration mein bhi bolo** — marker usi lafz pe chalta hai.
- Beat types: `doc` `article` `photo` `frame` (`t`, `tile`) `collage` `title` `definition` `quote`
  `timeline` `charge` `checklist` `broll` (`file`) `court` (hearing footage, B&W/slow).
- Ek block mein 2-5 beats; aakhri beat aksar `court` (wapas hearing ki taraf).
Extra fields:
- `"focus": [[src_start, src_end, tile]]` — hearing ke us hisse mein ek camera full screen (jo bol raha hai).
  `layout.py` Zoom ke green border se `speakers` khud nikaalta hai (agar stream mein ho); `focus` likhoge to wo use hoga.
- `"notes": [[src_time, "text"]]` — B04 ka THE LAW panel (hearing ke dauran chalta hai).
- `"info"` — B02 panel. `"labels_default"` — name tags.

## 3. Narration style (B templates)
Legal explainer: 4-5 blocks, 60-100 sec each (hook + law + local process + lawsuit/background + outcome).
Facts → law → is case pe kaise lagta hai. Har claim ka source research mein ho. Opinion kam, samjhana zyada.
Outro: anjaam + sabaq + comment sawal.
