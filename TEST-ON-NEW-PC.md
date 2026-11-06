# Court Studio — new PC full setup + test (instructions for Claude)

You are Claude Code on a NEW computer (Windows or Mac). Goal: install everything Court Studio needs,
then test EVERY part end-to-end, fix what breaks, and write `TEST-REPORT.md`.
The user is not technical: run every command yourself. Only stop and ask the user for:
(a) their license key, (b) logging in to ChatGPT in the window that opens, (c) optional ai33 / ElevenLabs keys.
Use `python` on Windows if `python3` does not exist. Run long steps (downloads, transcription, renders)
in the background and keep working on other tests meanwhile. Total time ~1-1.5 hours.

Rules
- Record every test as PASS / FAIL / SKIPPED with the exact error and what you changed.
- If something fails: find the cause, fix the code in this repo, re-run the test, and note the fix.
  Do NOT `git push` (only report). Do not delete user files outside this folder.
- Look at every image you produce (layout check, previews, thumbnail) — "file exists" is not a pass.

---

## 0. Install (skip what is already installed)
Check: `git --version`, `python3 --version` (3.10+), `node --version` (18+), `ffmpeg -version`,
Google Chrome installed, `ffmpeg -hide_banner -filters` contains ` ass ` (libass) and ` drawbox `.

Windows (PowerShell):
```
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Gyan.FFmpeg -e
winget install --id Google.Chrome -e
```
(open a new terminal after winget so PATH updates)

Mac:
```
brew install git python node ffmpeg yt-dlp
```
Python packages (both):
```
python3 -m pip install -U yt-dlp faster-whisper edge-tts pillow numpy pyyaml youtube-transcript-api trafilatura pypdf
python3 -m pip install -U opencv-python    # optional, better thumbnail face picking
```
(Mac with Homebrew Python may need `--break-system-packages`; Windows: use `python -m pip ...`.)

## 1. Get the repo
```
git clone https://github.com/naveedpcworld-droid/court-studio.git
cd court-studio
```
PASS if `library/index.csv` and 35 files in `library/transcripts/` exist.
Then activate the license (ASK THE USER for their key — teacher gives one per PC):
`python3 tools/license.py activate CS-XXXX-XXXX-XXXX` → PASS: "✅ activated on this PC", then `python3 tools/license.py status`.
Never edit or bypass tools/license.py.
Then read `CLAUDE.md` and `studio/CLAUDE.md` once (that is how students will use it).

## 2. Library search  (`tools/find_case.py`)
```
python3 tools/find_case.py topics
python3 tools/find_case.py search --topic sovereign --n 5
python3 tools/find_case.py search --judge simpson --n 5
python3 tools/find_case.py search --text "i do not consent" --n 5
python3 tools/find_case.py suggest --n 5
python3 tools/find_case.py hot abVO4pMscUQ
python3 tools/find_case.py show abVO4pMscUQ --from 1:28:00 --to 1:30:00
```
PASS: topics list ~24 topics; sovereign search shows results with YouTube links; text search finds
"i do not consent" in 5+ videos in a few seconds; `hot` prints windows with a `fetch.py ... --section`
command; `show` prints the judge saying he won't accept the dismissal ("sovereign citizen nation").

## 3. Optional updates  (`tools/update.py`)
```
python3 tools/update.py --max-new 3
```
PASS: ends with "done. daily-desk videos now: N" (a few RSS 404 retries are OK). Then
`git status` shows only `desk/data/` / `desk/site/data/` changed. Run `git checkout -- desk` after, to
keep the test clean.

## 4. Download only the case + transcribe  (studio)
All studio commands run inside `studio/`:
```
cd studio
python3 tools/fetch.py graves-test "https://www.youtube.com/watch?v=abVO4pMscUQ" --section 4920 6180
python3 tools/cases.py graves-test --all
python3 tools/layout.py graves-test
```
(download ~5-15 min, transcription ~10-20 min — run in background.)
PASS: `projects/graves-test/src.mp4` ~21 min, `transcript.txt` mentions "abatement" / "corporate fiction";
OPEN `projects/graves-test/layout_check.jpg`: red box covers the Zoom camera picture (not the black bars).
If YouTube says "Sign in to confirm you're not a bot": retry later or add
`--cookies-from-browser chrome` to the yt-dlp calls in `tools/fetch.py` and note it.

