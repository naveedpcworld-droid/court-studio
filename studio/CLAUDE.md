# ⚖️ Courtroom Studio — court hearing → viral commentary video (Claude ke liye instructions)

Ye folder ek poori pipeline hai: **original court hearing** (YouTube link ya file) se **competitor jaisi
commentary video** banana — cold open, narrator hook, beech mein commentary, outro, karaoke captions,
6 ready templates mein se kisi ek mein. Student ko sirf link deni hai aur 2 sawalon ke jawab.
Baaki sab tum (Claude) khud karo. Student ko commands chalane ko **mat** kaho.

Pehli dafa? Pehle `docs/SETUP.md` ke checks chalao (python3, ffmpeg+libass, yt-dlp, faster-whisper, edge-tts>=7.3).

---

## 1. Shuru mein student se ye 3 cheezein pucho (ek hi message mein)

1. **Source video** — original court hearing ka YouTube link (ya local file). **Link nahi hai / sirf topic ya judge bataya** → repo root ki `tools/find_case.py` se library mein dhoondo (root `CLAUDE.md` section 1) aur `fetch.py --section` use karo. 2-3 ghante ki live-stream
   bhi chalegi; usme se best case tum khud nikaaloge.
2. **Template** — `templates/ALL-TEMPLATES.jpg` student ko dikhao (SendUserFile ho to bhejo). Har template
   ka `preview.jpg` dikhata hai wo **1 camera / 2 cameras / 3+ Zoom tiles / commentary** pe kaisa lagta hai,
   aur `sample.mp4` 45 sec ka example hai. Source ke hisaab se suggest bhi karo (layout.py ke baad pata chalta
   hai kitni cameras hain):

   | # | Template | Structure | Best for |
   |---|---|---|---|
   | T01 | Classic Strip | 2 cams side-by-side, white lines, blue grid (CapCut tutorial wala) | 2 cams — sab se safe |
   | T02 | Courtroom Wood + Gold | gold frame, wood bg, captions **neeche**, "COMING UP..." | 2 cams (Verdictly look) |
   | T03 | American Flag Boxes | do alag boxed cams + shadow, Impact captions neeche | 2 cams (CourtLines look) |
   | T04 | Noir Breakdown | commentary pe footage **black & white** + BREAKDOWN tag, box captions | koi bhi |
   | T05 | TV News Desk | footage box + right **CASE FILE panel** (case/court/charge/judge) + title ticker | 1-2 cams |
   | T06 | Spotlight + Side Cams | 1 bari camera + right column mein baqi log | 3+ / Zoom hearings |
   | T07 | Full Bleed + Pop Words | edge-to-edge footage, ek ek **bara word** caption | **1 camera** (fixed courtroom cam / akela judge) |
   | T08 | Cinematic Letterbox | 2.39:1 film bars, serif captions, B&W commentary | 1-2 cams, dramatic cases |
   | T09 | Courtroom + Big PiP | wide courtroom full screen + judge bara PiP | 2 cams jismein ek wide shot |
   | T10 | Zoom Gallery Grid | sab tiles ek grid mein + name tags | 4-6 log Zoom par |
   | T11 | Paper Cards | light beige theme, white cards + shadow, yellow box captions | 2 cams, clean look |
   | T12 | Focus Commentary | narration pe ek camera **full-screen zoom-in** + COMMENTARY tag | 2 cams (Verdictly style) |
   | T13 | Versus Split | do halves, naam plates + **VS** badge | 2 cams — labels zaroori |
   | T14 | Minimal Black | bari cameras, koi frame nahi | 2 cams, max footage |

   **B-roll / research templates (B01–B05)** — `templates/ALL-BROLL-TEMPLATES.jpg`. Narration ke waqt
   asli research visuals (law text + highlight, news, photos, charge/timeline/checklist cards, stock B-roll):

   | # | Template | Kab |
   |---|---|---|
   | B01 | Case File Explainer | default legal explainer (Audit the Court type) |
   | B02 | Newsroom Investigation | case news mein aaya ho |
   | B03 | Evidence Board | crime / backstory heavy |
   | B04 | Law Class | law samjhana main point |
   | B05 | Documentary | serious / emotional case |

   Student B template chune to **pehle research karo** — poora tareeqa `docs/RESEARCH-BROLL.md` (HARD rules wahan).

   Har template har source sambhalta hai: portrait phone video ya ajeeb size wali camera slot mein
   **blurred fill** ke saath aati hai (kabhi stretch/face-cut nahi).
