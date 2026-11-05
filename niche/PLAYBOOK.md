# ⚖️ Courtroom Commentary Channel — Complete Playbook

> Analysis date: 2026-11-02. Maine ye sab check kiya: aapki editing-style video (22.6 min screen-recording),
> 13 channels ki 60-60 latest videos (views, duration, titles), 10 competitor videos ke intro + mid sections
> (frames + Whisper transcripts), aur 7 original-source videos.
> Raw data: `courtroom-niche/channels/*.tsv`, `samples/`, `transcripts/`, `style-ref/`.

---

## 0. Aik line mein formula

**Original source channel se court hearing utha lo → uska transcript ChatGPT ko do → 1 hook + 5 commentary paragraphs (har ek ke saath timeline) lo → Clipchamp "Brian Multilingual" (UK) se voice banao → CapCut mein court footage ko neat 2-camera layout mein set karo, har paragraph ki voice uske timeline point pe daalo → auto captions (white + yellow word) → 1080p export.**

Aapki style-video mein exactly yehi hota hai. Is se zyada kuch nahi (no music, no SFX, no memes, no zooms-effects).

---

## 1. Original sources (jahan se video uthani hai)

Ye channels khud bhi court livestreams (Zoom/YouTube court streams) ko re-upload karte hain. Inke paas
**poori hearing** hoti hai, isliye ye hamare raw material hain.

| Channel | Avg views (last 60) | Avg length | Kis cheez ke liye best |
|---|---|---|---|
| @courtwatchers | 78K | 54 min | Lambi civil/family hearings, dashcam twists |
| @GavelGazers | 70K | 19 min | Judge McNally / Simpson, explosive hearings |
| @peopleincourt | 49K | 29 min | Judge Boyd / West, CPS, DWI |
| @CourtCamTV911 | 44K | 15 min | Sentencing ("Judge hands X years") |
| @OSGCourtWatch | 30K | 20 min | Judge Simpson, sovereign citizens, evictions |
| @CreedenceandMikey | 7K | 16 min | Judge Simpson / West (54-A District Court) |
| @LoneWolfUsul | 4K | 40 min | Lambi trials, cop testimony |

**Video kaise chunein (competitors yahi uthate hain):**
- Topics jo sab se zyada chal rahe hain (13 channels ki 780 titles mein ginti): **Sovereign citizen (180)** ≫ cop/police (53) > sentence (29) > bond (22) > probation (20) > contempt (15) > squatter (14) > custody / eviction / DUI.
- Sab se zyada repeat judges: **Judge J. Cedric Simpson** (54-A, Lansing), Judge McNally, Judge West, Judge Boyd, Judge Stevens.
- Hearing mein **ek clear conflict + ek clear payoff** hona chahiye (defendant judge ko taunt kare → contempt / jail / bond barhna / sentence). Payoff na ho to video mat uthao.
- Source video **15–30 min** ki ho (aapki style-video mein source 27:21 tha → final 29:52 bana).

**Download:** aapki video mein `vd6s.net` (YouTube Video Downloader) se 720p MP4 liya gaya. Hamare paas tested tool bhi hai:
```bash
./yt-download/get.sh -q 720 https://youtu.be/<VIDEO_ID>
```

---

## 2. Competitors — ye kya kar rahe hain (verified)

| Channel | Avg views | Avg length | Top video |
|---|---|---|---|
| @AudittheCourt | **373K** | 32 min | 1.5M — "When a Cop's Testimony IMMEDIATELY Backfires in Court!" |
| @Verdictly1 | **141K** | 12 min | 3.1M — "Squatter Thinks She Can KEEP A $1M Home... Gets MASSIVE Reality Check!" |
| @CourtroomAlice | 44K | 16 min | 1.0M — "Sovereign Citizen REFUSES To Remove His Hat—MASSIVE Mistake" |
| @Judge_Reacts | 13K | 25 min | 85K — "Deadbeat SovCit Brings a Complicated Script—Judge Makes Him Look Stupid!" |
| @GavelCases-u8w | 7K | 42 min | 19K — "Sovereign Citizen REFUSES to Admit He's the Defendant — Judge Puts Him in Custody" |
| @CourtLines | 3.5K | 23 min | 20K — "Sovereign Citizen's FAKE Legal Papers FAIL in Court" |

