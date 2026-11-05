# B-roll / Legal-Explainer style — breakdown (Audit the Court)

**Video:** "This is What Happens When You Hire the RIGHT Attorney for the Job!" — Audit the Court
(16:54, **1.68M views**, 3 Feb 2026) · https://www.youtube.com/watch?v=1SUszgTZEto
**Original hearing:** Vikky's Court Watch `LQsOkh6GyA0` (description link — ab **private**). Wohi hearing
Trial World pe mili: https://youtu.be/Nh4eWBh5wjA (10:38, transcript match ✅).
**Case:** State of Texas v. **Byron Reginald Laws** — DWI (BAC > .15, 5 Oct 2021), hearing 20 Mar 2025,
**Judge David Fleischer**, Harris County Criminal Court at Law No. 5, Houston. Defense: Anna Eady.
Issue: kya probable cause sirf sworn **DIMS** report se hoga (offense report se nahi)? Judge: **no probable cause**.
Note: kam az kam 6 copycat channels ne yahi Audit the Court video copy ki hai (same length 16-17 min).

Analysis: 254 frames (har 4 sec) khud dekhe + Gemini (Bulk Vision AI) timeline + dono videos ki
transcripts align ki.

---

## 1. Original vs edit — kya badla

| | Original (Trial World / Vikky) | Audit the Court edit |
|---|---|---|
| Length | 10:38 | 16:54 |
| Layout | poori video ek hi static 2-cam Zoom strip, kaala bg | 2-cam strip **wood + flag bg, green borders** + bolne wale ka **full-screen single cam** (usi tile ka crop) |
| Court footage use | — | **~9:30 of 10:38 (≈90%), bilkul same order**; sirf pehle 27 sec aur "give me 5 minutes" break kata |
| Narration | — | **4 blocks, ~7.3 min total (≈43% of video)** |
| Extra visuals | — | documents + highlights, case law, statutes, location photos, stock B-roll, definition cards, press footage |
| Captions | — | **koi subtitles nahi** (sirf Zoom ke original name labels) |
| Music | — | halka orchestral bed **sirf narration ke neeche**; court audio raw |

## 2. Video ka structure (timeline)

| Time | Block | Kya dikhaya |
|---|---|---|
| 0:00–0:05 | Intro | 3D "AUDIT THE COURT" logo (wood + flag), **DISCLAIMER card** |
| 0:05–1:57 | **Narration 1 — setup (1:52)** | date → defendant ka **framed clip on blurred bg** → **courthouse photo** (Harris County Criminal Justice Center, Ken Burns) → **charging document** (BAC line yellow highlight) → B&W split-screen → **Gerstein v. Pugh (1975)** opinion page, blue/yellow marker highlights → **Tex. Code Crim. Proc. art. 14.06** text highlight → complaint again → attorney ka framed shot |
| 1:57–4:46 | Court 1 | strip ↔ full-screen speaker cuts (attorney / judge) har 5-20 sec |
| 4:46–6:39 | **Narration 2 — "DIMS kya hai" (1:53)** | court **B&W freeze** → **DIMS manual** cover + pages (tilted paper on blurred desk), step-by-step highlights ("Contact an assistant D.A.", "Be specific") → **stock B-roll**: woman typing + scales, police officers with papers |
| 6:39–10:05 | Court 2 | same speaker-follow cutting |
| 10:05–11:20 | **Narration 3 — lawsuit (1:15)** | B&W freeze → **Lomas v. Harris County** case summary highlight → stock "LEGAL" scrabble tiles → **Settlement Agreement** → **Final Consent Judgment** clause highlights (blue) |
| 11:20–14:02 | Court 3 — ruling | judge close-up full screen for the warning to defendant ("don't kill someone on the road") → strip |
| 14:02–16:24 | **Narration 4 — aftermath + lesson (2:20)** | complaint doc → **"Grand Jury" definition card** (US Courts logo) on courtroom bg → **CCP ch. 20A** statute → stock: oath at podium, judge reading → **Harris County DA press-conference footage** → **Motion to Dismiss** (real filed doc, highlight "Court found no probable cause") → defendant clip → stock scales/gavel/police → Gerstein again → "LAW" tiles |
| 16:24–16:54 | Outro | white logo sting → branded end card |