3. **Length** — kitni lambi video chahiye? (e.g. 8-10 min · 12-15 min · 18-25 min · "jitna case hai")

Student jawab na de to: 1 camera → **T07**, 2 cameras → **T01**, 3+ → **T06**, length = "jitna case hai".

## 2. Pipeline (sab tum chalao, folder ke root se)

Ye commands `studio/` folder ke andar se chalao. Project ka naam chhota slug rakho (e.g. `wolfe-attorney-of-fact`). Sab files `projects/<name>/` mein.

```bash
python3 tools/fetch.py   <name> "<url or file>"        # download + transcribe (lambi video = waqt lagta hai)
python3 tools/cases.py   <name>                         # cases dhoondo -> cases.txt
python3 tools/cases.py   <name> --pick N                # best case kaato (ya --all / --range a b)
python3 tools/layout.py  <name>                         # cameras ke crop + full-screen moments
#   -> projects/<name>/layout_check.jpg KHUD dekho: laal boxes cameras pe hain? warna layout.json edit karo
#   (tum) script.json likho  — docs/SCRIPT-GUIDE.md ke mutabiq
python3 tools/voice.py   <name>                         # Brian Multilingual narrator + word timings
python3 tools/build.py   <name> --template T05 --dry     # final length check -> skip/auto_trim se adjust
python3 tools/build.py   <name> --template T05
python3 tools/render.py  <name> --template T05 --still 60  # ek frame dekh lo (preview_T05.jpg)
python3 tools/render.py  <name> --template T05          # -> projects/<name>/final_T05.mp4
python3 tools/thumbnail.py <name> frames                # chehron wale frames -> thumbs/sheet.jpg (KHUD dekho)
python3 tools/thumbnail.py <name> frames --at 520 615   # jab defendant bolta hai us waqt ke frames
python3 tools/thumbnail.py <name> make --left thumbs/frames/c0_04.jpg --right thumbs/frames/c0_09.jpg \
        --text "CORPORATE FICTION?!" --highlight "FICTION?!" --sub "JUDGE SAYS NO"   # ChatGPT -> thumbs/thumb_1.jpg
```
Lambi commands (fetch on long video, render) background mein chalao.

## 3. Case chunna (2-3 ghante ki video ho to)
`cases.txt` mein har case ka time, length, opening lines aur **heat** (jhagre wale alfaaz) hota hai.
Tum khud best case chuno — student se mat pucho — aur usay **1 line mein batao kyun**:
- **Ek clear conflict + ek clear payoff** (defendant judge ko challenge kare → contempt / custody / jail /
  bond barhna / sentence). Payoff na ho to agla case.
- Sab se zyada chalne wale topics: **sovereign citizen** ≫ cop testimony > sentencing > bond > contempt >
  squatter/eviction > custody > DUI. (Full research: `../niche/PLAYBOOK.md`)
- Case kam az kam **5-6 min** ka ho. Bahut chhota ho to agla.
- Zaroorat ho to `transcript_full.txt` ka woh hissa parh ke confirm karo.
Docket call na mile (sirf 1 case) to `--all`. Ghalat boundary ho to `--range start end` (seconds).