### 2.1 Video ka structure (Verdictly + CourtroomAlice — sab se zyada views wala format)

| Time | Kya hota hai |
|---|---|
| 0:00 – 0:15/0:35 | **Cold open:** hearing ka sab se garam 15–35 sec ka clip (defendant ki badtameezi / judge ka jawab). CourtroomAlice upar "COMING UP..." likhta hai. |
| ~0:17 – 0:55 | **Narrator hook (4–5 lines, ~20–30 sec):** kaun hai, kya kiya, judge ne kya kiya, "ending dekhni padegi" + **"Let's get into it." / "Let's go ahead and dive in."** |
| Phir | Raw hearing (dead parts kaat ke) |
| Har ~3–6 min | **Commentary interjection** (~15–40 sec): kya hua samjhana + opinion + kabhi viewer se sawal |
| End | Judge ka faisla → narrator ka short recap/verdict |

**Asli hook examples (word-for-word, transcripts se):**
- Verdictly: *"This sovereign citizen squatter refused to leave a million dollar home. She walked into Judge Simpson's court, smiling like she had already won. Judge Simpson wiped that smile off real fast. And what he hit her with at the end, she never saw coming."*
- Verdictly: *"This sovereign citizen looked Judge Simpson dead in the eye and asked him where he gets his authority. And Judge Simpson showed him exactly where… I've covered hundreds of these kinds of people, and this guy is genuinely one of the most delusional defendants I've ever seen on this channel. This one does not end well for him at all. Let's get into it."*
- CourtroomAlice: *"This man stood in front of a judge and refused a direct order without blinking. He claimed removing his hat would strip him of some kind of spiritual power. The judge wasn't buying a word of it and called him out for manipulating the court. What happens after that final warning is something you need to see for yourself. Let's go ahead and dive in."*

**Mid-video interjection examples:**
- Verdictly: *"…like that resets anything is actually insane to me. You cannot just take back what you said and act like the judge just forgot you said it 10 seconds ago… Do you think she actually believes her own story, or was she just hoping the judge would let it slide?"*
- CourtroomAlice (end): *"A hat was never beating a judge who's heard every version of that excuse before. One day in jail for defying a direct order multiple times is almost lenient given how many chances he got just to comply."*
- AudittheCourt (legal-explainer type): intro *"In today's episode, we will explore the cross-examination of a police officer who…"*, mid mein *"Under Section 49.04 of the Texas Penal Code, the state cannot secure a DWI conviction by proving only…"*

**Commentary ki tone (rules):**
- 3rd person, past tense, short punchy sentences. Defendant ko "this sovereign citizen / this squatter / this man" bolo, judge ko **naam se** ("Judge Simpson").
- Halki roasting allowed ("most delusional defendant"), lekin gaali nahi; facts hearing se hi.
- Har interjection = **kya hua (1–2 lines) + kyun ghalat/sahi (1 line) + aage kya (tease)**.
- Kabhi kabhi viewer se sawal ("Do you think…?") — comments barhte hain.

### 2.2 Competitors ka frame layout
- 16:9, court ki **2 camera feeds side-by-side** ek strip mein, peeche themed background (dark courtroom wood + flag — Verdictly/AudittheCourt; US flag — CourtLines; blue gradient — GavelCases; dark frame border — CourtroomAlice).
- Choti court-speech subtitles strip ke neeche (GavelCases, Verdictly).
- Commentary ke waqt Verdictly **ek camera full-screen** kar deta hai (jis bande pe baat ho rahi hai).
- Apna chhota watermark (channel naam) footage pe.

> Lekin aapne kaha **"jo editing video mein hai wohi karna hai"** — to neeche Section 4 wala layout hi follow karna hai (wo inhi competitors jaisa hai: background + 2-cam strip + captions).