## 3. Techniques (aur kitni baar)

1. **Narration = legal research, opinion nahi.** Har block ek sawal ka jawab: kaunsa law, kaunsa Supreme
   Court case, local system (DIMS) kaise kaam karta hai, kaunsa lawsuit, aage kya hua (motion to dismiss,
   re-file nahi hua). Facts + citations; description mein **saare sources ke links**.
2. **Real public documents** (~20 shots): charging instrument, motion to dismiss, court opinion, statutes,
   DIMS manual, settlement/consent judgment. Paper page **halka tilted**, grey/blurred desk bg, **slow zoom
   ya pan**, aur jo line narrator bol raha hai us pe **marker highlight animation** (yellow + blue).
3. **Speaker-follow cutting from the SAME camera** (~25 cuts): jab attorney bole → courtroom tile full
   screen; judge bole → judge tile full screen; baat-cheet → 2-cam strip. Zoom ka **green active-speaker
   border** isi ka signal hai.
4. **B&W freeze** — har narration block court footage ke **black & white** ho jane se shuru aur khatam (4×).
5. **Stock B-roll** (~10 shots, 4-8 sec, slow push-in): police paperwork, scales of justice, gavel, scrabble
   LAW/LEGAL, typing, oath. Generic legal mood — sirf jab specific visual na ho.
6. **Location / real-world footage**: courthouse exterior photo, DA press conference clip.
7. **Definition card**: white card + source logo ("Grand Jury — ..."), courtroom bg.
8. **Person "photo"**: defendant ka hearing frame, blurred-bg ke upar framed (mugshot ki jagah).
9. **Branding**: logo intro, disclaimer, outro end card. Har shot pe consistent wood+flag bg.
10. **No captions, no SFX** (bas soft whoosh doc transitions pe), music sirf narration mein.

Ratio: **~57% court / ~43% narration**, aur narration ke 100% waqt screen pe koi "evidence" visual hota hai
(document / photo / B-roll), kabhi khaali talking nahi.

## 4. Hamare pipeline mein "B-roll / Legal Explainer" template (T15) — kya banana hoga

| Hissa | Kaise |
|---|---|
| **Research** (`research.py`) | case se keywords (naam, court, county, charge, legal issue) → SearXNG/Serper se news + courthouse photos; **CourtListener / Justia** API se case law text; **Cornell LII / state code sites** se statute text; Wikipedia/Wikimedia se location photos. Sab `research/` folder + `sources.json` (description ke links ke liye). |
| **Beats** in script.json | har narration paragraph ke visuals: `{"type":"doc","text":..., "highlight":[...]}`, `photo`, `broll` (query), `definition`, `court_freeze` |
| **Document renderer** | text/PDF page → paper card (tilt, shadow, blurred desk bg), slow zoom, **highlight sweep** word timing se sync (PIL frames ya HTML capture) |
| **Stock B-roll** | Pexels / Pixabay free API (query per beat), Ken Burns |
| **Definition card** | template card + text |
| **Speaker-follow** | layout tiles ke **green Zoom border** detect karke active speaker → us tile ka full-screen; warna 2-cam strip |
| **B&W freeze** | narration ke start/end pe (engine mein `vo_style: bw` already hai) |
| **Music bed** | narration ke neeche low-volume (royalty-free) |
| **Narration** | 4-5 lambe blocks (1-2 min), legal-explainer tone, sources ke saath |

**Bari baat:** is style ki asal taqat editing nahi, **research** hai. 1.68M views isliye ke viewer ko law
samajh aata hai (Gerstein v. Pugh, DIMS, Lomas lawsuit). Isliye research step mein Claude/Gemini ko har
claim ka source dhoondna hoga, aur ghalat-fact ka risk sab se bara hai.