## 4. Length kaise hit karni hai
`build.py --dry` final length batata hai. Final ≈ cold open + saari narration + bachi hui hearing.
- **Lambi** aa rahi hai → `script.json` mein `"skip": [[a,b], ...]` daalo (bore hisse: date setting,
  khamoshi, doosre logon ki baatein) ya `"auto_trim": 1.5` (khamoshi zyada kaato).
- **Chhoti** aa rahi hai → zyada commentary blocks (har ~2 min hearing pe ek) aur thore lambe paragraphs
  (max ~110 words). Hearing jitni hai utni hi rahegi — bharti na karo.
- ±1 min theek hai.

## 4b. Voice (narrator) — student ki marzi
Default **edge** = FREE (Brian Multilingual, koi key nahi). Behtar/apni awaaz chahiye to `config.env` mein:
`VOICE_PROVIDER=ai33` + `AI33_KEY` + `AI33_VOICE` (ai33.pro, ElevenLabs voices sasti) ya
`VOICE_PROVIDER=elevenlabs` + `ELEVENLABS_KEY` + `ELEVENLABS_VOICE`. Test: `python3 tools/voice.py --test ai33 "hello"`.

## 4c. Thumbnail (ChatGPT, student ka apna account) — har video ke saath
1. `thumbnail.py <name> frames` → `thumbs/sheet.jpg` **khud dekho**: judge ka sakht/react chehra + defendant ka
   bolta/hairaan chehra (aankhein khuli). Zoom speaker-view mein defendant tab dikhta hai jab woh bolta hai →
   transcript se uske time lo aur `--at` se frames nikaalo.
2. Text = **2-5 lafz**, competitor style slang/quote: defendant ka apna ajeeb lafz ("CORPORATE FICTION?!",
   "NO NAME?!", "I DO NOT CONSENT"), ya natija ("INSTANT REGRET", "WRONG JUDGE", "BRO REALLY SAID THAT 💀").
   `--highlight` = yellow lafz, `--sub` = chhota red label (faisla). Jhoota claim nahi.
3. `make` ChatGPT ko dono photos **attach** karke bhejta hai (photos attach na hon to send hi nahi karta),
   ChatGPT chehre upscale + typography karta hai → `thumbs/thumb_N.jpg` 1920x1080.
4. Result **khud dekho**: wohi log? spelling sahi? arrow sahi chehre pe? Ghalat → `thumbnail.py <name> fix "..."`.
Pehli dafa: `cd ../thumbnail-gpt && npm install && node open.js` → student us window mein ChatGPT login kare
(image generation wala account). Window khud khulti hai — student ka apna Chrome nahi.

## 5. Video ke baad — upload pack (zaroor do)
`projects/<name>/upload.md` banao — `docs/TITLES-SEO.md` ke formulas se:
- **3 title options** (competitor formulas), recommended pehle
- **Description** (template wala), **tags** (15-20), **thumbnail idea** (text + kis face ka frame),
  **pinned comment** (sawal)
Phir student ko final video + upload.md bhejo (SendUserFile ho to), aur 2-3 lines: kaun sa case,
kyun, template, length.

## Qaide (HARD)
- Sirf jo hearing mein hua — **facts transcript se**. Naam (judge/defendant) transcript ya source title se;
  pakka na ho to "the judge" / "this defendant".
- No music, no SFX, no memes — style simple hai (competitors + tutorial yahi karte hain).
- Commentary ke waqt court audio mute + footage 0.5x — ye build khud karta hai.
- Gaali/insult nahi; halki roasting theek ("most delusional defendant I've seen").
- Source channel ka halka watermark rehta hai — normal hai.

## Files
`tools/` scripts (`layouts.py` = template structures) · `templates/T01..T14/` (template.json, bg.jpg, preview.jpg, sample.mp4) ·
`docs/SETUP.md` install · `docs/SCRIPT-GUIDE.md` script.json likhna · `docs/TITLES-SEO.md` titles/description ·
`docs/RESEARCH-BROLL.md` B-template research · `../niche/PLAYBOOK.md` niche research · `projects/` kaam.