### 2.3 Title formulas (competitors ke top titles se)
- `[Type of person] [ACTION VERB] The Judge… MASSIVE Mistake!` → "Sovereign Citizen TAUNTS The Judge… MASSIVE Mistake!" (694K)
- `[Type] Thinks [delusion]... Gets MASSIVE/BRUTAL Reality Check!` → (3.1M)
- `He Smirked Thinking It'd Be Probation… Judge Delivers MASSIVE Sentence!`
- `When a Cop's Testimony IMMEDIATELY Backfires in Court!` (1.5M)
- `Judge [Name] [EXPLODES/ERUPTS] on [Lawyer/Prosecutor] …`
- CAPS sirf 1–3 power words pe: TAUNTS, MOCKS, REFUSES, MASSIVE, BRUTAL, INSTANT, DESTROYS, EXPLODES.

---

## 3. Script — ChatGPT step (aapki video jaisa)

### 3.1 Transcript nikaalo
Aapki video mein: YouTube video pe **"...more" → "Show transcript"** → poora transcript select + copy (timestamps ke saath).
(Hamara tool bhi chalega: `scraping-tools/YOUTUBE-TRANSCRIPT.md`.)

### 3.2 ChatGPT prompt — aapki video wala (exact, Roman Urdu)
Transcript paste karke neeche ye likha gaya tha:
```
[mujhe meri es courtroom cases ki script ko fully analyze kr ke es se related top fully engage
wale 5 paras bana do sath mein timeline bhi batao ke kon sa para kis jagah pr daalna hai, top fully
engage wala ho, script se related hon...] FULLY ENGAGE WALA HO... thora sa short and engage hon
```
ChatGPT ka jawab is shape mein aata hai:
```
5 Fully Engaging Courtroom Commentary Paragraphs
Paragraph 1 — Timeline: 1:19–2:50
<~90-110 words>
Paragraph 2 — Timeline: 4:10–7:48
...
Paragraph 5 — Timeline: 20:47–27:16
Timeline Guide: Where to Add Each Paragraph  (table: Paragraph | Insert at video time | Main focus)
```

### 3.3 Same prompt + competitor hook (recommended — taake competitors jaisa intro bhi aa jaye)
```
Below is the full timestamped transcript of a court hearing. Write commentary for a YouTube
courtroom-commentary video.

1) HOOK (60-80 words) for the very start of the video, in this style: "This sovereign citizen
looked Judge Simpson dead in the eye and asked him where he gets his authority. And Judge Simpson
showed him exactly where..." — who the person is, what they did, how the judge reacted, tease the
ending without revealing it, end with "Let's get into it."
Also tell me the best 15-30 second clip (start-end time) to play BEFORE the hook as a cold open.

2) 5 COMMENTARY PARAGRAPHS (80-110 words each), each with "Timeline: start–end" of the part it
talks about. Each = what just happened + why it matters / who is wrong + tease what comes next.
Short punchy sentences, 3rd person, call the judge by name, light roasting is fine, no swearing,
only facts from the transcript. One paragraph may end with a question to the viewer.

3) Timeline Guide table: Paragraph | Insert at video time | Main focus.

Transcript:
<PASTE>
```

---

## 4. Voiceover — Clipchamp (exact settings from your video)

1. `app.clipchamp.com` → new project → **Record & create → Text to speech**
2. **Language: English (United Kingdom)**
3. **Voice: Brian Multilingual**
4. Advanced: default (koi speed change nahi)
5. Text box mein **ek paragraph** paste → Save → **Export → Audio-only → .m4a**, naam `voice1`, `voice2` … `voice5`
6. Har paragraph = alag file. Aapki video mein lengths: 33s, 33s, 33s, 37s, 43s (+ hook ho to `voice0` ~25s).

---

## 5. Editing — CapCut (step-by-step, exactly as in your video)

**Project:** 16:9, 1920×1080, 30 fps.

### 5.1 Source saaf karo
1. Downloaded court MP4 import → timeline pe.
2. **End trim:** source channel ka outro/end screen kaat do (aapki video mein 27:21 → 26:56; red text "If you like the content please hit the like button…" wala hissa delete).
3. Source channel ke apne text overlays (e.g. "Yeah… it's NOT like he negotiated a SWEET plea deal…", "accelerated to 8x speed") **crop karke bahar** nikaal do (next step).

