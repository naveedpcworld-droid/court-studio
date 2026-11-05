# script.json — kaise likhna hai (Claude ke liye)

`projects/<name>/transcript.txt` poora parho (times seconds mein hain, case ke shuru se). Phir
`projects/<name>/script.json` likho:

```json
{
  "title": "Sovereign Citizen Claims He Has NO NAME... Judge OBLITERATES Him!",
  "voice": "en-US-BrianMultilingualNeural",
  "cold_open": [51.3, 66.6],
  "hearing": [1.4, 531.0],
  "skip": [[369.5, 446.5]],
  "auto_trim": 2.5,
  "vo": [
    {"id": "hook",  "broll": 16.0, "text": "..."},
    {"id": "p1",    "at": 67.8,    "text": "..."},
    {"id": "p2",    "at": 124.7,   "text": "..."},
    {"id": "outro", "broll": 448.0, "text": "..."}
  ]
}
```

| field | matlab |
|---|---|
| `cold_open` | sab se garam 15-30 sec (defendant ki badtameezi / judge ka jawab). Real audio ke saath sab se pehle chalta hai. Ending (faisla) **kabhi** cold open mein mat do. |
| `hearing` | case kahan se kahan tak (docket call se faisle tak). Uploader ka intro/outro bahar. |
| `highlights` | **hook montage** (cold_open ki jagah): `[[a,b],[a,b],[a,b]]` — 2-4 sab se garam lamhe, har ek 4-10 sec, kul 15-30 sec, real audio, ek ke baad ek. Faisla/ending kabhi nahi. |
| `skip` | hearing ke bore hisse jo poore kaatne hain (length kam karne ke liye). |
| `keep` | **lambi hearing ko chhota karna**: `[[a,b],...]` = sirf ye hisse rakho (main points), baqi sab kat jata hai. `skip` se aasan jab 40-60% katna ho. |
| `auto_trim` | is se lambi khamoshi khud kat jati hai (seconds). 0 = off. |
| `hook` | cold open ke baad narrator. `broll` = kis second ki footage neeche slow chale (koi aisa lamha jismein defendant dikhe). |
| `p1, p2...` | commentary blocks. `at` = hearing ka woh second jahan hearing rok ke ye bolna hai — **kisi sentence ke khatam hone pe** (transcript line ka start time lo). Neeche usse pehle ki footage 0.5x chalti hai. |
| `info` | (T05 News Desk panel + ticker) `{"case_title": "People v. Dallas Williams", "court": "14A-1 District Court, Michigan", "charge": "Unpaid child support", "judge": "Judge J. Cedric Simpson"}` |
| `labels` | name tags (T05, T06, T07, T09, T10, T13): `{"L0": ["JUDGE WOLFE", "COURTROOM"]}` — layout id se (layout.json / layout_check.jpg mein tiles 1,2,3 ka order). Sab layouts ke liye ek jaisa: `"labels_default": [...]`. **Zoom jab bolne wale ke hisaab se tiles ki jagah badalta hai to labels mat do** (ghalat naam aa jata hai). |
| `outro` | faisle ke baad. `broll` = faisle ke paas ka second. |

## Likhne ke rules (competitors se — Verdictly / CourtroomAlice / AudittheCourt)
**Hook (60-80 words, ~25 sec):** kaun hai → kya kiya → judge ne kya kiya → ending ka tease (bataye baghair)
→ **"Let's get into it."**
> "This man walked into court on his own criminal case and told the judge he doesn't have a name. He says
> he's not the defendant. He's the attorney of fact for the defendant... What happened next is one of the
> cleanest shutdowns you'll ever see. Let's get into it."

**Commentary block (70-110 words, ~25-35 sec):** kya hua (1-2 lines) + ye kyun ghalat/sahi hai (law ya
common sense, 1-2 lines) + aage kya hone wala hai ka tease. Kabhi kabhi viewer se sawal.
- Short punchy sentences, 3rd person, past/present tense.
- Judge ko **naam se** ("Judge Wolfe"), defendant ko "this sovereign citizen / this man / [naam]".
- Halki roasting OK, gaali nahi. **Sirf transcript ke facts.** Dates/amounts transcript se.
- Numbers words mein likho ("thirty-three days", "a thousand dollars") — voice behtar bolti hai.

**Outro (70-100 words):** faisla saaf saaf (kya mila, kitna, kab) + 1 line verdict/opinion + comment ka sawal
("Was the judge right...? Let me know in the comments.").

## Pacing — voice kitni, commentary kitni (competitors se naapa)
| | Rule |
|---|---|
| Final length | hearing 20 min se lambi → **10-15 min** final. Hearing 5-10 min → jitni hai (+narration). |
| Hook | highlights 15-30 sec → narrator hook 20-30 sec (60-80 words) → "Let's get into it." Pehle 60 sec mein viewer ko conflict + sawal mil jaye. |
| Narration share | **25-40%** of final video (Verdictly/CourtroomAlice ~25-30%, Audit the Court ~43%). Is se kam = sirf re-upload lagta hai; zyada = log court dekhne aaye hain. |
| Commentary block | har **2-3 min** court ke baad ek, 25-40 sec (70-110 words). Research/B-roll templates mein 60-100 sec tak. |
| Court clips | ek clip 1-4 min, kabhi 5+ min bina rukay nahi. |
| Kya katna | case numbers padhna, scheduling, "unmute yourself", doosre logon ke cases, khamoshi, breakout room. |
| Kya rakhna | defendant ka claim, judge ka sawal/jawab, conflict ka peak, faisla, judge ka aakhri lecture. |
| Outro | faisla saaf + 1 line sabaq + comment ka sawal, 25-35 sec. |
`build.py --dry` length batata hai; narration % = (hook+blocks+outro seconds) / final.

## Kitne blocks?
Har **2-3 min** hearing pe 1 block. 8-10 min video ≈ hook + 3 blocks + outro. 15 min ≈ hook + 5 + outro.
`voice.py` ke baad `build.py --dry` se length dekho aur `skip`/blocks adjust karo.

## Text badla?
Sirf `voice.py` dobara chalao — jo block badla wahi dobara banta hai.