## 5. Script + voice
```
copy projects\_example-graves-highlights\script.json projects\graves-test\       (Windows)
cp projects/_example-graves-highlights/script.json projects/graves-test/         (Mac)
python3 tools/voice.py --test edge "Testing the free narrator voice."
python3 tools/voice.py graves-test
```
PASS: test prints `ok -> ... voice_test.mp3`; project prints 6 blocks (hook, p1-p4, outro), ~175 s total.
Play `projects/graves-test/vo/hook.mp3` — it must be clear English speech.
Optional (ask the user ONCE if they have keys; skip otherwise): put `AI33_KEY` + `AI33_VOICE` or
`ELEVENLABS_KEY` + `ELEVENLABS_VOICE` in `studio/config.env` (copy from `config.env.example`) and run
`python3 tools/voice.py --test ai33 "hello"` / `--test elevenlabs "hello"`.

## 6. Build + every template preview
```
python3 tools/build.py graves-test --template T02 --dry
```
PASS: prints a final length of about 14:00 (13:30-14:30).
Then for EVERY template T01..T14 and B01..B05:
```
python3 tools/build.py graves-test --template T05
python3 tools/render.py graves-test --template T05 --still 120
```
(still frame -> `projects/graves-test/preview_T05.jpg`). OPEN each preview: the camera picture is in the
frame, background visible, captions readable and not over faces. B-templates without `beats` in the script
render like normal templates — that is expected.

## 7. Render
```
python3 tools/render.py graves-test --template T02 --sample 60
python3 tools/render.py graves-test --template T07 --sample 60
python3 tools/render.py graves-test --template T02
```
PASS: `sample_T02.mp4` / `sample_T07.mp4` are 60 s with sound and captions; the full `final_T02.mp4` is
~14 min, video and audio the same length (`ffprobe`), first 36 s are the 3 highlights with a "COMING UP..."
tag, then the narrator. Extract 6 frames across the final video and LOOK at them.

## 8. B-roll beat renderer (no internet needed)
```
python3 -c "import sys; sys.path.insert(0,'tools'); import beats; beats.render(dict(type='doc', subtitle='Texas', title='Art. 14.06', text='take the person arrested without unnecessary delay, but not later than 48 hours', highlight=['not later than 48 hours']), {}, 'projects/graves-test/beat_doc.mp4', 3, hl_at=0.3); beats.render(dict(type='charge', offense='DWI', law='Penal Code 49.04', penalty='Class A'), {}, 'projects/graves-test/beat_charge.mp4', 3); print('ok')"
```
PASS: both mp4s play; doc card shows a yellow marker over "not later than 48 hours"; nothing shakes.
Optional (only if the user has free keys): `SERPER_API_KEY`, `PEXELS_API_KEY` in `studio/config.env`, then
`python3 tools/research.py graves-test wiki "Sovereign citizen movement"` and
`python3 tools/research.py graves-test broll "judge gavel courtroom"`.

## 9. Thumbnail (ChatGPT)
```
cd ../thumbnail-gpt && npm install && cd ../studio
python3 tools/thumbnail.py graves-test frames --at 520 545 600 615 625 800
```
OPEN `projects/graves-test/thumbs/sheet.jpg`, pick the clearest judge frame and defendant frame, then:
```
python3 tools/thumbnail.py graves-test make --left thumbs/frames/<judge>.jpg --right thumbs/frames/<defendant>.jpg --text "CORPORATE FICTION?!" --highlight "FICTION?!" --sub "JUDGE SAYS NO"
```
The first time a Chrome window opens on chatgpt.com — ASK THE USER to log in there (an account with image
generation), wait for them to say done, then run `make` again.
PASS: in the ChatGPT window BOTH photos appear attached before the prompt is sent; `thumbs/thumb_1.jpg`
is 1920x1080; OPEN it: same two real people, text spelled exactly, red arrow, readable.
Then test a correction:
```
python3 tools/thumbnail.py graves-test fix "make the red arrow bigger and point it at her face"
```
PASS: `thumb_2.jpg` saved with the change.
If ChatGPT says it cannot generate (free limit) → note it as SKIPPED (limit), not FAIL.

## 10. Student flow check (as a student would)
Start a fresh Claude Code chat in the repo root and say:
"Judge Perkins ki koi sovereign citizen wali video dhoondo aur batao kaunsa case best hai."
PASS: Claude uses `tools/find_case.py` (not a web search), gives 5-8 options with reasons, and suggests a
`--section`. Do not build a second video — just check the answer.

## 11. Report
Write `TEST-REPORT.md` in the repo root:
- PC: OS + version, Python, Node, ffmpeg version, CPU.
- Table: step | PASS/FAIL/SKIPPED | time taken | notes.
- Every bug found: error, cause, file + fix.
- List of files you changed (`git status`, `git diff --stat`).
- Paths of: final video, 2 samples, thumbnail(s), 19 preview stills.
Then tell the user in simple Roman Urdu: what works, what failed, what they need to do (if anything).
Do not push. The repo owner will review the report and the diff.