### 5.2 2-camera layout banao (crop trick)
Court stream mein Zoom grid hota hai (judge cam + courtroom cam + defendant ka phone tile).
1. Clip ko **3 tracks pe duplicate** karo (copy-paste upar).
2. **Track A → Crop 4:3 → sirf JUDGE camera** → scale ~67%, frame ke **left** side.
3. **Track B → Crop 4:3 → sirf COURTROOM camera** → **right** side.
4. **Track C → Crop → sirf DEFENDANT ka Zoom tile** (e.g. "Robert's iPhone") → chhota karke (scale ~34%) courtroom cam ke **upar-left corner** mein PiP.
5. Duplicate tracks (B, C) ka **volume 0** — audio sirf ek track se.
6. Teeno select → right-click → **Create compound clip** (ab ek hi "Compound clip1" banta hai, edit asaan).
7. Result: ek wide strip — judge left | courtroom right (defendant PiP), Zoom logo / channel text bahar.

### 5.3 Commentary voices daalo
1. `voice1..5.m4a` import.
2. ChatGPT ke **"Insert at video time"** pe playhead le jao (paragraph ki range ke end ke paas, kisi natural pause pe) → court compound clip ko wahan **split**.
3. Voice clip us split point pe audio track mein rakho.
4. Voice ke neeche ke court piece ko **split karke speed 0.5x** (slow-motion) kiya gaya taake visuals chalte rahen jab tak narrator bole; is hisse ki court audio **mute** (sirf narrator sunai de). Phir normal hearing wapas chal padti hai.
5. Sab 5 voices aise hi. (Hook ho to: cold-open clip → `voice0` → hearing start.)

### 5.4 Background + frame
1. Sab se neeche track: **background image** full 1920×1080. Aapki video mein pehle dark wooden courtroom (Gemini generated) lagaya, phir final mein **dark blue grid** (`MuchaTeeble.jpg`) — dono chalte hain; ek channel ke liye ek fix kar lo.
2. Do tracks: **white thin line PNG** (`image (2).png`) — ek strip ke **upar edge**, ek **neeche edge** (frame border jaisa).
3. Ek track: **white vertical divider PNG** (`Screenshot…png`, rotate 90°, scale ~38%) dono cameras ke **beech** mein — har court segment ke saath (voice wale hisson pe gap).
4. Sab tracks poori video length tak stretch (aapki final length 29:52).

### 5.5 Captions
1. **Text → Auto captions → Spoken language: English → Generate** (poori video ke — court speech + narrator).
2. Style (Apply to all ✔):
   - Font: **System**, size ~7–10
   - Case: **UPPERCASE (TT)**
   - Color: **white**, preset style = **yellow highlight on the current word** (karaoke style: "HEAR YOU **NOW**")
   - **Shadow ON**: black, opacity ~79%, blur ~28%; stroke/thickness ~13
   - Position: strip ke **neeche wali white line ke upar**, center.
   - 2–4 words per line.

### 5.6 Export
**Export → 1080P, Bit rate: Recommended, Codec: H.264, Format: mp4, 30fps.**

---

## 6. Final checklist (har video)
- [ ] Hearing mein clear conflict + payoff hai
- [ ] Source outro + source channel ke text overlays hata diye
- [ ] Judge | Courtroom 2-cam strip + defendant PiP, white top/bottom lines + divider, background
- [ ] Cold open (15–35s) + hook + "Let's get into it."
- [ ] 5 commentary voices (Brian Multilingual, UK) sahi timeline points pe, neeche court footage 0.5x + muted
- [ ] Auto captions: UPPERCASE, white + yellow active word, shadow
- [ ] Title formula (Section 2.3), 1080p mp4

---

## 7. Notes
- Aapki style-video mein **koi background music, SFX, zoom/shake effect, meme ya B-roll nahi** — wo add mat karna.
- Competitors average **12–30 min**; sab se zyada views Verdictly (12 min) aur AudittheCourt (32 min) ko — dono lengths chalti hain, source ki length pe depend.
