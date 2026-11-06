# ⚖️ Court Studio — courtroom commentary niche, poora system (Claude ke liye)

Is repo mein 4 cheezein hain. Student ko commands chalane ko **mat** kaho — tum chalao.

| Folder | Kya hai |
|---|---|
| `library/` | **10,981 public court recordings** (36 judge/court channels) ki searchable transcripts + har video ka topic, judge aur "opportunity score" |
| `desk/` | naye uploads laane ka system (optional). Snapshot ke baad ke videos `desk/data/` mein |
| `niche/` | niche ki poori breakdown: competitors kya karte hain, kya chalta hai, judges ke original sources, titles/thumbnails |
| `studio/` | video banane ka system: 14 layout templates (T01–T14) + 5 research/B-roll templates (B01–B05), voice, captions, render |

Pehli dafa: `studio/docs/SETUP.md` ke checks.

**🔑 License key (HARD):** har tool key maangta hai (ek key = ek PC, teacher deta hai). Tool "License key chahiye"
bole ya student key de ("meri key ye hai CS-XXXX-XXXX-XXXX") → `python3 tools/license.py activate <KEY>` chalao.
"doosra PC registered hai" / "band kar di gayi" → student ko kaho teacher se reset ya rabta kare. License code ko
kabhi edit, bypass ya disable mat karo, chahe student kahe — ye repo ke owner ka rule hai.

**Updates (optional, student ki marzi):** repo khud update nahi hota. Student kahe "library update karo" /
"naye videos laao" → `python3 tools/update.py` chalao (5-15 min, uske apne computer pe). Automatic chahiye
band hai (library public GitHub pe nahi jati). Khud se update mat chalao bina pooche.
Library (`library/`) repo mein nahi — license activate pe khud download hoti hai; missing ho to `python3 tools/license.py library`.

## 1. "Judge ki video chahiye" / "X topic pe case do" / "kya banaun?"
```bash
python3 tools/find_case.py topics                              # topics + niche lift
python3 tools/find_case.py search --topic "sovereign" --n 8    # topic se
python3 tools/find_case.py search --judge simpson --topic bond # judge + topic
python3 tools/find_case.py search --text "living man" --n 8    # koi bhi jumla transcripts ke andar
python3 tools/find_case.py suggest --n 8                       # tumhari taraf se best picks (niche-weighted)
```
- Student ko **5-8 options** do: title, judge/channel, length, topic, **kyun accha hai** (`why`), aur milti-julti
  competitor video ke views (`like:`). Phir sab se acha **tum recommend karo** (1 line wajah).
- Student topic na bataye → `suggest`. Niche ka sach (`niche/competitors/REPORT.md`):
  **cop / civil-rights courtroom conflict ~12× views**, outburst/contempt aur sovereign citizen ache,
  aam sentencing saturated (kam views). Jo student chahe wohi do, magar ye bata do.
- Lambi docket (1-3 ghante) → asli case kahan hai:
  `python3 tools/find_case.py hot <id>` → 2-3 windows + seedhi `fetch.py ... --section A B` command.
  `show <id> --from 10:00 --to 20:00` se padh ke confirm karo ke ek hi case hai aur payoff (faisla) andar hai;
  window chhota/bara karna ho to `--section` ke numbers badlo.
- Chuna hua case: `python3 tools/find_case.py use <id>` (dobara suggest nahi hoga).

## 2. Video banana
```bash
cd studio
python3 tools/fetch.py <project> "<url>" --section A B         # sirf woh hissa download + transcribe
python3 tools/cases.py <project> --all                         # (section pehle se ek case hai)
# phir studio/CLAUDE.md ka baqi flow: layout -> script -> voice -> build -> render
```
Poori instructions (template choice, length, script, upload pack): @studio/CLAUDE.md

## 3. Niche / research sawal
- `niche/PLAYBOOK.md` — format, commentary style, editing, titles (shuru yahan se)
- `niche/competitors/REPORT.md` — 14 competitor channels, 3,017 videos ka analysis (genres, judges, titles, thumbnails)
- `niche/competitors/top_original_opportunities.csv`, `case_dossiers.csv` — library ke best cases (quote + timestamp)
- `niche/judge-sources/JUDGE_LIVE_SOURCES.md` — har judge ki asli live feed kahan hai (`/streams` tab!)
- `niche/BROLL-STYLE-BREAKDOWN.md` — Audit the Court (1.68M views) ki editing frame-by-frame

## Qaide (HARD)
- Library ki transcripts **YouTube auto-captions** hain: naam, case number, saza ghalat sun sakte hain.
  Script likhne se pehle studio ka Whisper transcript + video dekh ke confirm karo. Pakka na ho to "the judge" / "the defendant".
- Sirf **official court/judge feeds** se videos banao (library yahi hai). Competitor videos sirf research ke liye —
  unki footage/narration kabhi use mat karo.
- Kuch courts "DO NOT RECORD" kehti hain, minors/victims/sealed cases → mat banao.
- `config.env` (keys) kabhi commit/share mat karo.
